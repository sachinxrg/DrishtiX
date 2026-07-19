package com.drishtix.controller;

import com.drishtix.model.*;
import com.drishtix.service.*;
import com.drishtix.util.AppConstants;
import com.drishtix.util.AutoCloseableMat;
import com.drishtix.util.FxImageConverter;
import com.drishtix.util.ThreadPools;
import javafx.application.Platform;
import javafx.fxml.FXML;
import javafx.geometry.Insets;
import javafx.geometry.Pos;
import javafx.scene.control.*;
import javafx.scene.image.Image;
import javafx.scene.image.ImageView;
import javafx.scene.layout.*;

import javafx.stage.FileChooser;
import org.bytedeco.javacv.OpenCVFrameGrabber;
import org.bytedeco.javacv.Frame;
import org.bytedeco.javacv.OpenCVFrameConverter;
import org.bytedeco.opencv.opencv_core.*;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.io.File;
import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;
import java.util.List;
import java.util.concurrent.CompletableFuture;
import java.util.concurrent.atomic.AtomicBoolean;
import java.util.concurrent.atomic.AtomicReference;

import static org.bytedeco.opencv.global.opencv_imgcodecs.imwrite;
import static org.bytedeco.opencv.global.opencv_imgproc.*;

/**
 * HERO CONTROLLER — manages the main dashboard with:
 * 1. Live camera feed (70% of screen)
 * 2. Stats panel with target counts and recent alerts (30%)
 * 3. Pop-up alert notifications for matches
 * 4. Quick-add target capability
 *
 * Implements the three-pool threading model:
 * - UI Thread: JavaFX rendering, pop-up alerts, status updates
 * - Video Inference Thread: frame capture, face detection, recognition
 * - Audio Alert Thread: sound playback (via AlertService)
 */
public class DashboardController {

    private static final Logger log = LoggerFactory.getLogger(DashboardController.class);

    // ==================== FXML Bindings ====================
    @FXML private ImageView cameraFeed;
    @FXML private ComboBox<CameraSource> cameraSelector;
    @FXML private Button btnStartStop;
    @FXML private Slider confidenceSlider;
    @FXML private Label lblConfidence;
    @FXML private ToggleButton btnMute;
    @FXML private Label lblTotalTargets;
    @FXML private Label lblCriminals;
    @FXML private Label lblMissing;
    @FXML private Label lblDetectionsToday;
    @FXML private Label lblCameraStatus;
    @FXML private Label lblRecognizerStatus;
    @FXML private VBox recentAlertsBox;
    @FXML private StackPane alertOverlay;
    @FXML private Label lblFps;

    // ==================== Services ====================
    private final TargetRegistryService registryService = TargetRegistryService.getInstance();
    private final FaceProcessingService faceService = FaceProcessingService.getInstance();
    private final RecognitionService recognitionService = RecognitionService.getInstance();
    private final AlertService alertService = AlertService.getInstance();
    private final DetectionLogService detectionLogService = DetectionLogService.getInstance();
    private final ConfigurationService configService = ConfigurationService.getInstance();

    // ==================== Camera State ====================
    private final AtomicBoolean cameraRunning = new AtomicBoolean(false);
    private final AtomicReference<Double> currentThreshold = new AtomicReference<>(80.0);
    private OpenCVFrameGrabber grabber;
    private final OpenCVFrameConverter.ToMat converter = new OpenCVFrameConverter.ToMat();

    // ==================== FPS Counter ====================
    private long frameCount = 0;
    private long lastFpsTime = System.currentTimeMillis();
    private int currentFps = 0;

    @FXML
    public void initialize() {
        log.info("DashboardController initializing — HERO SCREEN");

        // Initialize confidence slider
        double threshold = configService.getConfidenceThreshold();
        if (confidenceSlider != null) {
            confidenceSlider.setValue(threshold);
            confidenceSlider.valueProperty().addListener((obs, oldVal, newVal) -> {
                currentThreshold.set(newVal.doubleValue());
                if (lblConfidence != null) {
                    lblConfidence.setText(String.format("%.0f", newVal.doubleValue()));
                }
            });
        }

        // Initialize mute button
        if (btnMute != null) {
            btnMute.setSelected(!alertService.isAudioEnabled());
            btnMute.setOnAction(e -> alertService.toggleMute());
        }

        // Update dashboard stats
        refreshStats();

        // Load recent alerts
        refreshRecentAlerts();

        // Initialize recognizer on startup
        registryService.initializeRecognizer();

        // Auto-start camera if configured
        if (configService.isAutoStartCamera()) {
            Platform.runLater(() -> startCamera());
        }

        log.info("DashboardController initialized");
    }

    // ==================== Camera Control ====================

    /**
     * Starts or stops the camera feed.
     */
    @FXML
    public void handleStartStop() {
        if (cameraRunning.get()) {
            stopCamera();
        } else {
            startCamera();
        }
    }

    /**
     * Starts the camera feed on the Video Inference thread pool.
     */
    private void startCamera() {
        if (cameraRunning.get()) return;

        CompletableFuture.runAsync(() -> {
            try {
                int cameraIndex = 0;
                if (cameraSelector != null && cameraSelector.getValue() != null) {
                    cameraIndex = cameraSelector.getValue().getDeviceIndex();
                    if (cameraIndex < 0) cameraIndex = 0;
                }

                // Use standard device index — OpenCVFrameGrabber picks the platform-native backend
                grabber = new OpenCVFrameGrabber(cameraIndex);
                grabber.setImageWidth(640);
                grabber.setImageHeight(480);
                grabber.start();

                // Validate that the grabber actually started by attempting a test grab
                Frame testFrame = grabber.grab();
                if (testFrame == null) {
                    log.warn("Camera opened but initial grab returned null — device may not be ready");
                }

                cameraRunning.set(true);

                Platform.runLater(() -> {
                    if (btnStartStop != null) btnStartStop.setText("⏹ Stop");
                    if (lblCameraStatus != null) {
                        lblCameraStatus.setText("● Active");
                        lblCameraStatus.setStyle("-fx-text-fill: #22C55E;");
                    }
                });

                log.info("Camera started on device index: {}", cameraIndex);

                // Main capture loop
                runCaptureLoop();

            } catch (Exception e) {
                log.error("Failed to start camera", e);
                cameraRunning.set(false);
                Platform.runLater(() -> {
                    showErrorToast("Camera Error: " + e.getMessage());
                    if (btnStartStop != null) btnStartStop.setText("▶ Start");
                });
            }
        }, ThreadPools.getVideoInferencePool());
    }

    /**
     * Stops the camera feed.
     */
    private void stopCamera() {
        cameraRunning.set(false);
        try {
            if (grabber != null) {
                grabber.stop();
                grabber.close();
            }
        } catch (Exception e) {
            log.error("Error stopping camera", e);
        }

        Platform.runLater(() -> {
            if (btnStartStop != null) btnStartStop.setText("▶ Start");
            if (lblCameraStatus != null) {
                lblCameraStatus.setText("○ Inactive");
                lblCameraStatus.setStyle("-fx-text-fill: #EF4444;");
            }
            if (cameraFeed != null) {
                cameraFeed.setImage(FxImageConverter.createPlaceholder(640, 480));
            }
        });

        log.info("Camera stopped");
    }

    /**
     * Main video capture and processing loop.
     * Runs on the Video Inference thread pool.
     * Captures frames → detects faces → recognizes → annotates → pushes to UI.
     */
    private void runCaptureLoop() {
        int fpsTarget = configService.getVideoFpsTarget();
        long frameDuration = 1000 / fpsTarget;
        int consecutiveErrors = 0;
        final int MAX_CONSECUTIVE_ERRORS = 10;

        while (cameraRunning.get()) {
            long startTime = System.currentTimeMillis();

            try {
                Frame frame = grabber.grab();
                if (frame == null || frame.image == null) {
                    consecutiveErrors++;
                    if (consecutiveErrors >= MAX_CONSECUTIVE_ERRORS) {
                        log.error("Camera produced {} consecutive null frames — stopping camera", consecutiveErrors);
                        break;
                    }
                    continue;
                }

                // Reset error counter on successful grab
                consecutiveErrors = 0;

                Mat mat = converter.convert(frame);
                if (mat == null || mat.empty()) continue;

                // Clone the frame for processing (original may be reused by grabber)
                try (AutoCloseableMat processingMat = new AutoCloseableMat()) {
                    mat.copyTo(processingMat.get());
                    processFrame(processingMat.get());
                }

            } catch (Exception e) {
                if (cameraRunning.get()) {
                    consecutiveErrors++;
                    if (consecutiveErrors <= 3) {
                        log.error("Error during frame capture (attempt {}/{})", consecutiveErrors, MAX_CONSECUTIVE_ERRORS, e);
                    } else if (consecutiveErrors == MAX_CONSECUTIVE_ERRORS) {
                        log.error("Too many consecutive capture errors ({}) — stopping camera", consecutiveErrors);
                        break;
                    }
                    // Exponential back-off: sleep 100ms, 200ms, 400ms... up to 1600ms
                    try {
                        long backoff = Math.min(100L * (1L << (consecutiveErrors - 1)), 1600L);
                        Thread.sleep(backoff);
                    } catch (InterruptedException ie) {
                        Thread.currentThread().interrupt();
                        break;
                    }
                }
            }

            // FPS control
            long elapsed = System.currentTimeMillis() - startTime;
            long sleepTime = frameDuration - elapsed;
            if (sleepTime > 0) {
                try {
                    Thread.sleep(sleepTime);
                } catch (InterruptedException e) {
                    Thread.currentThread().interrupt();
                    break;
                }
            }

            // Update FPS counter
            frameCount++;
            long now = System.currentTimeMillis();
            if (now - lastFpsTime >= 1000) {
                currentFps = (int) frameCount;
                frameCount = 0;
                lastFpsTime = now;
                Platform.runLater(() -> {
                    if (lblFps != null) lblFps.setText("FPS: " + currentFps);
                });
            }
        }

        // If we broke out of the loop due to errors, auto-stop the camera gracefully
        if (cameraRunning.get()) {
            cameraRunning.set(false);
            Platform.runLater(() -> {
                showErrorToast("Camera stopped: too many consecutive errors. Please check your camera connection.");
                if (btnStartStop != null) btnStartStop.setText("▶ Start");
                if (lblCameraStatus != null) {
                    lblCameraStatus.setText("⚠ Error");
                    lblCameraStatus.setStyle("-fx-text-fill: #EF4444;");
                }
                if (cameraFeed != null) {
                    cameraFeed.setImage(FxImageConverter.createPlaceholder(640, 480));
                }
            });
            try {
                if (grabber != null) {
                    grabber.stop();
                    grabber.close();
                }
            } catch (Exception e) {
                log.error("Error stopping camera after failure", e);
            }
        }
    }

    /**
     * Processes a single frame: detect faces, recognize, annotate, alert.
     */
    private void processFrame(Mat frame) {
        // Detect all faces in the frame
        RectVector faces = faceService.detectFaces(frame);

        for (long i = 0; i < faces.size(); i++) {
            Rect faceRect = faces.get(i);

            // Extract face ROI for recognition
            Mat faceROI = faceService.extractFaceROI(frame, faceRect);
            RecognitionResult result = recognitionService.predict(faceROI);
            faceROI.release();

            // Determine bounding box color and label
            int[] color;
            String label;

            if (result.isMatched() && result.getMatchedTarget() != null) {
                TargetRegistry target = result.getMatchedTarget();
                TargetCategory category = target.getCategory();

                color = (category == TargetCategory.CRIMINAL)
                        ? AppConstants.COLOR_CRIMINAL_BGR
                        : AppConstants.COLOR_MISSING_BGR;

                label = target.getFullName() + " | " + target.getCaseNumber();

                // Trigger alert (respects cooldown)
                boolean alertTriggered = alertService.triggerAlert(target.getTargetId(), category);

                if (alertTriggered) {
                    // Save detection snapshot
                    String snapshotPath = saveSnapshot(frame, target.getTargetId());

                    // Log detection
                    DetectionLog detection = new DetectionLog(
                            target.getTargetId(),
                            result.getConfidence(),
                            snapshotPath,
                            1, // default camera
                            null
                    );
                    CompletableFuture.runAsync(
                            () -> detectionLogService.logDetection(detection),
                            ThreadPools.getVideoInferencePool()
                    );

                    // Show pop-up alert on UI thread
                    Platform.runLater(() -> showAlertPopup(target, result, snapshotPath));
                }
            } else {
                color = AppConstants.COLOR_UNKNOWN_BGR;
                label = "Unknown";
            }

            // Draw bounding box
            rectangle(frame,
                    new Point(faceRect.x(), faceRect.y()),
                    new Point(faceRect.x() + faceRect.width(), faceRect.y() + faceRect.height()),
                    new Scalar(color[0], color[1], color[2], 255),
                    2, LINE_AA, 0);

            // Draw label background (approximate text dimensions since JavaCV lacks getTextSize)
            int textHeight = 14;
            int textWidth = label.length() * 7;
            rectangle(frame,
                    new Point(faceRect.x(), faceRect.y() - textHeight - 10),
                    new Point(faceRect.x() + textWidth + 4, faceRect.y()),
                    new Scalar(color[0], color[1], color[2], 200),
                    FILLED, LINE_AA, 0);

            // Draw label text
            putText(frame, label,
                    new Point(faceRect.x() + 2, faceRect.y() - 5),
                    FONT_HERSHEY_SIMPLEX, 0.5,
                    new Scalar(255, 255, 255, 255),
                    1, LINE_AA, false);
        }

        // Push annotated frame to the UI thread
        Image fxImage = FxImageConverter.matToImage(frame);
        if (fxImage != null) {
            Platform.runLater(() -> {
                if (cameraFeed != null) {
                    cameraFeed.setImage(fxImage);
                }
            });
        }
    }

    // ==================== Pop-Up Alert ====================

    /**
     * Shows a pop-up alert notification overlay on the dashboard.
     * This runs on the JavaFX Application Thread.
     */
    private void showAlertPopup(TargetRegistry target, RecognitionResult result, String snapshotPath) {
        if (alertOverlay == null) return;

        boolean isCriminal = target.getCategory() == TargetCategory.CRIMINAL;
        String borderColor = isCriminal ? "#FF4D2E" : "#00D4FF";
        String headerText = isCriminal
                ? "⚠ CRIMINAL DETECTED — HIGH PRIORITY ALERT ⚠"
                : "🔵 MISSING PERSON FOUND — NOTIFICATION";
        String headerBg = isCriminal ? "#FF4D2E" : "#00D4FF";

        // Create the popup content
        VBox popup = new VBox(12);
        popup.setAlignment(Pos.CENTER);
        popup.setMaxWidth(520);
        popup.setMaxHeight(420);
        popup.setStyle(String.format(
                "-fx-background-color: #111827; " +
                "-fx-border-color: %s; -fx-border-width: 3; -fx-border-radius: 12; " +
                "-fx-background-radius: 12; -fx-padding: 0; " +
                "-fx-effect: dropshadow(gaussian, %s, 20, 0.3, 0, 0);",
                borderColor, borderColor));

        // Header
        Label header = new Label(headerText);
        header.setStyle(String.format(
                "-fx-background-color: %s; -fx-text-fill: white; -fx-font-size: 14; " +
                "-fx-font-weight: bold; -fx-padding: 10 20; -fx-background-radius: 10 10 0 0; " +
                "-fx-min-width: 520; -fx-alignment: center;", headerBg));

        // Image row: registered photo + live snapshot
        HBox imageRow = new HBox(20);
        imageRow.setAlignment(Pos.CENTER);
        imageRow.setPadding(new Insets(10));

        // Registered photo
        VBox regPhotoBox = new VBox(4);
        regPhotoBox.setAlignment(Pos.CENTER);
        ImageView regPhoto = new ImageView();
        regPhoto.setFitWidth(140);
        regPhoto.setFitHeight(140);
        regPhoto.setPreserveRatio(true);
        try {
            File profileFile = new File(target.getProfileImagePath());
            if (profileFile.exists()) {
                regPhoto.setImage(new Image(profileFile.toURI().toString(), 140, 140, true, true));
            }
        } catch (Exception e) {
            log.warn("Could not load profile image for popup", e);
        }
        Label regLabel = new Label("REGISTERED");
        regLabel.setStyle("-fx-text-fill: #94A3B8; -fx-font-size: 10;");
        regPhotoBox.getChildren().addAll(regPhoto, regLabel);

        // Live snapshot
        VBox livePhotoBox = new VBox(4);
        livePhotoBox.setAlignment(Pos.CENTER);
        ImageView livePhoto = new ImageView();
        livePhoto.setFitWidth(140);
        livePhoto.setFitHeight(140);
        livePhoto.setPreserveRatio(true);
        try {
            if (snapshotPath != null) {
                File snapFile = new File(snapshotPath);
                if (snapFile.exists()) {
                    livePhoto.setImage(new Image(snapFile.toURI().toString(), 140, 140, true, true));
                }
            }
        } catch (Exception e) {
            log.warn("Could not load snapshot for popup", e);
        }
        Label liveLabel = new Label("LIVE CAPTURE");
        liveLabel.setStyle("-fx-text-fill: #94A3B8; -fx-font-size: 10;");
        livePhotoBox.getChildren().addAll(livePhoto, liveLabel);

        imageRow.getChildren().addAll(regPhotoBox, livePhotoBox);

        // Details
        VBox details = new VBox(4);
        details.setPadding(new Insets(0, 20, 0, 20));
        details.getChildren().addAll(
                createDetailRow("Name:", target.getFullName()),
                createDetailRow("Category:", target.getCategory().getDbValue()),
                createDetailRow("Case #:", target.getCaseNumber()),
                createDetailRow("Confidence:", result.getConfidencePercentage()),
                createDetailRow("Time:", LocalDateTime.now().format(
                        DateTimeFormatter.ofPattern("HH:mm:ss dd-MMM-yyyy")))
        );

        // Action buttons
        HBox buttons = new HBox(15);
        buttons.setAlignment(Pos.CENTER);
        buttons.setPadding(new Insets(10, 0, 15, 0));

        Button btnDismiss = new Button("Dismiss");
        btnDismiss.setStyle("-fx-background-color: #374151; -fx-text-fill: #F1F5F9; " +
                "-fx-padding: 8 25; -fx-background-radius: 6; -fx-cursor: hand;");
        btnDismiss.setOnAction(e -> alertOverlay.setVisible(false));

        Button btnAcknowledge = new Button("Acknowledge & Log");
        btnAcknowledge.setStyle(String.format(
                "-fx-background-color: %s; -fx-text-fill: white; " +
                "-fx-padding: 8 25; -fx-background-radius: 6; -fx-font-weight: bold; -fx-cursor: hand;",
                headerBg));
        btnAcknowledge.setOnAction(e -> {
            alertOverlay.setVisible(false);
            refreshRecentAlerts();
            refreshStats();
        });

        buttons.getChildren().addAll(btnDismiss, btnAcknowledge);

        popup.getChildren().addAll(header, imageRow, details, buttons);

        // Show overlay
        alertOverlay.getChildren().setAll(popup);
        alertOverlay.setVisible(true);
        alertOverlay.setStyle("-fx-background-color: rgba(0,0,0,0.7);");

        // Refresh stats after alert
        refreshStats();
        refreshRecentAlerts();
    }

    private HBox createDetailRow(String labelText, String valueText) {
        HBox row = new HBox(8);
        row.setAlignment(Pos.CENTER_LEFT);
        Label lbl = new Label(labelText);
        lbl.setStyle("-fx-text-fill: #94A3B8; -fx-font-size: 12; -fx-min-width: 90;");
        Label val = new Label(valueText);
        val.setStyle("-fx-text-fill: #F1F5F9; -fx-font-size: 13; -fx-font-weight: bold;");
        row.getChildren().addAll(lbl, val);
        return row;
    }

    // ==================== Quick Add Target ====================

    @FXML
    public void handleQuickAddTarget() {
        FileChooser fileChooser = new FileChooser();
        fileChooser.setTitle("Upload Target Photo");
        fileChooser.getExtensionFilters().addAll(
                new FileChooser.ExtensionFilter("Image Files", "*.jpg", "*.jpeg", "*.png")
        );

        File selectedFile = fileChooser.showOpenDialog(cameraFeed.getScene().getWindow());
        if (selectedFile == null) return;

        // Show a quick registration dialog
        Dialog<TargetRegistry> dialog = new Dialog<>();
        dialog.setTitle("DrishtiX — Register New Target");
        dialog.setHeaderText("Register target from: " + selectedFile.getName());

        // Form fields
        GridPane grid = new GridPane();
        grid.setHgap(10);
        grid.setVgap(10);
        grid.setPadding(new Insets(20, 20, 10, 20));
        grid.setStyle("-fx-background-color: #111827;");

        TextField nameField = new TextField();
        nameField.setPromptText("Full Name");
        ComboBox<TargetCategory> categoryBox = new ComboBox<>();
        categoryBox.getItems().addAll(TargetCategory.values());
        categoryBox.setValue(TargetCategory.CRIMINAL);
        TextField caseField = new TextField();
        caseField.setPromptText("Case/FIR Number");
        TextArea descField = new TextArea();
        descField.setPromptText("Description (optional)");
        descField.setPrefRowCount(2);

        grid.add(new Label("Name:"), 0, 0);
        grid.add(nameField, 1, 0);
        grid.add(new Label("Category:"), 0, 1);
        grid.add(categoryBox, 1, 1);
        grid.add(new Label("Case #:"), 0, 2);
        grid.add(caseField, 1, 2);
        grid.add(new Label("Description:"), 0, 3);
        grid.add(descField, 1, 3);

        dialog.getDialogPane().setContent(grid);
        dialog.getDialogPane().getButtonTypes().addAll(ButtonType.OK, ButtonType.CANCEL);

        dialog.setResultConverter(btn -> {
            if (btn == ButtonType.OK) {
                String name = nameField.getText().trim();
                String caseNum = caseField.getText().trim();
                if (name.isEmpty() || caseNum.isEmpty()) {
                    showErrorToast("Name and Case Number are required");
                    return null;
                }
                try {
                    return registryService.registerTarget(
                            selectedFile.getAbsolutePath(),
                            name,
                            categoryBox.getValue(),
                            caseNum,
                            descField.getText().trim()
                    );
                } catch (Exception ex) {
                    showErrorToast(ex.getMessage());
                    return null;
                }
            }
            return null;
        });

        dialog.showAndWait().ifPresent(target -> {
            showSuccessToast("Target registered: " + target.getFullName() +
                    "\nDrishtiX is now watching.");
            refreshStats();
        });
    }

    // ==================== Stats & Alerts ====================

    public void refreshStats() {
        Platform.runLater(() -> {
            try {
                if (lblTotalTargets != null)
                    lblTotalTargets.setText(String.valueOf(registryService.getActiveTargetCount()));
                if (lblCriminals != null)
                    lblCriminals.setText(String.valueOf(registryService.getCriminalCount()));
                if (lblMissing != null)
                    lblMissing.setText(String.valueOf(registryService.getMissingPersonCount()));
                if (lblDetectionsToday != null)
                    lblDetectionsToday.setText(String.valueOf(detectionLogService.getTodayCount()));
                if (lblRecognizerStatus != null) {
                    lblRecognizerStatus.setText(recognitionService.isTrained() ? "● Trained" : "○ Not Trained");
                    lblRecognizerStatus.setStyle(recognitionService.isTrained()
                            ? "-fx-text-fill: #22C55E;" : "-fx-text-fill: #FBBF24;");
                }
            } catch (Exception e) {
                log.warn("Failed to refresh stats", e);
            }
        });
    }

    public void refreshRecentAlerts() {
        Platform.runLater(() -> {
            try {
                if (recentAlertsBox == null) return;
                recentAlertsBox.getChildren().clear();

                List<DetectionLog> recent = detectionLogService.getRecentDetections(5);
                for (DetectionLog dl : recent) {
                    HBox alertItem = new HBox(8);
                    alertItem.setAlignment(Pos.CENTER_LEFT);
                    alertItem.setPadding(new Insets(6, 10, 6, 10));
                    alertItem.setStyle("-fx-background-color: #1E293B; -fx-background-radius: 6;");

                    String dot = dl.getTargetCategory() == TargetCategory.CRIMINAL ? "🔴" : "🔵";
                    Label dotLabel = new Label(dot);
                    Label nameLabel = new Label(dl.getTargetName());
                    nameLabel.setStyle("-fx-text-fill: #F1F5F9; -fx-font-size: 11;");
                    Label timeLabel = new Label(dl.getDetectionTimestamp()
                            .format(DateTimeFormatter.ofPattern("HH:mm")));
                    timeLabel.setStyle("-fx-text-fill: #64748B; -fx-font-size: 10;");

                    Region spacer = new Region();
                    HBox.setHgrow(spacer, Priority.ALWAYS);

                    alertItem.getChildren().addAll(dotLabel, nameLabel, spacer, timeLabel);
                    recentAlertsBox.getChildren().add(alertItem);
                }
            } catch (Exception e) {
                log.warn("Failed to refresh recent alerts", e);
            }
        });
    }

    // ==================== Snapshot ====================

    private String saveSnapshot(Mat frame, int targetId) {
        try {
            String date = LocalDateTime.now().format(DateTimeFormatter.ofPattern("yyyy-MM-dd"));
            String dir = AppConstants.SNAPSHOTS_DIR + "/" + date;
            new File(dir).mkdirs();

            String timestamp = LocalDateTime.now().format(DateTimeFormatter.ofPattern("HHmmss_SSS"));
            String path = dir + "/" + targetId + "_" + timestamp + ".png";

            imwrite(path, frame);
            log.debug("Snapshot saved: {}", path);
            return path;
        } catch (Exception e) {
            log.error("Failed to save snapshot", e);
            return null;
        }
    }

    // ==================== Toast Notifications ====================

    private void showSuccessToast(String message) {
        showToast(message, "#22C55E");
    }

    private void showErrorToast(String message) {
        showToast(message, "#EF4444");
    }

    private void showToast(String message, String color) {
        Platform.runLater(() -> {
            Alert alert = new Alert(Alert.AlertType.INFORMATION);
            alert.setTitle("DrishtiX");
            alert.setHeaderText(null);
            alert.setContentText(message);
            alert.showAndWait();
        });
    }

    // ==================== Cleanup ====================

    /**
     * Called when the application is shutting down.
     */
    public void shutdown() {
        stopCamera();
        log.info("DashboardController shut down");
    }
}
