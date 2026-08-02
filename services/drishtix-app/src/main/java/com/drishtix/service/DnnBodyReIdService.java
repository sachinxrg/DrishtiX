package com.drishtix.service;

import com.drishtix.util.AppConstants;
import org.bytedeco.javacpp.indexer.FloatIndexer;
import org.bytedeco.opencv.opencv_core.*;
import org.bytedeco.opencv.opencv_dnn.Net;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.io.File;
import java.io.InputStream;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardCopyOption;

import static org.bytedeco.opencv.global.opencv_core.*;
import static org.bytedeco.opencv.global.opencv_dnn.*;
import static org.bytedeco.opencv.global.opencv_imgproc.*;

/**
 * DNN-based whole-body Re-Identification service using OSNet (x0.25, MSMT17).
 * <p>
 * Extracts 512-dimensional L2-normalized appearance embeddings from person
 * torso/body crops, enabling identity persistence when facial landmarks are
 * lost (head turned, back to camera).
 * </p>
 * <p>
 * Architecture:
 * - Singleton with ThreadLocal&lt;Net&gt; for safe concurrent access
 * - Runs on the recognition inference pool (never on the capture thread)
 * - Input: 256×128 BGR torso crop → Output: 512-dim L2-normalized float[]
 * </p>
 * <p>
 * Thread safety: ThreadLocal ensures each pool thread has its own Net instance.
 * The service itself is stateless after initialization.
 * </p>
 */
public class DnnBodyReIdService {

    private static final Logger log = LoggerFactory.getLogger(DnnBodyReIdService.class);
    private static volatile DnnBodyReIdService instance;

    private final ThreadLocal<Net> netLocal = new ThreadLocal<>();
    private String modelPath;
    private boolean initialized = false;

    private DnnBodyReIdService() {
        initialize();
    }

    public static DnnBodyReIdService getInstance() {
        if (instance == null) {
            synchronized (DnnBodyReIdService.class) {
                if (instance == null) {
                    instance = new DnnBodyReIdService();
                }
            }
        }
        return instance;
    }

    /**
     * Extracts a 512-dimensional L2-normalized body appearance embedding
     * from a person torso crop.
     * <p>
     * The input is resized internally to 256×128 (OSNet's training size).
     * Pixel values are normalized to [0, 1] and mean-subtracted using
     * ImageNet statistics (matching OSNet's training preprocessing).
     * </p>
     *
     * @param torsoCrop the BGR torso crop from the frame (any resolution)
     * @return L2-normalized 512-dim float embedding, or null on failure
     */
    public float[] extractEmbedding(Mat torsoCrop) {
        if (!initialized || torsoCrop == null || torsoCrop.empty()) {
            return null;
        }

        Mat resized = null;
        Mat blob = null;
        Mat output = null;
        try {
            Net net = netLocal.get();
            if (net == null) {
                net = createNetInstance();
                if (net == null) return null;
                netLocal.set(net);
                log.debug("OSNet Net initialized for thread: {}", Thread.currentThread().getName());
            }

            // Resize to OSNet input: 256×128 (H×W)
            resized = new Mat();
            resize(torsoCrop, resized,
                    new Size(AppConstants.OSNET_INPUT_WIDTH, AppConstants.OSNET_INPUT_HEIGHT));

            // Create blob: scale 1/255.0, size 256×128, mean subtraction (ImageNet stats)
            // OSNet expects [0,1] normalized pixels with ImageNet mean subtraction
            blob = blobFromImage(resized,
                    1.0 / 255.0,
                    new Size(AppConstants.OSNET_INPUT_WIDTH, AppConstants.OSNET_INPUT_HEIGHT),
                    new Scalar(0.485 * 255, 0.456 * 255, 0.406 * 255, 0), // BGR mean
                    true,   // swapRB: BGR → RGB
                    false,  // crop
                    CV_32F  // ddepth — required by JavaCV binding
            );

            // Forward pass
            net.setInput(blob);
            output = net.forward();

            if (output.empty()) {
                log.warn("OSNet forward pass returned empty output");
                return null;
            }

            // Extract embedding from output Mat (1 × N)
            int cols = output.total() > 0 ? (int) output.total() : 0;
            if (cols == 0) return null;

            float[] embedding = new float[cols];
            try (FloatIndexer idx = output.reshape(1, cols).createIndexer()) {
                for (int i = 0; i < cols; i++) {
                    embedding[i] = idx.get(0, i);
                }
            }

            // L2-normalize for cosine similarity via dot product
            l2Normalize(embedding);

            return embedding;

        } catch (Exception e) {
            log.error("OSNet embedding extraction failed", e);
            return null;
        } finally {
            if (resized != null) resized.release();
            if (blob != null) blob.release();
            if (output != null) output.release();
        }
    }

    /**
     * Computes cosine similarity between two L2-normalized body embeddings.
     * Since both vectors are unit-length, this is a simple dot product.
     *
     * @return similarity in [-1, 1], typically [0, 1] for appearance vectors
     */
    public double similarity(float[] a, float[] b) {
        if (a == null || b == null || a.length != b.length) return 0;
        double sum = 0;
        for (int i = 0; i < a.length; i++) {
            sum += a[i] * b[i];
        }
        return sum;
    }

    /**
     * Expands a face bounding box downward to capture the upper torso region.
     * The expansion is clipped to frame boundaries.
     *
     * @param faceBox        the face bounding box from YuNet
     * @param frameWidth     the frame width (for clipping)
     * @param frameHeight    the frame height (for clipping)
     * @param expansionRatio how much to expand downward (2.0 = 200%)
     * @return the expanded torso bounding box, clipped to frame bounds
     */
    public static Rect expandFaceToTorso(Rect faceBox, int frameWidth, int frameHeight,
                                          double expansionRatio) {
        int faceW = faceBox.width();
        int faceH = faceBox.height();

        // 1. Wider torso: expand 50% to capture full shoulder width for robust CSRT tracking
        int torsoW = (int) (faceW * 1.5);
        int torsoX = faceBox.x() - (torsoW - faceW) / 2;

        // 2. Shift Y downwards: Start from mid-face (captures neck + shoulders for stability)
        int torsoY = faceBox.y() + (int) (faceH * 0.6);
        
        // 3. Torso height: extend down relative to face height
        int torsoH = (int) (faceH * expansionRatio);

        // Clip to frame boundaries
        torsoX = Math.max(0, torsoX);
        torsoY = Math.max(0, torsoY);
        if (torsoX + torsoW > frameWidth) torsoW = frameWidth - torsoX;
        if (torsoY + torsoH > frameHeight) torsoH = frameHeight - torsoY;

        if (torsoW <= 0 || torsoH <= 0) return faceBox; // fallback to face box

        return new Rect(torsoX, torsoY, torsoW, torsoH);
    }

    public boolean isInitialized() {
        return initialized;
    }

    // ==================== Internal Methods ====================

    /**
     * L2-normalizes an embedding in-place so cosine similarity == dot product.
     */
    private void l2Normalize(float[] embedding) {
        double norm = 0;
        for (float v : embedding) norm += v * v;
        norm = Math.sqrt(norm);
        if (norm > 0) {
            for (int i = 0; i < embedding.length; i++) {
                embedding[i] = (float) (embedding[i] / norm);
            }
        }
    }

    /**
     * Creates a new Net instance for the calling thread.
     * Attempts CUDA then falls back to CPU.
     */
    private Net createNetInstance() {
        try {
            Net net = readNetFromONNX(modelPath);
            if (net.empty()) {
                log.error("OSNet model loaded but Net is empty");
                return null;
            }

            // Try CUDA backend first
            try {
                net.setPreferableBackend(DNN_BACKEND_CUDA);
                net.setPreferableTarget(DNN_TARGET_CUDA);
                log.debug("OSNet using CUDA backend");
            } catch (Exception e) {
                // Fall back to CPU
                net.setPreferableBackend(DNN_BACKEND_OPENCV);
                net.setPreferableTarget(DNN_TARGET_CPU);
                log.debug("OSNet using CPU backend (CUDA unavailable)");
            }

            return net;
        } catch (Exception e) {
            log.error("Failed to create OSNet Net instance", e);
            return null;
        }
    }

    /**
     * Initializes the service by resolving the OSNet ONNX model path.
     */
    private void initialize() {
        try {
            modelPath = resolveModelPath(AppConstants.OSNET_MODEL_FILE);
            if (modelPath == null) {
                log.warn("OSNet model not found — body Re-ID unavailable. "
                        + "Place '{}' in '{}'",
                        AppConstants.OSNET_MODEL_FILE, AppConstants.MODELS_DIR);
                return;
            }

            // Validate model loads successfully
            Net testNet = createNetInstance();
            if (testNet == null) {
                log.error("Failed to load OSNet model — body Re-ID unavailable");
                return;
            }

            // Seed ThreadLocal for the current thread
            netLocal.set(testNet);
            initialized = true;
            log.info("DNN Body Re-ID (OSNet x0.25) initialized. Model={}", modelPath);

        } catch (Exception e) {
            log.error("Failed to initialize OSNet body Re-ID service", e);
        }
    }

    /**
     * Resolves the model file path (same strategy as DnnFaceRecognitionService).
     */
    private String resolveModelPath(String modelFile) {
        String modelDir = ConfigurationService.getInstance().getDnnModelDir();
        File fileInDir = new File(modelDir, modelFile);
        if (fileInDir.exists()) {
            return fileInDir.getAbsolutePath();
        }

        File defaultFile = new File(AppConstants.MODELS_DIR, modelFile);
        if (defaultFile.exists()) {
            return defaultFile.getAbsolutePath();
        }

        try {
            InputStream is = getClass().getClassLoader().getResourceAsStream("models/" + modelFile);
            if (is != null) {
                Path tempFile = Files.createTempFile("drishtix_osnet_", "_" + modelFile);
                Files.copy(is, tempFile, StandardCopyOption.REPLACE_EXISTING);
                is.close();
                return tempFile.toString();
            }
        } catch (Exception e) {
            log.warn("Failed to extract OSNet model from classpath: {}", e.getMessage());
        }

        return null;
    }
}
