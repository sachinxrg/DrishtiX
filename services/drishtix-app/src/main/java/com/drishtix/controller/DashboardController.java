package com.drishtix.controller;

import com.drishtix.model.*;
import com.drishtix.service.*;
import com.drishtix.util.AppConstants;
import com.drishtix.util.AutoCloseableMat;
import com.drishtix.util.FxImageConverter;
import com.drishtix.util.ThreadPools;
import com.drishtix.util.VectorMathUtil;
import com.drishtix.dao.PersonEmbeddingDAO;
import javafx.application.Platform;
import javafx.beans.property.SimpleIntegerProperty;
import javafx.beans.property.IntegerProperty;
import javafx.fxml.FXML;
import javafx.geometry.Insets;
import javafx.geometry.Pos;
import javafx.scene.control.*;
import javafx.scene.image.Image;
import javafx.scene.image.ImageView;
import javafx.scene.layout.*;
import javafx.scene.shape.Rectangle;

import org.controlsfx.control.Notifications;
import javafx.util.Duration;

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
import java.util.ArrayList;
import java.util.List;
import java.util.concurrent.CompletableFuture;
import java.util.concurrent.atomic.AtomicBoolean;
import java.util.concurrent.atomic.AtomicLong;
import java.util.concurrent.atomic.AtomicReference;

import static org.bytedeco.opencv.global.opencv_imgcodecs.imwrite;
import static org.bytedeco.opencv.global.opencv_imgproc.*;

/**
 * HERO CONTROLLER — manages the main dashboard with:
 * 1. Live camera feed (70% of screen)
 * 2. Stats panel with reactive IntegerProperty-bound counters (30%)
 * 3. Dynamic sidebar alert queue (no modal popups)
 * 4. Quick-add target capability
 *
 * Implements the four-pool threading model:
 * - UI Thread: JavaFX rendering, alert card injection, status updates
 * - Video Inference Thread: frame capture, face detection (YuNet DNN)
 * - Recognition Inference Thread (NEW): DNN embedding extraction (SFace)
 * - Audio Alert Thread: sound playback (via AlertService)
 */
public class DashboardController {

    private static final Logger log = LoggerFactory.getLogger(DashboardController.class);
    private static final int MAX_ALERT_QUEUE_SIZE = 50;

    // ==================== FXML Bindings ====================
    @FXML private ImageView cameraFeed;
    @FXML private ImageView cameraFeedBg;
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
    @FXML private VBox alertQueueBox;
    @FXML private StackPane alertOverlay;
    @FXML private Label lblFps;

    // ==================== Reactive Dashboard Metrics ====================
    private final IntegerProperty totalTargetsProperty = new SimpleIntegerProperty(0);
    private final IntegerProperty criminalsProperty = new SimpleIntegerProperty(0);
    private final IntegerProperty missingProperty = new SimpleIntegerProperty(0);
    private final IntegerProperty detectionsProperty = new SimpleIntegerProperty(0);

    // ==================== Services ====================
    private final TargetRegistryService registryService = TargetRegistryService.getInstance();
    private final FaceProcessingService faceService = FaceProcessingService.getInstance();
    private final RecognitionService recognitionService = RecognitionService.getInstance();
    private final AlertService alertService = AlertService.getInstance();
    private final DetectionLogService detectionLogService = DetectionLogService.getInstance();
    private final ConfigurationService configService = ConfigurationService.getInstance();
    private final ReIDService reidService = ReIDService.getInstance();
    private final DnnBodyReIdService bodyReIdService = DnnBodyReIdService.getInstance();
    private final PersonEmbeddingDAO embeddingDAO = new PersonEmbeddingDAO();

    // ==================== Camera State ====================
    private final AtomicBoolean cameraRunning = new AtomicBoolean(false);
    private final AtomicReference<Double> currentThreshold = new AtomicReference<>(80.0);
    private OpenCVFrameGrabber grabber;
    private final OpenCVFrameConverter.ToMat converter = new OpenCVFrameConverter.ToMat();

    // ==================== FPS Counter ====================
    private long frameCount = 0;
    private long lastFpsTime = System.currentTimeMillis();
    private int currentFps = 0;

    // ==================== Frame-Skip & Tracking (Phase 3) ====================
    private final AtomicLong globalFrameIndex = new AtomicLong(0);
    private FaceTrackingManager trackingManager;
    private final AtomicBoolean isCsrtUpdating = new AtomicBoolean(false);

    @FXML
    public void initialize() {
        log.info("DashboardController initializing — HERO SCREEN (v4.0 Parallel Inference Pipeline)");

        // Initialize face tracking manager
        trackingManager = new FaceTrackingManager();

        // Bind reactive metric properties to UI labels
        if (lblTotalTargets != null) lblTotalTargets.textProperty().bind(totalTargetsProperty.asString());
        if (lblCriminals != null) lblCriminals.textProperty().bind(criminalsProperty.asString());
        if (lblMissing != null) lblMissing.textProperty().bind(missingProperty.asString());
        if (lblDetectionsToday != null) lblDetectionsToday.textProperty().bind(detectionsProperty.asString());

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

        // Initialize camera selector
        if (cameraSelector != null) {
            try {
                com.drishtix.dao.CameraSourceDAO cameraDAO = new com.drishtix.dao.CameraSourceDAO();
                java.util.List<com.drishtix.model.CameraSource> cameras = cameraDAO.findAllActive();
                if (cameras.isEmpty()) {
                    cameras.add(new com.drishtix.model.CameraSource("Default Camera", "0"));
                }
                cameraSelector.getItems().setAll(cameras);
                cameraSelector.getSelectionModel().selectFirst();
            } catch (Exception e) {
                log.error("Failed to load camera sources", e);
                cameraSelector.getItems().add(new com.drishtix.model.CameraSource("Default Camera", "0"));
                cameraSelector.getSelectionModel().selectFirst();
            }
        }

        // Initialize mute button
        if (btnMute != null) {
            btnMute.setSelected(!alertService.isAudioEnabled());
            btnMute.setOnAction(e -> alertService.toggleMute());
        }

        // Bind camera feed background to fill the container (anti-letterbox)
        if (cameraFeedBg != null && cameraFeed != null) {
            StackPane parent = (StackPane) cameraFeedBg.getParent();
            
            // CRITICAL FIX: Prevent infinite layout loops by stopping the StackPane
            // from calculating its preferred size based on the ImageViews.
            parent.setMinSize(0, 0);
            parent.setPrefSize(0, 0);

            cameraFeedBg.fitWidthProperty().bind(parent.widthProperty());
            cameraFeedBg.fitHeightProperty().bind(parent.heightProperty());
            
            cameraFeed.fitWidthProperty().bind(parent.widthProperty());
            cameraFeed.fitHeightProperty().bind(parent.heightProperty());
        }

        // Update dashboard stats via properties
        refreshStats();

        // Initialize recognizer on startup
        registryService.initializeRecognizer();

        // Also rebuild DNN gallery if in DNN mode
        if (configService.isDnnMode()) {
            CompletableFuture.runAsync(
                    () -> recognitionService.rebuildDnnGallery(),
                    ThreadPools.getRecognitionInferencePool()
            ).thenRun(ThreadPools::preWarmRecognitionPool);
        }

        // Auto-start camera if configured
        if (configService.isAutoStartCamera()) {
            Platform.runLater(() -> startCamera());
        }

        log.info("DashboardController initialized (mode={})",
                configService.isDnnMode() ? "DNN" : "HAAR+LBPH");
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
                    if (btnStartStop != null) {
                        btnStartStop.setText("⏹ Stop");
                        btnStartStop.getStyleClass().setAll("btn-stop-circle");
                    }
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
                    if (btnStartStop != null) {
                        btnStartStop.setText("▶ Start");
                        btnStartStop.getStyleClass().setAll("btn-start-circle");
                    }
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

        // Release all face trackers AND body locks (CSRT native memory)
        if (trackingManager != null) {
            trackingManager.clearAll();
        }

        Platform.runLater(() -> {
            if (btnStartStop != null) {
                btnStartStop.setText("▶ Start");
                btnStartStop.getStyleClass().setAll("btn-start-circle");
            }
            if (lblCameraStatus != null) {
                lblCameraStatus.setText("○ Inactive");
                lblCameraStatus.setStyle("-fx-text-fill: #EF4444;");
            }
            if (cameraFeed != null) {
                cameraFeed.setImage(FxImageConverter.createPlaceholder(640, 480));
            }
            if (cameraFeedBg != null) {
                cameraFeedBg.setImage(null);
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
                if (btnStartStop != null) {
                    btnStartStop.setText("▶ Start");
                    btnStartStop.getStyleClass().setAll("btn-start-circle");
                }
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
     * Processes a single frame: detect faces → recognize → annotate → alert.
     * <p>
     * DNN mode: Uses FaceDetectorYN (fast, on capture thread) + SFace (async, on recognition pool)
     * LBPH mode (fallback): Uses Haar Cascade + LBPH (synchronous)
     * </p>
     */
    private void processFrame(Mat frame) {
        if (configService.isDnnMode()) {
            processFrameDnn(frame);
        } else {
            processFrameLbph(frame);
        }
    }

    /**
     * DNN pipeline with frame-skip heuristic and parallel inference.
     * <p>
     * Every Nth frame (N=3 default): Full YuNet detection → parallel SFace
     * embedding extraction on 4-thread pool → initialize KCF/CSRT trackers.
     * Intermediate frames: Lightweight tracker.update() for smooth bounding
     * box interpolation at 30+ FPS without running heavy DNN.
     * </p>
     */
    private void processFrameDnn(Mat frame) {
        DnnFaceDetectionService dnnDetector = DnnFaceDetectionService.getInstance();
        if (!dnnDetector.isInitialized()) {
            processFrameLbph(frame);
            return;
        }

        long currentFrameIdx = globalFrameIndex.getAndIncrement();
        int inferenceInterval = configService.getInferenceFrameInterval();
        boolean isInferenceFrame = (currentFrameIdx % inferenceInterval == 0);

        // ===== BODY LOCK UPDATES — run on EVERY frame (inference + intermediate) =====
        // Body locks are persistent CSRT trackers that survive face tracker re-initialization.
        // They update independently of the face detection cycle.
        List<Rect> currentFaceBoxes = null; // Populated on inference frames for face re-confirmation

        if (isInferenceFrame) {
            // ===== FULL INFERENCE FRAME =====
            List<FaceDetection> faces = dnnDetector.detectFaces(frame);

            // Extract face boxes for body lock face re-confirmation
            currentFaceBoxes = new ArrayList<>();
            for (FaceDetection face : faces) {
                currentFaceBoxes.add(face.getBoundingBox());
            }

            // Initialize face trackers from fresh detections (with IoU label carry-over)
            trackingManager.initTrackers(frame, faces, currentFrameIdx);

            if (!faces.isEmpty()) {
                // Clone the frame ONCE so async threads can safely read pixels
                final Mat asyncFrame = frame.clone();
                List<CompletableFuture<Void>> futures = new ArrayList<>();

                int trackerIdx = 0;
                for (FaceDetection detection : faces) {
                    final int trackId = trackerIdx++;
                    final Rect box = detection.getBoundingBox();

                    // === GATE 1: Resolution check (main thread, ~0ms) ===
                    if (box.width() < 48 || box.height() < 48) {
                        trackingManager.updateTrackLabel(trackId, "Too Small", AppConstants.COLOR_UNKNOWN_BGR);
                        drawBoundingBox(frame, box, null, "Too Small", AppConstants.COLOR_UNKNOWN_BGR);
                        continue;
                    }

                    // === GATE 2: FQA on main thread (~3ms, NOT on pool) ===
                    int cx = Math.max(0, box.x());
                    int cy = Math.max(0, box.y());
                    int cw = Math.min(box.width(), frame.cols() - cx);
                    int ch = Math.min(box.height(), frame.rows() - cy);
                    if (cw <= 0 || ch <= 0) continue;

                    Mat rawCrop = new Mat(frame, new Rect(cx, cy, cw, ch));
                    FaceQuality fqa = faceService.assessFaceQuality(rawCrop, detection);
                    rawCrop.release();

                    if (fqa.isSpoofAttempt()) {
                        trackingManager.updateTrackLabel(trackId, "SPOOF", new int[]{0, 165, 255});
                        drawBoundingBox(frame, box, null, "SPOOF", new int[]{0, 165, 255});
                        continue;
                    }
                    if (fqa.isUnfavorable()) {
                        trackingManager.updateTrackLabel(trackId, "Unfavorable", AppConstants.COLOR_UNKNOWN_BGR);
                        drawBoundingBox(frame, box, null, "Unfavorable", AppConstants.COLOR_UNKNOWN_BGR);
                        continue;
                    }

                    // === GATE 3: Dynamic threshold computation (main thread, ~0ms) ===
                    double baseThreshold = configService.getDnnCosineThreshold();
                    double dynamicThreshold = baseThreshold;
                    if (box.width() < 80) dynamicThreshold += 0.05;
                    if (fqa.getLaplacianVariance() < 80.0) dynamicThreshold += 0.05;
                    dynamicThreshold = Math.min(dynamicThreshold, 0.95);
                    final double threshold = dynamicThreshold;

                    // Draw initial bounding box
                    drawBoundingBox(frame, box, null, "Analyzing...", AppConstants.COLOR_UNKNOWN_BGR);

                    // === SUBMIT: alignCrop + SFace embedding → pool (~8ms per face) ===
                    final float[] detRow = detection.getDetectionRow();
                    // Capture detection confidence + frame index for body lock handoff gating
                    final float yunetConfidence = detection.getDetectionScore();
                    final long frameIdx = currentFrameIdx;

                    CompletableFuture<Void> future = CompletableFuture.supplyAsync(() -> {
                        DnnFaceRecognitionService dnnRecog = DnnFaceRecognitionService.getInstance();
                        float[] embedding = dnnRecog.alignAndExtractEmbedding(asyncFrame, detRow);
                        if (embedding == null) return null;
                        RecognitionResult result = dnnRecog.matchAgainstGallery(embedding, threshold);
                        // Package both result and embedding for body lock handoff
                        if (result != null) {
                            result.setProbeEmbedding(embedding);
                        }
                        return result;
                    }, ThreadPools.getRecognitionInferencePool())
                    .thenAcceptAsync(result -> {
                        if (result == null) return;

                        handleRecognitionResult(result, box);
                        if (result.isMatched() && result.getMatchedTarget() != null) {
                            TargetRegistry target = result.getMatchedTarget();
                            boolean isCriminal = target.getCategory() == TargetCategory.CRIMINAL;
                            String label = target.getFullName() + " | " + target.getCaseNumber();
                            int[] color = isCriminal ? AppConstants.COLOR_CRIMINAL_BGR : AppConstants.COLOR_MISSING_BGR;
                            trackingManager.updateTrackLabel(trackId, label, color);

                            // === GATE 4: YuNet confidence > 0.8 for body lock ===
                            // Only acquire persistent CSRT body locks on high-confidence
                            // detections. This prevents false body locks on phantom faces
                            // where YuNet reports partial landmarks (head partially visible).
                            // The 200% torso expansion amplifies any spatial error, so
                            // the face detection itself must be strong.
                            if (yunetConfidence > 0.8f && !trackingManager.hasActiveBodyLock(target.getTargetId())) {
                                // BODY LOCK HANDOFF: expand face box 200% downward → torso ROI
                                // → initialize dedicated TrackerCSRT on the expanded region
                                LockedTarget lock = trackingManager.acquireBodyLock(
                                        asyncFrame, box,
                                        target.getTargetId(), label, color,
                                        result.getProbeEmbedding(), result.getSimilarity(),
                                        frameIdx
                                );

                                // Async: Extract OSNet body embedding on recognition pool
                                if (lock != null && bodyReIdService.isInitialized()) {
                                    final LockedTarget lockRef = lock;
                                    CompletableFuture.runAsync(() -> {
                                        Rect torsoBox = lockRef.getBodyBox();
                                        int tx = Math.max(0, torsoBox.x());
                                        int ty = Math.max(0, torsoBox.y());
                                        int tw = Math.min(torsoBox.width(), asyncFrame.cols() - tx);
                                        int th = Math.min(torsoBox.height(), asyncFrame.rows() - ty);
                                        if (tw <= 0 || th <= 0) return;

                                        Mat torsoCrop = null;
                                        try {
                                            torsoCrop = new Mat(asyncFrame, new Rect(tx, ty, tw, th));
                                            float[] bodyEmbed = bodyReIdService.extractEmbedding(torsoCrop);
                                            if (bodyEmbed != null) {
                                                lockRef.setBodyEmbedding(bodyEmbed);
                                                lockRef.setLastBodySimilarity(1.0); // Self-similarity at lock time
                                                log.debug("OSNet body embedding extracted for targetId={}",
                                                        lockRef.getTargetId());
                                            }
                                        } finally {
                                            if (torsoCrop != null) torsoCrop.release();
                                        }
                                    }, ThreadPools.getRecognitionInferencePool());
                                }
                            }
                        } else {
                            trackingManager.updateTrackLabel(trackId, "Unknown", AppConstants.COLOR_UNKNOWN_BGR);
                        }
                    }, ThreadPools.getVideoInferencePool());

                    futures.add(future);
                }

                // Memory-safe frame release — fires on BOTH success and exception
                CompletableFuture.allOf(futures.toArray(new CompletableFuture[0]))
                        .whenCompleteAsync((ignored, throwable) -> {
                            asyncFrame.release();
                            if (throwable != null) {
                                log.warn("Async frame released after exception in {} futures",
                                        futures.size(), throwable);
                            } else {
                                log.trace("Async frame clone released after {} parallel inferences",
                                        futures.size());
                            }
                        }, ThreadPools.getVideoInferencePool());
            }

            // === ReID Pipeline (runs for ALL detected faces, async) ===
            if (configService.isReIDEnabled()) {
                for (FaceDetection detection : faces) {
                    Rect faceRect = detection.getBoundingBox();
                    Mat personCrop = faceService.extractPersonCrop(frame, faceRect);
                    if (personCrop != null) {
                        try {
                            byte[] jpegBytes = matToJpegBytes(personCrop);
                            if (jpegBytes != null) {
                                reidService.extractEmbedding(jpegBytes, "person_crop.jpg")
                                        .thenAcceptAsync(embedding -> {
                                            if (embedding != null) {
                                                handleReIDEmbedding(embedding, null, 1, null);
                                            }
                                        }, ThreadPools.getVideoInferencePool());
                            }
                        } finally {
                            personCrop.release();
                        }
                    }
                }
            }

        } else {
            // ===== INTERMEDIATE FRAME — lightweight tracker update =====
            List<TrackedFace> trackedFaces = trackingManager.updateTrackers(frame);

            for (TrackedFace tracked : trackedFaces) {
                // Append [T] suffix and use dashed bounding box for tracker-predicted frames
                String trackerLabel = tracked.getLabel();
                if (tracked.isTrackerPredicted() && !trackerLabel.endsWith(" [T]")) {
                    trackerLabel = trackerLabel + " [T]";
                }
                drawBoundingBox(frame, tracked.getBoundingBox(), null,
                        trackerLabel, tracked.getColor(), tracked.isTrackerPredicted());
            }
        }

        // ===== BODY LOCK DRAWING — runs EVERY frame (both inference + intermediate) =====
        // Body locks are independent of the face tracker lifecycle.

        // 1. ASYNC CSRT UPDATE (Prevents FPS drop)
        // Only queue a new CSRT update if the previous one has completely finished (Lock-Step Frame Dropping)
        if (isCsrtUpdating.compareAndSet(false, true)) {
            final Mat csrtFrame = frame.clone();
            final long currentIdx = currentFrameIdx;
            final List<Rect> finalFaceBoxes = currentFaceBoxes;
            
            java.util.concurrent.CompletableFuture.runAsync(() -> {
                try {
                    long startTime = System.currentTimeMillis();
                    
                    // updateBodyLocks now runs asynchronously in the background
                    trackingManager.updateBodyLocks(csrtFrame, currentIdx, finalFaceBoxes);
                    
                    long elapsed = System.currentTimeMillis() - startTime;
                    System.out.println("[DIAGNOSTIC] CSRT update completed in " + elapsed + "ms for frame " + currentIdx);
                } finally {
                    csrtFrame.release();
                    isCsrtUpdating.set(false); // Release the lock so the next frame can be processed
                }
            }, ThreadPools.getRecognitionInferencePool());
        } else {
            // Drop intermediate frame from tracker to maintain real-time sync
            System.out.println("[DIAGNOSTIC] CSRT busy. Dropping frame " + currentFrameIdx + " from tracking queue.");
        }

        // 2. SYNCHRONOUS DRAWING (Draws last known coordinates with zero latency)
        for (LockedTarget lock : trackingManager.getActiveBodyLocks()) {
            boolean faceLost = !lock.isFaceCurrentlyVisible();
            
            System.out.println("[DIAGNOSTIC] Drawing Body Lock for targetId=" + lock.getTargetId() + 
                               " at X:" + lock.getBodyBox().x() + ", Y:" + lock.getBodyBox().y() + 
                               " | FaceVisible=" + !faceLost + " | FusedConf=" + String.format("%.3f", lock.getFusedConfidence()));
                               
            drawBoundingBox(frame, lock.getBodyBox(), null,
                    lock.getDisplayLabel(), lock.getDisplayColor(), faceLost);
        }

        // === PERIODIC OSNet RE-VERIFICATION (shared frame clone, async) ===
        // First pass: check if ANY lock needs re-verification
        boolean anyNeedsReverify = false;
        for (LockedTarget lock : trackingManager.getActiveBodyLocks()) {
            if (lock.needsBodyReverification(currentFrameIdx) && bodyReIdService.isInitialized()) {
                anyNeedsReverify = true;
                break;
            }
        }

        if (anyNeedsReverify) {
            // Clone frame ONCE for ALL re-verification futures
            final Mat sharedVerifyFrame = frame.clone();
            List<CompletableFuture<Void>> reverifyFutures = new ArrayList<>();

            for (LockedTarget lock : trackingManager.getActiveBodyLocks()) {
                if (lock.needsBodyReverification(currentFrameIdx) && bodyReIdService.isInitialized()) {
                    lock.setLastBodyVerifyFrame(currentFrameIdx);
                    final LockedTarget lockRef = lock;
                    final Rect torsoBox = lockRef.getBodyBox();

                    reverifyFutures.add(CompletableFuture.runAsync(() -> {
                        Mat torsoCrop = null;
                        try {
                            int tx = Math.max(0, torsoBox.x());
                            int ty = Math.max(0, torsoBox.y());
                            int tw = Math.min(torsoBox.width(), sharedVerifyFrame.cols() - tx);
                            int th = Math.min(torsoBox.height(), sharedVerifyFrame.rows() - ty);
                            if (tw <= 0 || th <= 0) return;

                            torsoCrop = new Mat(sharedVerifyFrame, new Rect(tx, ty, tw, th));
                            float[] currentBodyEmbed = bodyReIdService.extractEmbedding(torsoCrop);
                            if (currentBodyEmbed != null && lockRef.getBodyEmbedding() != null) {
                                double sim = bodyReIdService.similarity(
                                        currentBodyEmbed, lockRef.getBodyEmbedding());
                                lockRef.setLastBodySimilarity(sim);
                                log.trace("OSNet re-verify: targetId={}, similarity={}",
                                        lockRef.getTargetId(), String.format("%.3f", sim));
                            }
                        } finally {
                            if (torsoCrop != null) torsoCrop.release();
                        }
                    }, ThreadPools.getRecognitionInferencePool()));
                }
            }

            // Release the shared clone when ALL re-verifications complete
            CompletableFuture.allOf(reverifyFutures.toArray(new CompletableFuture[0]))
                    .whenCompleteAsync((v, t) -> {
                        sharedVerifyFrame.release();
                        if (t != null) {
                            log.warn("OSNet re-verify frame released after error", t);
                        }
                    }, ThreadPools.getRecognitionInferencePool());
        }

        // Push annotated frame to the UI thread
        pushFrameToUI(frame);
    }

    /**
     * Legacy LBPH pipeline (fallback mode).
     */
    private void processFrameLbph(Mat frame) {
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

                // Trigger multi-channel alert (respects cooldown)
                String snapshotPath = saveSnapshot(frame, target.getTargetId());

                boolean alertTriggered = alertService.triggerAlert(
                        target.getTargetId(), category, target, result, snapshotPath);

                if (alertTriggered) {
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

                    // Inject sidebar alert card (replaces modal popup)
                    injectAlertCard(target, result, snapshotPath);

                    // Update dashboard metrics
                    refreshStats();
                }
            } else {
                color = AppConstants.COLOR_UNKNOWN_BGR;
                label = "Unknown";
            }

            // === ReID Pipeline (runs for ALL detected faces, async) ===
            if (configService.isReIDEnabled()) {
                Mat personCrop = faceService.extractPersonCrop(frame, faceRect);
                if (personCrop != null) {
                    final Integer targetId = (result.isMatched() && result.getMatchedTarget() != null)
                            ? result.getMatchedTarget().getTargetId() : null;
                    try {
                        byte[] jpegBytes = matToJpegBytes(personCrop);
                        if (jpegBytes != null) {
                            reidService.extractEmbedding(jpegBytes, "person_crop.jpg")
                                    .thenAcceptAsync(embedding -> {
                                        if (embedding != null) {
                                            handleReIDEmbedding(embedding, targetId, 1, null);
                                        }
                                    }, ThreadPools.getVideoInferencePool());
                        }
                    } finally {
                        personCrop.release();
                    }
                }
            }

            // Draw bounding box with WCAG-compliant label
            drawBoundingBox(frame, faceRect, null, label, color);
        }

        // Push annotated frame to the UI thread
        pushFrameToUI(frame);
    }

    /**
     * Handles a recognition result from the DNN async pipeline.
     * Called on the video inference thread after SFace embedding matching completes.
     */
    private void handleRecognitionResult(RecognitionResult result, Rect faceRect) {
        if (result.isMatched() && result.getMatchedTarget() != null) {
            TargetRegistry target = result.getMatchedTarget();
            TargetCategory category = target.getCategory();

            // Trigger multi-channel alert
            // Note: snapshot is saved from the frame that was current at detection time
            boolean alertTriggered = alertService.triggerAlert(
                    target.getTargetId(), category, target, result, null);

            if (alertTriggered) {
                DetectionLog detection = new DetectionLog(
                        target.getTargetId(),
                        result.getMatchScore(),
                        null,
                        1,
                        null
                );
                CompletableFuture.runAsync(
                        () -> detectionLogService.logDetection(detection),
                        ThreadPools.getVideoInferencePool()
                );

                // Inject sidebar alert card
                injectAlertCard(target, result, null);

                // Update reactive metrics
                refreshStats();
            }
        }
    }

    /**
     * Draws a bounding box with a WCAG AA-compliant label background.
     * The text label sits on a dark semi-transparent rectangle for readability.
     * Color coding: Red = Criminal, Blue = Missing, Green = Unknown.
     * <p>
     * Overload that defaults to a solid (non-dashed) bounding box.
     * </p>
     */
    private void drawBoundingBox(Mat frame, Rect faceRect, TargetCategory category,
                                  String label, int[] color) {
        drawBoundingBox(frame, faceRect, category, label, color, false);
    }

    /**
     * Draws a bounding box with a WCAG AA-compliant label background.
     * <p>
     * When {@code dashed} is true, the rectangle is rendered as spaced line segments
     * to visually indicate a tracker-predicted (interpolated) bounding box.
     * Solid boxes indicate a live DNN inference result.
     * </p>
     *
     * @param frame    the video frame to draw on
     * @param faceRect the bounding box rectangle
     * @param category the target category (nullable, used for color override)
     * @param label    the text label to display above the box
     * @param color    BGR color array for the bounding box
     * @param dashed   if true, draw dashed outline; if false, draw solid outline
     */
    private void drawBoundingBox(Mat frame, Rect faceRect, TargetCategory category,
                                  String label, int[] color, boolean dashed) {
        Scalar boxColor = new Scalar(color[0], color[1], color[2], 255);

        if (dashed) {
            // Draw dashed rectangle using line segments with gaps
            drawDashedRect(frame, faceRect, boxColor, 2, 10, 6);
        } else {
            // Draw solid bounding box outline
            rectangle(frame,
                    new Point(faceRect.x(), faceRect.y()),
                    new Point(faceRect.x() + faceRect.width(), faceRect.y() + faceRect.height()),
                    boxColor,
                    2, LINE_AA, 0);
        }

        // Draw WCAG-compliant dark label background (semi-transparent black)
        int textHeight = 14;
        int textWidth = label.length() * 7 + 8;
        int labelY = faceRect.y() - textHeight - 10;
        if (labelY < 0) labelY = faceRect.y() + faceRect.height() + 5; // flip below if too close to top

        rectangle(frame,
                new Point(faceRect.x(), labelY),
                new Point(faceRect.x() + textWidth, labelY + textHeight + 8),
                new Scalar(0, 0, 0, 180),  // dark semi-transparent background
                FILLED, LINE_AA, 0);

        // Draw label text (white on dark background for WCAG AA contrast)
        putText(frame, label,
                new Point(faceRect.x() + 4, labelY + textHeight + 2),
                FONT_HERSHEY_SIMPLEX, 0.5,
                new Scalar(255, 255, 255, 255),
                1, LINE_AA, false);
    }

    /**
     * Draws a dashed rectangle by iterating line segments along each edge.
     *
     * @param frame     the frame to draw on
     * @param rect      the rectangle coordinates
     * @param color     the line color
     * @param thickness the line thickness
     * @param dashLen   length of each dash in pixels
     * @param gapLen    length of each gap in pixels
     */
    private void drawDashedRect(Mat frame, Rect rect, Scalar color,
                                 int thickness, int dashLen, int gapLen) {
        int x1 = rect.x();
        int y1 = rect.y();
        int x2 = rect.x() + rect.width();
        int y2 = rect.y() + rect.height();

        // Top edge (left to right)
        drawDashedLine(frame, x1, y1, x2, y1, color, thickness, dashLen, gapLen);
        // Right edge (top to bottom)
        drawDashedLine(frame, x2, y1, x2, y2, color, thickness, dashLen, gapLen);
        // Bottom edge (right to left)
        drawDashedLine(frame, x2, y2, x1, y2, color, thickness, dashLen, gapLen);
        // Left edge (bottom to top)
        drawDashedLine(frame, x1, y2, x1, y1, color, thickness, dashLen, gapLen);
    }

    /**
     * Draws a single dashed line between two points.
     */
    private void drawDashedLine(Mat frame, int x1, int y1, int x2, int y2,
                                 Scalar color, int thickness, int dashLen, int gapLen) {
        double dx = x2 - x1;
        double dy = y2 - y1;
        double totalLength = Math.sqrt(dx * dx + dy * dy);
        if (totalLength < 1) return;

        double ux = dx / totalLength; // unit vector x
        double uy = dy / totalLength; // unit vector y

        double pos = 0;
        boolean drawing = true;

        while (pos < totalLength) {
            double segLen = drawing ? dashLen : gapLen;
            double endPos = Math.min(pos + segLen, totalLength);

            if (drawing) {
                line(frame,
                        new Point((int) (x1 + ux * pos), (int) (y1 + uy * pos)),
                        new Point((int) (x1 + ux * endPos), (int) (y1 + uy * endPos)),
                        color, thickness, LINE_AA, 0);
            }

            pos = endPos;
            drawing = !drawing;
        }
    }

    /**
     * Pushes an annotated frame to the JavaFX UI thread.
     * Also updates the blurred background fill layer.
     */
    private void pushFrameToUI(Mat frame) {
        Image fxImage = FxImageConverter.matToImage(frame);
        if (fxImage != null) {
            Platform.runLater(() -> {
                if (cameraFeed != null) {
                    cameraFeed.setImage(fxImage);
                }
                // Use same image as blurred background fill (eliminates letterboxing)
                if (cameraFeedBg != null) {
                    cameraFeedBg.setImage(fxImage);
                }
            });
        }
    }

    // ==================== Sidebar Alert Card Injection ====================

    /**
     * Injects a styled alert card into the sidebar alert queue.
     * Runs on the JavaFX Application Thread via Platform.runLater().
     * <p>
     * Card displays: profile image ↔ live snapshot, target name (bold 16px),
     * case number, category badge (pill), confidence %, timestamp.
     * </p>
     */
    private void injectAlertCard(TargetRegistry target, RecognitionResult result, String snapshotPath) {
        Platform.runLater(() -> {
            if (alertQueueBox == null) return;

            boolean isCriminal = target.getCategory() == TargetCategory.CRIMINAL;

            // Outer card container
            HBox card = new HBox(10);
            card.setAlignment(Pos.CENTER_LEFT);
            card.setPadding(new Insets(10));
            card.getStyleClass().add(isCriminal ? "alert-card-criminal" : "alert-card-missing");

            // Profile image (from database)
            ImageView profileImg = new ImageView();
            profileImg.setFitWidth(60);
            profileImg.setFitHeight(60);
            profileImg.setPreserveRatio(true);
            profileImg.setSmooth(true);
            // Rounded clip
            Rectangle profileClip = new Rectangle(60, 60);
            profileClip.setArcWidth(10);
            profileClip.setArcHeight(10);
            profileImg.setClip(profileClip);
            try {
                File profileFile = new File(target.getProfileImagePath());
                if (profileFile.exists()) {
                    profileImg.setImage(new Image(profileFile.toURI().toString(), 60, 60, true, true));
                }
            } catch (Exception e) {
                log.debug("Could not load profile image for alert card", e);
            }

            // Live snapshot (if available)
            ImageView snapImg = new ImageView();
            snapImg.setFitWidth(60);
            snapImg.setFitHeight(60);
            snapImg.setPreserveRatio(true);
            snapImg.setSmooth(true);
            Rectangle snapClip = new Rectangle(60, 60);
            snapClip.setArcWidth(10);
            snapClip.setArcHeight(10);
            snapImg.setClip(snapClip);
            if (snapshotPath != null) {
                try {
                    File snapFile = new File(snapshotPath);
                    if (snapFile.exists()) {
                        snapImg.setImage(new Image(snapFile.toURI().toString(), 60, 60, true, true));
                    }
                } catch (Exception e) {
                    log.debug("Could not load snapshot for alert card", e);
                }
            }

            // Text details
            VBox details = new VBox(3);
            details.setAlignment(Pos.CENTER_LEFT);

            // Target name (bold, 14px)
            Label nameLabel = new Label(target.getFullName());
            nameLabel.getStyleClass().add("alert-card-name");

            // Case number
            Label caseLabel = new Label("Case: " + target.getCaseNumber());
            caseLabel.getStyleClass().add("alert-card-case");

            // Category badge (pill)
            Label badge = new Label(isCriminal ? "CRIMINAL" : "MISSING");
            badge.getStyleClass().add(isCriminal ? "badge-criminal" : "badge-missing");

            // Confidence
            Label confidenceLabel = new Label("Match: " + result.getConfidencePercentage());
            confidenceLabel.getStyleClass().add("alert-card-confidence");

            // Timestamp
            Label timeLabel = new Label(LocalDateTime.now().format(
                    DateTimeFormatter.ofPattern("HH:mm:ss")));
            timeLabel.getStyleClass().add("alert-card-time");

            details.getChildren().addAll(nameLabel, caseLabel, badge, confidenceLabel, timeLabel);

            // Assemble card
            VBox imageColumn = new VBox(4);
            imageColumn.setAlignment(Pos.CENTER);
            imageColumn.getChildren().addAll(profileImg, snapImg);

            card.getChildren().addAll(imageColumn, details);

            // Prepend (newest first) to the alert queue
            alertQueueBox.getChildren().add(0, card);

            // Auto-prune if queue exceeds max size
            if (alertQueueBox.getChildren().size() > MAX_ALERT_QUEUE_SIZE) {
                alertQueueBox.getChildren().remove(
                        alertQueueBox.getChildren().size() - 1);
            }
        });
    }

    // ==================== ReID Processing ====================

    /**
     * Handles a newly extracted ReID embedding: stores it in MongoDB and
     * compares against recent embeddings from other cameras for cross-camera matching.
     */
    private void handleReIDEmbedding(double[] embedding, Integer targetId,
                                      int cameraId, String snapshotPath) {
        try {
            // Store the embedding
            PersonEmbedding pe = new PersonEmbedding(targetId, cameraId, embedding, snapshotPath);
            embeddingDAO.insert(pe);

            // Compare against recent embeddings from OTHER cameras
            int matchWindow = configService.getReIDMatchWindow();
            double threshold = configService.getReIDSimilarityThreshold();

            java.util.List<PersonEmbedding> candidates =
                    embeddingDAO.findRecentExcludingCamera(cameraId, matchWindow);

            if (candidates.isEmpty()) return;

            // Find the best match
            double bestSimilarity = 0;
            PersonEmbedding bestMatch = null;

            for (PersonEmbedding candidate : candidates) {
                if (candidate.getEmbedding() == null) continue;
                try {
                    double sim = VectorMathUtil.cosineSimilarity(embedding, candidate.getEmbedding());
                    if (sim > bestSimilarity) {
                        bestSimilarity = sim;
                        bestMatch = candidate;
                    }
                } catch (IllegalArgumentException e) {
                    // Dimension mismatch — skip this candidate
                    log.debug("Skipping embedding comparison: {}", e.getMessage());
                }
            }

            if (bestMatch != null && bestSimilarity >= threshold) {
                ReIDMatch match = new ReIDMatch(pe, bestMatch, bestSimilarity);
                log.info("REID MATCH: {} (camera {} → camera {}, similarity={})",
                        match, cameraId,
                        bestMatch.getCameraId() != null ? bestMatch.getCameraId() : "?",
                        String.format("%.3f", bestSimilarity));

                // Fire notification
                NotificationService.getInstance().showReIDAlert(match);

                // Fire Telegram alert for ReID
                if (configService.isTelegramEnabled() && bestMatch.getCameraId() != null) {
                    TelegramAlertService.getInstance().sendReIDAlert(
                            snapshotPath, cameraId, bestMatch.getCameraId(), bestSimilarity);
                }
            }

        } catch (Exception e) {
            log.warn("ReID embedding processing failed: {}", e.getMessage());
        }
    }

    /**
     * Encodes an OpenCV Mat to JPEG bytes for HTTP transport to the ReID service.
     */
    private byte[] matToJpegBytes(Mat mat) {
        try {
            String tempPath = System.getProperty("java.io.tmpdir") + "/drishtix_reid_crop.jpg";
            imwrite(tempPath, mat);
            return java.nio.file.Files.readAllBytes(java.nio.file.Path.of(tempPath));
        } catch (Exception e) {
            log.warn("Failed to encode Mat to JPEG: {}", e.getMessage());
            return null;
        }
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

        DialogPane dialogPane = dialog.getDialogPane();
        try {
            dialogPane.getStylesheets().add(getClass().getResource("/css/drishtix-dark.css").toExternalForm());
        } catch (Exception e) {
            log.warn("Could not load CSS for dialog");
        }
        // Ambient room background for the dialog window itself
        dialogPane.setStyle("-fx-background-color: linear-gradient(to bottom right, #0B0B12, #161625);");

        // Form fields wrapped in a bento card layout
        GridPane grid = new GridPane();
        grid.setHgap(20);
        grid.setVgap(20);
        grid.setPadding(new Insets(25));
        
        // Ensure columns take up 50% width each
        ColumnConstraints col1 = new ColumnConstraints();
        col1.setPercentWidth(50);
        ColumnConstraints col2 = new ColumnConstraints();
        col2.setPercentWidth(50);
        grid.getColumnConstraints().addAll(col1, col2);

        Label titleLabel = new Label("Register target from: " + selectedFile.getName());
        titleLabel.setStyle("-fx-text-fill: white; -fx-font-size: 16px; -fx-font-weight: bold;");
        grid.add(titleLabel, 0, 0, 2, 1);

        // Module 1: Name
        VBox nameTile = new VBox(8);
        nameTile.getStyleClass().add("bento-card");
        nameTile.setPadding(new Insets(15));
        Label lblName = new Label("👤 Name:");
        lblName.setStyle("-fx-text-fill: #9CA3AF;");
        TextField nameField = new TextField();
        nameField.setPromptText("Full Name");
        nameTile.getChildren().addAll(lblName, nameField);

        // Module 2: Category
        VBox catTile = new VBox(8);
        catTile.getStyleClass().add("bento-card");
        catTile.setPadding(new Insets(15));
        Label lblCat = new Label("📁 Category:");
        lblCat.setStyle("-fx-text-fill: #9CA3AF;");
        ComboBox<TargetCategory> categoryBox = new ComboBox<>();
        categoryBox.getItems().addAll(TargetCategory.values());
        categoryBox.setValue(TargetCategory.CRIMINAL);
        categoryBox.setMaxWidth(Double.MAX_VALUE);
        catTile.getChildren().addAll(lblCat, categoryBox);

        // Module 3: Case Number
        VBox caseTile = new VBox(8);
        caseTile.getStyleClass().add("bento-card");
        caseTile.setPadding(new Insets(15));
        Label lblCase = new Label("⚖ Case #:");
        lblCase.setStyle("-fx-text-fill: #9CA3AF;");
        TextField caseField = new TextField();
        caseField.setPromptText("Case/FIR Number");
        caseTile.getChildren().addAll(lblCase, caseField);

        // Module 4: Description
        VBox descTile = new VBox(8);
        descTile.getStyleClass().add("bento-card");
        descTile.setPadding(new Insets(15));
        Label lblDesc = new Label("📝 Description:");
        lblDesc.setStyle("-fx-text-fill: #9CA3AF;");
        TextArea descField = new TextArea();
        descField.setPromptText("Description (Optional)");
        descField.setPrefRowCount(2);
        descTile.getChildren().addAll(lblDesc, descField);

        // Add tiles to 2x2 grid
        grid.add(nameTile, 0, 1);
        grid.add(catTile, 1, 1);
        grid.add(caseTile, 0, 2);
        grid.add(descTile, 1, 2);

        dialogPane.setContent(grid);
        
        // Custom styling for buttons
        ButtonType okButtonType = new ButtonType("OK", ButtonBar.ButtonData.OK_DONE);
        ButtonType cancelButtonType = new ButtonType("Cancel", ButtonBar.ButtonData.CANCEL_CLOSE);
        dialogPane.getButtonTypes().addAll(okButtonType, cancelButtonType);
        
        Button okButton = (Button) dialogPane.lookupButton(okButtonType);
        okButton.setStyle("-fx-background-color: rgba(37, 99, 235, 0.4); -fx-text-fill: white; -fx-border-color: rgba(59, 130, 246, 0.5); -fx-border-radius: 6; -fx-background-radius: 6;");
        Button cancelButton = (Button) dialogPane.lookupButton(cancelButtonType);
        cancelButton.setStyle("-fx-background-color: rgba(220, 38, 38, 0.3); -fx-text-fill: white; -fx-border-color: rgba(239, 68, 68, 0.4); -fx-border-radius: 6; -fx-background-radius: 6;");

        dialog.setResultConverter(btn -> {
            if (btn == okButtonType) {
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

            // Rebuild DNN gallery if in DNN mode
            if (configService.isDnnMode()) {
                CompletableFuture.runAsync(
                        () -> recognitionService.rebuildDnnGallery(),
                        ThreadPools.getRecognitionInferencePool()
                );
            }
        });
    }

    // ==================== Stats (Reactive Properties) ====================

    public void refreshStats() {
        try {
            int total = registryService.getActiveTargetCount();
            int criminals = registryService.getCriminalCount();
            int missing = registryService.getMissingPersonCount();
            int today = detectionLogService.getTodayCount();

            Platform.runLater(() -> {
                totalTargetsProperty.set(total);
                criminalsProperty.set(criminals);
                missingProperty.set(missing);
                detectionsProperty.set(today);

                if (lblRecognizerStatus != null) {
                    lblRecognizerStatus.setText(recognitionService.isTrained() ? "● Trained" : "○ Not Trained");
                    lblRecognizerStatus.setStyle(recognitionService.isTrained()
                            ? "-fx-text-fill: #22C55E;" : "-fx-text-fill: #FBBF24;");
                }
            });
        } catch (Exception e) {
            log.warn("Failed to refresh stats", e);
        }
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

    // ==================== Header Icon Handlers ====================

    @FXML
    private void handleNotificationsClick() {
        Platform.runLater(() -> {
            Notifications.create()
                    .title("Notifications")
                    .text("You have no new alerts.")
                    .position(Pos.TOP_RIGHT)
                    .hideAfter(Duration.seconds(3))
                    .showInformation();
        });
    }

    @FXML
    private void handleProfileClick() {
        Platform.runLater(() -> {
            Notifications.create()
                    .title("Profile Settings")
                    .text("System Administrator mode is active.")
                    .position(Pos.TOP_RIGHT)
                    .hideAfter(Duration.seconds(3))
                    .showInformation();
        });
    }
}
