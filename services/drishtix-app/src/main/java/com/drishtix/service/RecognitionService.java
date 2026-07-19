package com.drishtix.service;

import com.drishtix.dao.TargetDAO;
import com.drishtix.dao.TargetImageDAO;
import com.drishtix.exception.RecognitionException;
import com.drishtix.model.RecognitionResult;
import com.drishtix.model.TargetImage;
import com.drishtix.model.TargetRegistry;

import org.bytedeco.opencv.opencv_core.*;
import org.bytedeco.opencv.opencv_face.LBPHFaceRecognizer;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.io.File;
import java.util.List;
import java.util.Optional;
import java.util.concurrent.locks.ReentrantReadWriteLock;

import static org.bytedeco.opencv.global.opencv_imgcodecs.*;

/**
 * Service managing the LBPH Face Recognizer for face identification.
 * <p>
 * Handles training the model with registered face templates and
 * performing predictions against live or scanned face ROIs.
 * </p>
 * <p>
 * Thread safety: Uses a ReadWriteLock to allow concurrent predictions
 * while serializing model retraining operations.
 * </p>
 */
public class RecognitionService {

    private static final Logger log = LoggerFactory.getLogger(RecognitionService.class);
    private static volatile RecognitionService instance;

    private LBPHFaceRecognizer recognizer;
    private final TargetImageDAO targetImageDAO;
    private final TargetDAO targetDAO;
    private final ReentrantReadWriteLock modelLock;
    private volatile boolean trained;

    private RecognitionService() {
        this.recognizer = LBPHFaceRecognizer.create(1, 8, 8, 8, 200.0);
        this.targetImageDAO = new TargetImageDAO();
        this.targetDAO = new TargetDAO();
        this.modelLock = new ReentrantReadWriteLock();
        this.trained = false;
    }

    public static RecognitionService getInstance() {
        if (instance == null) {
            synchronized (RecognitionService.class) {
                if (instance == null) {
                    instance = new RecognitionService();
                }
            }
        }
        return instance;
    }

    /**
     * Trains (or retrains) the LBPH recognizer with all active target face templates.
     * <p>
     * Acquires a write lock during training to prevent concurrent predictions
     * from using an incomplete model.
     * </p>
     */
    public void trainModel() {
        modelLock.writeLock().lock();
        try {
            log.info("Starting LBPH model training...");

            List<TargetImage> templates = targetImageDAO.findAllActiveTemplates();

            if (templates.isEmpty()) {
                log.warn("No active face templates found — recognizer not trained");
                trained = false;
                return;
            }

            MatVector images = new MatVector();
            Mat labels = new Mat(templates.size(), 1, org.bytedeco.opencv.global.opencv_core.CV_32SC1);

            int loadedCount = 0;
            for (int i = 0; i < templates.size(); i++) {
                TargetImage ti = templates.get(i);
                String templatePath = ti.getTemplatePath();

                if (templatePath == null || !new File(templatePath).exists()) {
                    log.warn("Template file missing for image_id={}: {}", ti.getImageId(), templatePath);
                    continue;
                }

                Mat templateMat = imread(templatePath, IMREAD_GRAYSCALE);
                if (templateMat.empty()) {
                    log.warn("Failed to load template: {}", templatePath);
                    templateMat.release();
                    continue;
                }

                // Lookup the recognizer_label from the parent target
                Optional<TargetRegistry> targetOpt = targetDAO.findById(ti.getTargetId());
                if (targetOpt.isEmpty()) {
                    log.warn("Target not found for image_id={}", ti.getImageId());
                    templateMat.release();
                    continue;
                }

                images.push_back(templateMat);
                labels.ptr(loadedCount).putInt(targetOpt.get().getRecognizerLabel());
                loadedCount++;
            }

            if (loadedCount == 0) {
                log.warn("No valid templates could be loaded — recognizer not trained");
                trained = false;
                images.close();
                labels.release();
                return;
            }

            // Trim the labels Mat to the actual loaded count
            Mat trimmedLabels = new Mat(loadedCount, 1, org.bytedeco.opencv.global.opencv_core.CV_32SC1);
            for (int i = 0; i < loadedCount; i++) {
                trimmedLabels.ptr(i).putInt(labels.ptr(i).getInt());
            }

            // Recreate recognizer to clear previous model
            recognizer = LBPHFaceRecognizer.create(1, 8, 8, 8, 200.0);
            recognizer.train(images, trimmedLabels);
            trained = true;

            log.info("LBPH model trained successfully with {} templates from {} targets",
                    loadedCount, templates.stream().map(TargetImage::getTargetId).distinct().count());

            // Cleanup
            labels.release();
            trimmedLabels.release();
            for (long i = 0; i < images.size(); i++) {
                images.get(i).release();
            }
            images.close();

        } catch (Exception e) {
            trained = false;
            throw new RecognitionException("Failed to train LBPH model", e);
        } finally {
            modelLock.writeLock().unlock();
        }
    }

    /**
     * Predicts the identity of a face ROI against the trained model.
     *
     * @param faceROI the preprocessed grayscale face image (200x200)
     * @return a RecognitionResult with the predicted label and confidence
     */
    public RecognitionResult predict(Mat faceROI) {
        if (!trained) {
            return RecognitionResult.unknown(999.0);
        }

        modelLock.readLock().lock();
        try {
            int[] label = new int[1];
            double[] confidence = new double[1];

            recognizer.predict(faceROI, label, confidence);

            double threshold = ConfigurationService.getInstance().getConfidenceThreshold();

            if (confidence[0] < threshold) {
                RecognitionResult result = RecognitionResult.matched(label[0], confidence[0]);

                // Lookup target details
                Optional<TargetRegistry> targetOpt = targetDAO.findByRecognizerLabel(label[0]);
                targetOpt.ifPresent(result::setMatchedTarget);

                log.info("Face MATCHED: label={}, confidence={}, target={}",
                        label[0], String.format("%.2f", confidence[0]),
                        targetOpt.map(TargetRegistry::getFullName).orElse("UNKNOWN"));

                return result;
            } else {
                return RecognitionResult.unknown(confidence[0]);
            }

        } catch (Exception e) {
            log.error("Face prediction failed", e);
            return RecognitionResult.unknown(999.0);
        } finally {
            modelLock.readLock().unlock();
        }
    }

    /**
     * Returns true if the recognizer has been trained with at least one template.
     */
    public boolean isTrained() {
        return trained;
    }
}
