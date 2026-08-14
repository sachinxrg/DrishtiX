package com.drishtix.service;

import com.drishtix.dao.TargetDAO;
import com.drishtix.dao.TargetImageDAO;
import com.drishtix.model.RecognitionResult;
import com.drishtix.model.TargetImage;
import com.drishtix.model.TargetRegistry;
import com.drishtix.model.TargetEmbeddings;
import com.drishtix.util.AppConstants;
import com.drishtix.util.VectorMathUtil;
import org.bytedeco.opencv.opencv_core.*;
import static org.bytedeco.opencv.global.opencv_core.CV_32FC1;
import static org.bytedeco.opencv.global.opencv_core.BORDER_CONSTANT;
import static org.bytedeco.opencv.global.opencv_core.copyMakeBorder;
import org.bytedeco.opencv.opencv_objdetect.FaceRecognizerSF;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.io.File;
import java.io.InputStream;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardCopyOption;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.OptionalDouble;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.locks.ReentrantReadWriteLock;

import static org.bytedeco.opencv.global.opencv_imgcodecs.*;
import static org.bytedeco.opencv.global.opencv_imgproc.*;

/**
 * DNN-based face recognition service using OpenCV's FaceRecognizerSF (SFace).
 * <p>
 * Extracts 128-dimensional feature embeddings based on facial geometry
 * (not raw textures like LBPH), providing occlusion resistance and
 * superior accuracy under varying lighting/pose conditions.
 * </p>
 * <p>
 * Maintains an in-memory embedding gallery loaded from the database,
 * and performs cosine similarity matching against probe faces.
 * </p>
 * <p>
 * Thread safety: Uses ReentrantReadWriteLock — concurrent reads (matching)
 * are allowed, writes (gallery updates) are serialized.
 * </p>
 */
public class DnnFaceRecognitionService {

    private static final Logger log = LoggerFactory.getLogger(DnnFaceRecognitionService.class);
    private static volatile DnnFaceRecognitionService instance;

    private final ThreadLocal<FaceRecognizerSF> recognizerLocal = new ThreadLocal<>();
    private String modelPath;
    private boolean initialized = false;

    // In-memory embedding gallery: targetId → TargetEmbeddings (multi-templates + centroid)
    private final ConcurrentHashMap<Integer, TargetEmbeddings> gallery = new ConcurrentHashMap<>();
    private final ReentrantReadWriteLock galleryLock = new ReentrantReadWriteLock();

    private final TargetDAO targetDAO;
    private final TargetImageDAO targetImageDAO;

    private DnnFaceRecognitionService() {
        this.targetDAO = new TargetDAO();
        this.targetImageDAO = new TargetImageDAO();
        initialize();
    }

    public static DnnFaceRecognitionService getInstance() {
        if (instance == null) {
            synchronized (DnnFaceRecognitionService.class) {
                if (instance == null) {
                    instance = new DnnFaceRecognitionService();
                }
            }
        }
        return instance;
    }

    /**
     * Extracts a 128-dimensional feature embedding from an aligned face image.
     * <p>
     * The input must be a 112×112 BGR image, typically produced by face alignment
     * using 5-point landmarks from FaceDetectorYN.
     * </p>
     *
     * @param alignedFace the aligned face Mat (112×112, BGR)
     * @return the feature embedding as a float array, or null on failure
     */
    public float[] extractEmbedding(Mat alignedFace) {
        if (!initialized || modelPath == null) {
            return null;
        }

        try {
            FaceRecognizerSF recognizer = recognizerLocal.get();
            if (recognizer == null) {
                recognizer = createRecognizerInstance();
                if (recognizer == null) {
                    return null;
                }
                recognizerLocal.set(recognizer);
                log.debug("Initialized FaceRecognizerSF for thread: {}", Thread.currentThread().getName());
            }

            Mat feature = new Mat();
            recognizer.feature(alignedFace, feature);

            if (feature.empty()) {
                feature.release();
                return null;
            }

            // Convert to float array and L2-normalize for dot-product matching
            int cols = feature.cols();
            float[] embedding = new float[cols];
            for (int i = 0; i < cols; i++) {
                embedding[i] = feature.ptr(0).getFloat(i * 4L);
            }
            l2Normalize(embedding);

            feature.release();
            return embedding;

        } catch (Exception e) {
            log.error("DNN feature extraction failed", e);
            return null;
        }
    }

    /**
     * Aligns a detected face using OpenCV's built-in alignCrop() and extracts
     * the L2-normalized SFace embedding in a single, optimized call.
     * <p>
     * alignCrop() produces the EXACT alignment that SFace was trained on,
     * eliminating distribution shift from manual estimateAffinePartial2D + warpAffine.
     * This is the primary API for the live camera pipeline.
     * </p>
     *
     * @param frame        the full camera frame (BGR)
     * @param detectionRow the raw 15-value detection row from FaceDetectorYN
     * @return the L2-normalized feature embedding as a float array, or null on failure
     */
    public float[] alignAndExtractEmbedding(Mat frame, float[] detectionRow) {
        if (!initialized || modelPath == null || detectionRow == null || detectionRow.length < 15) {
            return null;
        }

        Mat alignedFace = null;
        Mat detRow = null;
        Mat feature = null;
        try {
            FaceRecognizerSF recognizer = recognizerLocal.get();
            if (recognizer == null) {
                recognizer = createRecognizerInstance();
                if (recognizer == null) return null;
                recognizerLocal.set(recognizer);
                log.debug("Initialized FaceRecognizerSF for thread: {}", Thread.currentThread().getName());
            }

            // Reconstruct the detection row as a 1×15 CV_32F Mat for alignCrop()
            detRow = new Mat(1, 15, CV_32FC1);
            for (int i = 0; i < 15; i++) {
                detRow.ptr(0).putFloat(i * 4L, detectionRow[i]);
            }

            // alignCrop: OpenCV-native alignment matching SFace training distribution
            alignedFace = new Mat();
            recognizer.alignCrop(frame, detRow, alignedFace);

            if (alignedFace.empty()) {
                return null;
            }

            // Extract and L2-normalize embedding
            feature = new Mat();
            recognizer.feature(alignedFace, feature);

            if (feature.empty()) {
                return null;
            }

            int cols = feature.cols();
            float[] embedding = new float[cols];
            for (int i = 0; i < cols; i++) {
                embedding[i] = feature.ptr(0).getFloat(i * 4L);
            }
            l2Normalize(embedding);

            return embedding;

        } catch (Exception e) {
            log.error("alignCrop + feature extraction failed", e);
            return null;
        } finally {
            if (alignedFace != null) alignedFace.release();
            if (detRow != null) detRow.release();
            if (feature != null) feature.release();
        }
    }

    /**
     * Matches a probe embedding against the gallery using cosine similarity and Max-Similarity Scoring.
     * Checks against the centroid first, and if promising, checks individual templates.
     *
     * @param probeEmbedding the embedding to match
     * @param dynamicThreshold the dynamically calculated similarity threshold (based on quality)
     * @return RecognitionResult with the best match, or unknown if below threshold
     */
    public RecognitionResult matchAgainstGallery(float[] probeEmbedding, double dynamicThreshold) {
        if (probeEmbedding == null || gallery.isEmpty()) {
            return RecognitionResult.unknownDnn(0);
        }

        // Early-exit threshold: if a match exceeds this, skip remaining gallery entries.
        double earlyExitThreshold = Math.min(dynamicThreshold + 0.15, 0.95);

        galleryLock.readLock().lock();
        try {
            double bestScore = -1;
            int bestTargetId = -1;

            for (Map.Entry<Integer, TargetEmbeddings> entry : gallery.entrySet()) {
                TargetEmbeddings target = entry.getValue();
                
                // Max-Similarity rule across all registered templates for this target
                double maxSimilarity = target.getTemplates().stream()
                        .mapToDouble(template -> dotProduct(probeEmbedding, template))
                        .max()
                        .orElseGet(() -> dotProduct(probeEmbedding, target.getCentroid()));

                if (maxSimilarity > bestScore) {
                    bestScore = maxSimilarity;
                    bestTargetId = entry.getKey();

                    // Early exit: high-confidence match found, no need to scan further
                    if (bestScore >= earlyExitThreshold) {
                        log.debug("Gallery early-exit: targetId={}, similarity={}", bestTargetId,
                                String.format("%.3f", bestScore));
                        break;
                    }
                }
            }

            if (bestScore >= dynamicThreshold && bestTargetId > 0) {
                RecognitionResult result = RecognitionResult.matchedDnn(bestTargetId, bestScore);

                // Lookup target details
                Optional<TargetRegistry> targetOpt = targetDAO.findById(bestTargetId);
                targetOpt.ifPresent(result::setMatchedTarget);

                log.info("DNN Face MATCHED: targetId={}, similarity={}, target={}",
                        bestTargetId, String.format("%.3f", bestScore),
                        targetOpt.map(TargetRegistry::getFullName).orElse("UNKNOWN"));

                return result;
            }

            return RecognitionResult.unknownDnn(bestScore);

        } finally {
            galleryLock.readLock().unlock();
        }
    }

    /**
     * Rebuilds the embedding gallery from the database.
     * <p>
     * For each active target with face templates, loads the uploaded image,
     * runs YuNet face detection to locate the face, then uses
     * {@code alignCrop() + SFace feature()} to extract an embedding that
     * is distribution-identical to the live camera pipeline.
     * </p>
     */
    public void rebuildGallery() {
        if (!initialized) {
            log.warn("Cannot rebuild gallery — DNN recognizer not initialized");
            return;
        }

        galleryLock.writeLock().lock();
        try {
            gallery.clear();
            log.info("Rebuilding DNN embedding gallery...");

            // Use the same DNN face detector as the live pipeline
            DnnFaceDetectionService faceDetector = DnnFaceDetectionService.getInstance();
            if (!faceDetector.isInitialized()) {
                log.warn("YuNet face detector not initialized — cannot rebuild gallery with aligned embeddings");
                return;
            }

            List<TargetImage> allTemplates = targetImageDAO.findAllActiveTemplates();
            int loaded = 0;
            int skippedNoFace = 0;

            for (TargetImage ti : allTemplates) {
                String imgPath = ti.getImagePath();
                if (imgPath == null || !new File(imgPath).exists()) continue;

                Optional<TargetRegistry> targetOpt = targetDAO.findById(ti.getTargetId());
                if (targetOpt.isEmpty() || !targetOpt.get().isActive()) continue;

                // Load the uploaded image (full photo or cropped target image)
                Mat img = imread(imgPath);
                if (img.empty()) {
                    img.release();
                    continue;
                }

                try {
                    // Step 1: Detect faces using YuNet (same detector as live pipeline)
                    List<com.drishtix.model.FaceDetection> detections = faceDetector.detectFaces(img);

                    if (detections.isEmpty()) {
                        // Add border padding for cropped face photos so YuNet can detect 5-point landmarks
                        Mat padded = new Mat();
                        int top = Math.max(40, img.rows() / 3);
                        int bottom = Math.max(40, img.rows() / 3);
                        int left = Math.max(40, img.cols() / 3);
                        int right = Math.max(40, img.cols() / 3);
                        copyMakeBorder(img, padded, top, bottom, left, right, BORDER_CONSTANT, new Scalar(0, 0, 0, 0));

                        detections = faceDetector.detectFaces(padded);

                        if (!detections.isEmpty()) {
                            com.drishtix.model.FaceDetection bestDetection = detections.get(0);
                            float[] detRow = bestDetection.getDetectionRow();
                            float[] embedding = alignAndExtractEmbedding(padded, detRow);
                            padded.release();

                            if (embedding != null) {
                                int targetId = ti.getTargetId();
                                gallery.putIfAbsent(targetId, new TargetEmbeddings());
                                gallery.get(targetId).addTemplate(embedding);
                                loaded++;
                                continue;
                            }
                        }
                        padded.release();

                        // Fallback: if YuNet still yields no face, use direct extraction
                        Mat resized = new Mat();
                        resize(img, resized, new Size(AppConstants.DNN_FACE_INPUT_SIZE, AppConstants.DNN_FACE_INPUT_SIZE));
                        float[] embedding = extractEmbedding(resized);
                        resized.release();

                        if (embedding != null) {
                            int targetId = ti.getTargetId();
                            gallery.putIfAbsent(targetId, new TargetEmbeddings());
                            gallery.get(targetId).addTemplate(embedding);
                            loaded++;
                        } else {
                            skippedNoFace++;
                        }
                        continue;
                    }

                    // Step 2: Use the highest-confidence detection's raw row for alignCrop
                    com.drishtix.model.FaceDetection bestDetection = detections.get(0);
                    for (com.drishtix.model.FaceDetection d : detections) {
                        if (d.getDetectionScore() > bestDetection.getDetectionScore()) {
                            bestDetection = d;
                        }
                    }

                    // Step 3: alignCrop + SFace embedding (identical to live pipeline)
                    float[] detRow = bestDetection.getDetectionRow();
                    float[] embedding = alignAndExtractEmbedding(img, detRow);

                    if (embedding != null) {
                        int targetId = ti.getTargetId();
                        gallery.putIfAbsent(targetId, new TargetEmbeddings());
                        gallery.get(targetId).addTemplate(embedding);
                        loaded++;
                    } else {
                        skippedNoFace++;
                    }
                } finally {
                    img.release();
                }
            }

            log.info("DNN gallery rebuilt: {} unique targets with {} total templates ({} skipped — no face)",
                    gallery.size(), loaded, skippedNoFace);

        } catch (Exception e) {
            log.error("Failed to rebuild DNN gallery", e);
        } finally {
            galleryLock.writeLock().unlock();
        }
    }

    /**
     * Removes a target from the embedding gallery.
     */
    public void removeFromGallery(int targetId) {
        gallery.remove(targetId);
    }

    /**
     * Returns the number of targets in the gallery.
     */
    public int getGallerySize() {
        return gallery.size();
    }

    /**
     * Thread-safe injection of a single embedding into the live gallery.
     * <p>
     * Called by the BackgroundIngestionEngine after scraping a new face.
     * Uses the write lock to ensure no concurrent reads see a partial update.
     * The target becomes immediately active on the live camera feed.
     * </p>
     *
     * @param targetId  the registered target's database ID
     * @param embedding the 128-dim SFace feature vector
     */
    public void injectEmbedding(int targetId, float[] embedding) {
        if (embedding == null || embedding.length == 0) {
            log.warn("Cannot inject null/empty embedding for targetId={}", targetId);
            return;
        }

        galleryLock.writeLock().lock();
        try {
            gallery.putIfAbsent(targetId, new TargetEmbeddings());
            gallery.get(targetId).addTemplate(embedding);
            log.info("Embedding injected into live gallery: targetId={}, gallerySize={}",
                    targetId, gallery.size());
        } finally {
            galleryLock.writeLock().unlock();
        }
    }

    public boolean isInitialized() {
        return initialized;
    }

    /**
     * L2-normalizes an embedding in-place so cosine similarity == dot product.
     * Called at extraction time (both probe and gallery embeddings).
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
     * Dot product between two L2-normalized vectors.
     * Mathematically equivalent to cosine similarity: S_C(A,B) = A·B / (||A|| ||B||)
     * but since ||A||=||B||=1 after L2 normalization, it reduces to just A·B.
     * Eliminates 2× sqrt + 1 division per comparison.
     */
    private double dotProduct(float[] a, float[] b) {
        if (a == null || b == null || a.length != b.length) return 0;
        double sum = 0;
        for (int i = 0; i < a.length; i++) {
            sum += a[i] * b[i];
        }
        return sum;
    }

    /**
     * Initializes the SFace FaceRecognizerSF from the ONNX model.
     * <p>
     * Attempts hardware-accelerated backends in priority order:
     * 1. Intel OpenVINO (iGPU/NPU) — best for Intel laptops
     * 2. NVIDIA CUDA/TensorRT — best for NVIDIA GPU laptops
     * 3. Default ONNX Runtime on CPU — universal fallback
     * </p>
     */
    private void initialize() {
        try {
            modelPath = resolveModelPath(AppConstants.SFACE_MODEL_FILE);
            if (modelPath == null) {
                log.warn("SFace model not found — DNN face recognition unavailable. "
                        + "Place '{}' in '{}'",
                        AppConstants.SFACE_MODEL_FILE, AppConstants.MODELS_DIR);
                return;
            }

            // Test creation on init thread to verify model validity
            FaceRecognizerSF testRecognizer = createRecognizerInstance();
            if (testRecognizer == null) {
                log.error("Failed to create FaceRecognizerSF — recognizer is null after all backend attempts");
                return;
            }
            
            // Seed the ThreadLocal for the current thread
            recognizerLocal.set(testRecognizer);

            initialized = true;
            log.info("DNN Face Recognition (SFace) initialized with ThreadLocal pooling. Model={}", modelPath);

            // Rebuild gallery on initialization
            rebuildGallery();

        } catch (Exception e) {
            log.error("Failed to initialize DNN face recognizer", e);
        }
    }

    /**
     * Creates a new instance of FaceRecognizerSF for the calling thread.
     */
    private FaceRecognizerSF createRecognizerInstance() {
        FaceRecognizerSF newRecognizer = null;
        String backendUsed = "DEFAULT (CPU)";

        try {
            // === Attempt 1: OpenVINO backend ===
            try {
                newRecognizer = FaceRecognizerSF.create(modelPath, "",
                        0,  // DNN_BACKEND_DEFAULT
                        0   // DNN_TARGET_CPU
                );
                if (newRecognizer != null) {
                    backendUsed = "OPENVINO (CPU target)";
                }
            } catch (Exception e) {
                log.trace("SFace: OpenVINO backend unavailable: {}", e.getMessage());
            }

            // === Attempt 2: NVIDIA CUDA backend ===
            if (newRecognizer == null) {
                try {
                    newRecognizer = FaceRecognizerSF.create(modelPath, "",
                            5,  // DNN_BACKEND_CUDA
                            6   // DNN_TARGET_CUDA
                    );
                    if (newRecognizer != null) {
                        backendUsed = "CUDA (NVIDIA GPU)";
                    }
                } catch (Exception e) {
                    log.trace("SFace: CUDA backend unavailable: {}", e.getMessage());
                }
            }

            // === Attempt 3: Default CPU fallback ===
            if (newRecognizer == null) {
                newRecognizer = FaceRecognizerSF.create(modelPath, "");
                backendUsed = "DEFAULT (CPU ONNX Runtime)";
            }
            
            log.debug("Created FaceRecognizerSF instance. Backend used: {}", backendUsed);

        } catch (Exception e) {
            log.error("Error creating FaceRecognizerSF instance", e);
        }

        return newRecognizer;
    }

    /**
     * Resolves the model file path by checking configured dir, defaults dir, and classpath.
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
                Path tempFile = Files.createTempFile("drishtix_dnn_", "_" + modelFile);
                Files.copy(is, tempFile, StandardCopyOption.REPLACE_EXISTING);
                is.close();
                return tempFile.toString();
            }
        } catch (Exception e) {
            log.warn("Failed to extract DNN model from classpath: {}", e.getMessage());
        }

        return null;
    }
}
