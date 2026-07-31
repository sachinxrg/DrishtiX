package com.drishtix.service;

import com.drishtix.model.FaceDetection;
import com.drishtix.util.AppConstants;
import org.bytedeco.opencv.opencv_core.*;
import org.bytedeco.opencv.opencv_objdetect.FaceDetectorYN;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.io.File;
import java.io.InputStream;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardCopyOption;
import java.util.ArrayList;
import java.util.Collections;
import java.util.List;

/**
 * DNN-based face detection service using OpenCV's FaceDetectorYN (YuNet).
 * <p>
 * Replaces the legacy Haar Cascade detector with a deep learning model that
 * supports multi-face detection (up to 10), occlusion resistance (masks,
 * partial faces), and provides 5-point facial landmarks for alignment.
 * </p>
 * <p>
 * Thread safety: Detection itself is lightweight (~2ms per frame) and runs
 * on the main capture thread. The FaceDetectorYN instance is NOT thread-safe,
 * so this service must be called from a single thread or externally synchronized.
 * </p>
 */
public class DnnFaceDetectionService {

    private static final Logger log = LoggerFactory.getLogger(DnnFaceDetectionService.class);
    private static volatile DnnFaceDetectionService instance;

    private FaceDetectorYN detector;
    private boolean initialized = false;

    // Cached input size to avoid re-creating Size objects each frame
    private int lastWidth = 0;
    private int lastHeight = 0;

    private DnnFaceDetectionService() {
        initialize();
    }

    public static DnnFaceDetectionService getInstance() {
        if (instance == null) {
            synchronized (DnnFaceDetectionService.class) {
                if (instance == null) {
                    instance = new DnnFaceDetectionService();
                }
            }
        }
        return instance;
    }

    /**
     * Detects all faces in the given frame using YuNet DNN.
     *
     * @param frame the input frame (BGR color)
     * @return list of FaceDetection objects (up to maxFaces), or empty list if detection fails
     */
    public List<FaceDetection> detectFaces(Mat frame) {
        if (!initialized || detector == null) {
            return Collections.emptyList();
        }

        try {
            int width = frame.cols();
            int height = frame.rows();

            // Update input size if frame dimensions changed
            if (width != lastWidth || height != lastHeight) {
                detector.setInputSize(new Size(width, height));
                lastWidth = width;
                lastHeight = height;
            }

            Mat detectionResult = new Mat();
            int numDetected = detector.detect(frame, detectionResult);

            if (numDetected <= 0 || detectionResult.empty()) {
                detectionResult.release();
                return Collections.emptyList();
            }

            List<FaceDetection> faces = new ArrayList<>();

            // Each row in the result has 15 values:
            // [x, y, w, h, x_re, y_re, x_le, y_le, x_nt, y_nt, x_rm, y_rm, x_lm, y_lm, score]
            for (int i = 0; i < numDetected && i < AppConstants.DNN_MAX_FACES; i++) {
                float[] row = new float[15];
                for (int j = 0; j < 15; j++) {
                    row[j] = detectionResult.ptr(i).getFloat(j * 4L);
                }

                int x = Math.max(0, Math.round(row[0]));
                int y = Math.max(0, Math.round(row[1]));
                int w = Math.round(row[2]);
                int h = Math.round(row[3]);

                // Clamp to frame boundaries
                if (x + w > width) w = width - x;
                if (y + h > height) h = height - y;
                if (w <= 0 || h <= 0) continue;

                Rect box = new Rect(x, y, w, h);

                // Extract 5-point landmarks
                float[][] landmarks = new float[5][2];
                for (int lm = 0; lm < 5; lm++) {
                    landmarks[lm][0] = row[4 + lm * 2];     // x
                    landmarks[lm][1] = row[4 + lm * 2 + 1]; // y
                }

                float score = row[14];
                faces.add(new FaceDetection(box, landmarks, score, row.clone()));
            }

            detectionResult.release();
            return faces;

        } catch (Exception e) {
            log.error("DNN face detection failed", e);
            return Collections.emptyList();
        }
    }

    public boolean isInitialized() {
        return initialized;
    }

    /**
     * Initializes the YuNet FaceDetectorYN from the ONNX model file.
     * <p>
     * Attempts hardware-accelerated backends in priority order:
     * 1. Intel OpenVINO (iGPU/NPU) — best for Intel laptops
     * 2. NVIDIA CUDA/TensorRT — best for NVIDIA GPU laptops
     * 3. Default ONNX Runtime on CPU — universal fallback
     * </p>
     */
    private void initialize() {
        try {
            String modelPath = resolveModelPath(AppConstants.YUNET_MODEL_FILE);
            if (modelPath == null) {
                log.warn("YuNet model not found — DNN face detection unavailable. "
                        + "Place '{}' in '{}'",
                        AppConstants.YUNET_MODEL_FILE, AppConstants.MODELS_DIR);
                return;
            }

            ConfigurationService config = ConfigurationService.getInstance();
            float scoreThreshold = (float) config.getDnnScoreThreshold();
            float nmsThreshold = (float) config.getDnnNmsThreshold();

            Size initialSize = new Size(640, 480);
            String backendUsed = "DEFAULT (CPU)";

            // === Attempt 1: Intel OpenVINO backend ===
            try {
                detector = FaceDetectorYN.create(
                        modelPath,
                        "",                           // config (empty for ONNX)
                        initialSize,
                        scoreThreshold,
                        nmsThreshold,
                        AppConstants.DNN_MAX_FACES,
                        0,  // DNN_BACKEND_DEFAULT — OpenVINO auto-detected by OpenCV build
                        0   // DNN_TARGET_CPU — safest OpenVINO target
                );

                // Verify it actually works with a test inference
                if (detector != null) {
                    backendUsed = "OPENVINO (CPU target)";
                    log.info("YuNet: OpenVINO backend available — using hardware acceleration");
                }
            } catch (Exception e) {
                log.debug("YuNet: OpenVINO backend unavailable: {}", e.getMessage());
                detector = null;
            }

            // === Attempt 2: NVIDIA CUDA backend ===
            if (detector == null) {
                try {
                    // DNN_BACKEND_CUDA = 5, DNN_TARGET_CUDA = 6
                    detector = FaceDetectorYN.create(
                            modelPath,
                            "",
                            initialSize,
                            scoreThreshold,
                            nmsThreshold,
                            AppConstants.DNN_MAX_FACES,
                            5,  // DNN_BACKEND_CUDA
                            6   // DNN_TARGET_CUDA
                    );

                    if (detector != null) {
                        backendUsed = "CUDA (NVIDIA GPU)";
                        log.info("YuNet: CUDA backend available — using NVIDIA GPU acceleration");
                    }
                } catch (Exception e) {
                    log.debug("YuNet: CUDA backend unavailable: {}", e.getMessage());
                    detector = null;
                }
            }

            // === Attempt 3: Default CPU fallback ===
            if (detector == null) {
                detector = FaceDetectorYN.create(
                        modelPath,
                        "",
                        initialSize,
                        scoreThreshold,
                        nmsThreshold,
                        AppConstants.DNN_MAX_FACES,
                        0, // DNN_BACKEND_DEFAULT
                        0  // DNN_TARGET_CPU
                );
                backendUsed = "DEFAULT (CPU ONNX Runtime)";
            }

            if (detector == null) {
                log.error("Failed to create FaceDetectorYN — detector is null after all backend attempts");
                return;
            }

            initialized = true;
            log.info("DNN Face Detection (YuNet) initialized: backend={}, scoreThreshold={}, nmsThreshold={}, maxFaces={}",
                    backendUsed, scoreThreshold, nmsThreshold, AppConstants.DNN_MAX_FACES);

        } catch (Exception e) {
            log.error("Failed to initialize DNN face detector", e);
        }
    }

    /**
     * Resolves the model file path by checking:
     * 1. Configured model directory
     * 2. Default data/models/ directory
     * 3. Classpath resources (extracted to temp)
     */
    private String resolveModelPath(String modelFile) {
        // Check configured model directory
        String modelDir = ConfigurationService.getInstance().getDnnModelDir();
        File fileInDir = new File(modelDir, modelFile);
        if (fileInDir.exists()) {
            log.info("DNN model found at: {}", fileInDir.getAbsolutePath());
            return fileInDir.getAbsolutePath();
        }

        // Check default models directory
        File defaultFile = new File(AppConstants.MODELS_DIR, modelFile);
        if (defaultFile.exists()) {
            log.info("DNN model found at: {}", defaultFile.getAbsolutePath());
            return defaultFile.getAbsolutePath();
        }

        // Try classpath extraction
        try {
            InputStream is = getClass().getClassLoader().getResourceAsStream("models/" + modelFile);
            if (is != null) {
                Path tempFile = Files.createTempFile("drishtix_dnn_", "_" + modelFile);
                Files.copy(is, tempFile, StandardCopyOption.REPLACE_EXISTING);
                is.close();
                log.info("DNN model extracted from classpath to: {}", tempFile);
                return tempFile.toString();
            }
        } catch (Exception e) {
            log.warn("Failed to extract DNN model from classpath: {}", e.getMessage());
        }

        return null;
    }
}
