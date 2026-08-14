package com.drishtix.controller;

import com.drishtix.model.FaceDetection;
import com.drishtix.model.RecognitionResult;
import com.drishtix.model.TargetCategory;
import com.drishtix.model.TargetRegistry;
import com.drishtix.service.*;
import com.drishtix.util.AppConstants;
import com.drishtix.util.FxImageConverter;
import javafx.fxml.FXML;
import javafx.scene.control.Button;
import javafx.scene.control.Label;
import javafx.scene.image.Image;
import javafx.scene.image.ImageView;
import javafx.stage.FileChooser;
import org.bytedeco.opencv.opencv_core.*;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.io.File;
import java.util.List;

import static org.bytedeco.opencv.global.opencv_imgcodecs.*;
import static org.bytedeco.opencv.global.opencv_imgproc.*;

/**
 * Controller for the static image / CCTV frame scanning module.
 * <p>
 * Supports DNN mode (YuNet + SFace) for high-accuracy multi-face scanning in crowded scenes
 * (capable of detecting and recognizing 40+ to 200 faces simultaneously).
 * </p>
 */
public class ImageScanController {

    private static final Logger log = LoggerFactory.getLogger(ImageScanController.class);

    @FXML private ImageView originalImageView;
    @FXML private ImageView annotatedImageView;
    @FXML private Button btnUpload;
    @FXML private Button btnSave;
    @FXML private Label lblResults;

    private final FaceProcessingService faceService = FaceProcessingService.getInstance();
    private final RecognitionService recognitionService = RecognitionService.getInstance();
    private final ConfigurationService configService = ConfigurationService.getInstance();

    private Mat annotatedMat;

    @FXML
    public void handleUploadAndScan() {
        FileChooser fc = new FileChooser();
        fc.setTitle("Upload Image for Scanning");
        fc.getExtensionFilters().add(new FileChooser.ExtensionFilter("Images", "*.jpg", "*.jpeg", "*.png"));
        File file = fc.showOpenDialog(originalImageView.getScene().getWindow());
        if (file == null) return;

        // Load original image
        Mat original = imread(file.getAbsolutePath());
        if (original.empty()) {
            if (lblResults != null) lblResults.setText("Failed to load image.");
            return;
        }

        // Display original
        Image origFx = FxImageConverter.matToImage(original);
        if (originalImageView != null) originalImageView.setImage(origFx);

        // Clone for annotation
        if (annotatedMat != null) annotatedMat.release();
        annotatedMat = original.clone();

        int matchedCount;
        int totalFaces;

        // Dynamic styling variables based on image resolution
        int thickness = Math.max(2, Math.round(annotatedMat.cols() / 600.0f));
        double fontScale = Math.max(0.4, Math.min(1.0, annotatedMat.cols() / 1400.0));

        if (configService.isDnnMode() && DnnFaceDetectionService.getInstance().isInitialized()) {
            // === DNN MODE: YuNet multi-face detection + SFace recognition (supports 40+ faces) ===
            DnnFaceDetectionService dnnDetector = DnnFaceDetectionService.getInstance();
            DnnFaceRecognitionService dnnRecognizer = DnnFaceRecognitionService.getInstance();
            double threshold = configService.getDnnCosineThreshold();

            List<FaceDetection> detections = dnnDetector.detectFaces(annotatedMat);
            totalFaces = detections.size();
            matchedCount = 0;

            for (FaceDetection detection : detections) {
                Rect faceRect = detection.getBoundingBox();
                float[] detRow = detection.getDetectionRow();

                float[] embedding = dnnRecognizer.alignAndExtractEmbedding(annotatedMat, detRow);
                RecognitionResult result = (embedding != null)
                        ? dnnRecognizer.matchAgainstGallery(embedding, threshold)
                        : RecognitionResult.unknownDnn(0);

                int[] color;
                String label;

                if (result.isMatched() && result.getMatchedTarget() != null) {
                    TargetRegistry target = result.getMatchedTarget();
                    color = (target.getCategory() == TargetCategory.CRIMINAL)
                            ? AppConstants.COLOR_CRIMINAL_BGR : AppConstants.COLOR_MISSING_BGR;
                    label = target.getFullName() + " | " + target.getCaseNumber();
                    matchedCount++;
                } else {
                    color = AppConstants.COLOR_UNKNOWN_BGR;
                    label = "Unknown";
                }

                drawFaceAnnotation(annotatedMat, faceRect, label, color, thickness, fontScale);
            }

        } else {
            // === LEGACY FALLBACK: Haar Cascade + LBPH ===
            RectVector faces = faceService.detectFaces(annotatedMat);
            totalFaces = (int) faces.size();
            matchedCount = 0;

            for (long i = 0; i < faces.size(); i++) {
                Rect faceRect = faces.get(i);
                Mat faceROI = faceService.extractFaceROI(annotatedMat, faceRect);
                RecognitionResult result = recognitionService.predict(faceROI);
                faceROI.release();

                int[] color;
                String label;

                if (result.isMatched() && result.getMatchedTarget() != null) {
                    TargetRegistry target = result.getMatchedTarget();
                    color = (target.getCategory() == TargetCategory.CRIMINAL)
                            ? AppConstants.COLOR_CRIMINAL_BGR : AppConstants.COLOR_MISSING_BGR;
                    label = target.getFullName() + " | " + target.getCaseNumber();
                    matchedCount++;
                } else {
                    color = AppConstants.COLOR_UNKNOWN_BGR;
                    label = "Unknown";
                }

                drawFaceAnnotation(annotatedMat, faceRect, label, color, thickness, fontScale);
            }
        }

        // Display annotated image
        Image annotFx = FxImageConverter.matToImage(annotatedMat);
        if (annotatedImageView != null) annotatedImageView.setImage(annotFx);

        // Update results label
        if (lblResults != null) {
            lblResults.setText(String.format("Scanned: %d faces detected | %d targets matched", totalFaces, matchedCount));
        }

        if (btnSave != null) btnSave.setDisable(false);
        original.release();

        log.info("Image scan complete: {} faces detected, {} matched (DNN={})",
                totalFaces, matchedCount, configService.isDnnMode());
    }

    /**
     * Draws bounding box and contrast-enhanced text label for a detected face.
     * Prevents text clipping near top frame boundaries.
     */
    private void drawFaceAnnotation(Mat mat, Rect rect, String label, int[] color, int thickness, double fontScale) {
        // Draw bounding box
        rectangle(mat,
                new Point(rect.x(), rect.y()),
                new Point(rect.x() + rect.width(), rect.y() + rect.height()),
                new Scalar(color[0], color[1], color[2], 255), thickness, LINE_AA, 0);

        // Safe label Y position (ensures text is never clipped at top boundary)
        int textY = Math.max(22, rect.y() - 6);

        // Text background box for high legibility in crowded photos
        int[] base = new int[1];
        Size textSize = getTextSize(label, FONT_HERSHEY_SIMPLEX, fontScale, 1, base);
        rectangle(mat,
                new Point(rect.x(), textY - textSize.height() - 4),
                new Point(rect.x() + textSize.width() + 6, textY + base[0]),
                new Scalar(15, 23, 42, 220), -1, LINE_AA, 0);

        // Draw label text
        putText(mat, label,
                new Point(rect.x() + 3, textY - 2),
                FONT_HERSHEY_SIMPLEX, fontScale,
                new Scalar(color[0], color[1], color[2], 255), 1, LINE_AA, false);
    }

    @FXML
    public void handleSaveResult() {
        if (annotatedMat == null || annotatedMat.empty()) return;

        FileChooser fc = new FileChooser();
        fc.setTitle("Save Annotated Image");
        fc.getExtensionFilters().add(new FileChooser.ExtensionFilter("PNG", "*.png"));
        fc.setInitialFileName("DrishtiX_Scan_Result.png");
        File file = fc.showSaveDialog(annotatedImageView.getScene().getWindow());

        if (file != null) {
            imwrite(file.getAbsolutePath(), annotatedMat);
            log.info("Annotated image saved: {}", file.getAbsolutePath());
        }
    }
}
