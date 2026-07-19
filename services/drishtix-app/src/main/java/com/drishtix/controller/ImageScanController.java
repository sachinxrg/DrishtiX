package com.drishtix.controller;

import com.drishtix.model.RecognitionResult;
import com.drishtix.model.TargetCategory;
import com.drishtix.model.TargetRegistry;
import com.drishtix.service.FaceProcessingService;
import com.drishtix.service.RecognitionService;
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

import static org.bytedeco.opencv.global.opencv_imgcodecs.*;
import static org.bytedeco.opencv.global.opencv_imgproc.*;

/**
 * Controller for the static image / CCTV frame scanning module.
 * Allows uploading a crowded photo and scanning all faces against the watchlist.
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

        // Detect all faces
        RectVector faces = faceService.detectFaces(annotatedMat);
        int matchedCount = 0;
        int totalFaces = (int) faces.size();

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

            // Draw bounding box
            rectangle(annotatedMat,
                    new Point(faceRect.x(), faceRect.y()),
                    new Point(faceRect.x() + faceRect.width(), faceRect.y() + faceRect.height()),
                    new Scalar(color[0], color[1], color[2], 255), 2, LINE_AA, 0);

            // Draw label
            putText(annotatedMat, label,
                    new Point(faceRect.x(), faceRect.y() - 8),
                    FONT_HERSHEY_SIMPLEX, 0.5,
                    new Scalar(255, 255, 255, 255), 1, LINE_AA, false);
        }

        // Display annotated image
        Image annotFx = FxImageConverter.matToImage(annotatedMat);
        if (annotatedImageView != null) annotatedImageView.setImage(annotFx);

        // Update results label
        if (lblResults != null) {
            lblResults.setText(String.format("Detected: %d faces | Matched: %d targets", totalFaces, matchedCount));
        }

        if (btnSave != null) btnSave.setDisable(false);
        original.release();

        log.info("Image scan complete: {} faces detected, {} matched", totalFaces, matchedCount);
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
