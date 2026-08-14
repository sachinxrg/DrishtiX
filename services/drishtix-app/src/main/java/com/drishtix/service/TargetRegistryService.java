package com.drishtix.service;

import com.drishtix.dao.AuditLogDAO;
import com.drishtix.dao.DetectionLogDAO;
import com.drishtix.dao.TargetDAO;
import com.drishtix.dao.TargetImageDAO;
import com.drishtix.exception.FaceNotFoundException;
import com.drishtix.model.*;
import com.drishtix.util.AppConstants;
import com.drishtix.util.ThreadPools;
import org.bytedeco.opencv.opencv_core.Mat;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.io.File;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardCopyOption;
import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;
import java.util.List;
import java.util.Optional;
import java.util.concurrent.CompletableFuture;

/**
 * Service orchestrating target registration workflow:
 * 1. Validate and save the uploaded photo
 * 2. Extract face template via FaceProcessingService
 * 3. Save metadata to database via TargetDAO
 * 4. Trigger LBPH model retraining via RecognitionService
 * 5. Log the action via AuditLogDAO
 */
public class TargetRegistryService {

    private static final Logger log = LoggerFactory.getLogger(TargetRegistryService.class);
    private static volatile TargetRegistryService instance;

    private final TargetDAO targetDAO;
    private final TargetImageDAO targetImageDAO;
    private final AuditLogDAO auditLogDAO;
    private final FaceProcessingService faceService;
    private final RecognitionService recognitionService;

    private TargetRegistryService() {
        this.targetDAO = new TargetDAO();
        this.targetImageDAO = new TargetImageDAO();
        this.auditLogDAO = new AuditLogDAO();
        this.faceService = FaceProcessingService.getInstance();
        this.recognitionService = RecognitionService.getInstance();
        ensureDirectories();
    }

    public static TargetRegistryService getInstance() {
        if (instance == null) {
            synchronized (TargetRegistryService.class) {
                if (instance == null) {
                    instance = new TargetRegistryService();
                }
            }
        }
        return instance;
    }

    /**
     * Registers a new target with the provided photo and metadata.
     * <p>
     * Full workflow:
     * 1. Copy uploaded photo to data/uploads/
     * 2. Detect and extract face → save template to data/templates/
     * 3. Insert target_registry record
     * 4. Insert target_images record
     * 5. Retrain LBPH model asynchronously
     * 6. Log audit entry
     * </p>
     *
     * @param sourceImagePath the path to the uploaded photo file
     * @param fullName        the target's full name
     * @param category        CRIMINAL or MISSING_PERSON
     * @param caseNumber      the case/FIR number
     * @param description     optional description
     * @return the created TargetRegistry entity
     * @throws FaceNotFoundException if no face is detected in the image
     */
    public TargetRegistry registerTarget(String sourceImagePath, String fullName,
                                         TargetCategory category, String caseNumber,
                                         String description) {

        // Validate file exists and size
        File sourceFile = new File(sourceImagePath);
        if (!sourceFile.exists()) {
            throw new FaceNotFoundException("Image file not found: " + sourceImagePath);
        }
        if (sourceFile.length() > AppConstants.MAX_IMAGE_SIZE_BYTES) {
            throw new IllegalArgumentException("Image exceeds maximum size of 10MB");
        }

        // Generate unique filenames
        String timestamp = LocalDateTime.now().format(DateTimeFormatter.ofPattern("yyyyMMdd_HHmmss"));
        String ext = getFileExtension(sourceImagePath);
        String baseName = caseNumber.replaceAll("[^a-zA-Z0-9-]", "_");

        String uploadFileName = baseName + "_" + timestamp + "." + ext;
        String templateFileName = baseName + "_" + timestamp + "_template.png";

        String uploadPath = AppConstants.UPLOADS_DIR + "/" + uploadFileName;
        String templatePath = AppConstants.TEMPLATES_DIR + "/" + templateFileName;

        // Step 1: Copy uploaded image to uploads directory
        try {
            Files.copy(sourceFile.toPath(), Path.of(uploadPath), StandardCopyOption.REPLACE_EXISTING);
            log.info("Uploaded image saved: {}", uploadPath);
        } catch (IOException e) {
            throw new RuntimeException("Failed to save uploaded image", e);
        }

        // Step 2: Detect and extract face template
        Mat faceTemplate = faceService.detectAndExtractFace(uploadPath);
        faceService.saveTemplate(faceTemplate, templatePath);
        faceTemplate.release();

        // Step 3: Get next recognizer label and insert target
        int recognizerLabel = targetDAO.getNextRecognizerLabel();

        TargetRegistry target = new TargetRegistry(fullName, category, caseNumber,
                description, uploadPath, recognizerLabel);
        int targetId = targetDAO.insert(target);

        // Step 4: Insert target image record
        TargetImage image = new TargetImage(targetId, uploadPath, templatePath, 1);
        targetImageDAO.insert(image);

        // Step 5: Retrain LBPH model + rebuild DNN gallery asynchronously
        CompletableFuture.runAsync(() -> {
            try {
                recognitionService.trainModel();
                log.info("LBPH model retrained after registering: {}", fullName);
            } catch (Exception e) {
                log.error("Failed to retrain model after registration", e);
            }
        }, ThreadPools.getVideoInferencePool());

        // Step 5b: Rebuild DNN gallery so the new target is immediately detectable
        CompletableFuture.runAsync(() -> {
            try {
                recognitionService.rebuildDnnGallery();
                log.info("DNN gallery rebuilt after registering: {}", fullName);
            } catch (Exception e) {
                log.error("Failed to rebuild DNN gallery after registration", e);
            }
        }, ThreadPools.getVideoInferencePool());

        // Step 6: Audit log
        auditLogDAO.insert(AuditLogEntry.targetAction(
                AppConstants.AUDIT_TARGET_ADDED, targetId,
                String.format("{\"name\":\"%s\",\"category\":\"%s\",\"case\":\"%s\"}",
                        fullName, category, caseNumber)));

        log.info("Target registered successfully: id={}, name={}, category={}, case={}",
                targetId, fullName, category, caseNumber);

        return target;
    }

    /**
     * Deactivates a target and retrains the model.
     * Also removes the target from the DNN gallery to prevent ghost detections.
     */
    public void deactivateTarget(int targetId) {
        targetDAO.deactivate(targetId);

        // Remove from DNN gallery immediately (Bug #3 fix: removeFromGallery was never called)
        DnnFaceRecognitionService.getInstance().removeFromGallery(targetId);
        log.info("Target removed from DNN gallery: targetId={}", targetId);

        // Retrain LBPH model without the deactivated target
        CompletableFuture.runAsync(() -> {
            recognitionService.trainModel();
            log.info("LBPH model retrained after deactivating target: {}", targetId);
        }, ThreadPools.getVideoInferencePool());

        auditLogDAO.insert(AuditLogEntry.targetAction(
                AppConstants.AUDIT_TARGET_DEACTIVATED, targetId, "Target deactivated"));
    }

    /**
     * Permanently deletes a target and all associated data.
     * <p>
     * Cascading delete workflow:
     * 1. Verify target exists
     * 2. Delete physical image/template files
     * 3. Delete physical snapshot files from detection logs
     * 4. Delete detection_logs documents for this target
     * 5. Delete target_images documents for this target
     * 6. Delete the target document itself
     * 7. Retrain LBPH model
     * 8. Record audit log
     * </p>
     *
     * @param targetId the ID of the target to delete
     * @throws IllegalArgumentException if the target is not found
     */
    public void deleteTarget(int targetId) {
        // Step 1: Verify target exists
        Optional<TargetRegistry> targetOpt = targetDAO.findById(targetId);
        if (targetOpt.isEmpty()) {
            throw new IllegalArgumentException("Target not found: " + targetId);
        }
        TargetRegistry target = targetOpt.get();
        String targetName = target.getFullName();

        log.info("Starting cascading delete for target: id={}, name={}", targetId, targetName);

        // Step 2: Delete physical image and template files
        List<TargetImage> images = targetImageDAO.findByTargetId(targetId);
        for (TargetImage img : images) {
            deleteFileQuietly(img.getImagePath());
            deleteFileQuietly(img.getTemplatePath());
        }

        // Step 3: Delete physical snapshot files from detection logs
        DetectionLogDAO detectionLogDAO = new DetectionLogDAO();
        List<DetectionLog> logs = detectionLogDAO.findByTargetId(targetId);
        for (DetectionLog dl : logs) {
            deleteFileQuietly(dl.getSnapshotPath());
        }

        // Step 4: Delete detection_logs documents
        int logsDeleted = detectionLogDAO.deleteByTargetId(targetId);
        log.info("Deleted {} detection logs for target: {}", logsDeleted, targetId);

        // Step 5: Delete target_images documents
        targetImageDAO.deleteByTargetId(targetId);

        // Step 6: Delete the target document
        targetDAO.delete(targetId);

        // Also delete the profile image file
        deleteFileQuietly(target.getProfileImagePath());

        // Step 7: Remove from DNN gallery immediately (Bug #3 fix)
        DnnFaceRecognitionService.getInstance().removeFromGallery(targetId);
        log.info("Target removed from DNN gallery: targetId={}", targetId);

        // Step 8: Retrain LBPH model asynchronously
        CompletableFuture.runAsync(() -> {
            try {
                recognitionService.trainModel();
                log.info("LBPH model retrained after deleting target: {}", targetId);
            } catch (Exception e) {
                log.error("Failed to retrain model after target deletion", e);
            }
        }, ThreadPools.getVideoInferencePool());

        // Step 9: Audit log
        auditLogDAO.insert(AuditLogEntry.targetAction(
                AppConstants.AUDIT_TARGET_DELETED, targetId,
                String.format("{\"name\":\"%s\",\"category\":\"%s\",\"case\":\"%s\"}",
                        targetName, target.getCategory(), target.getCaseNumber())));

        log.info("Target permanently deleted: id={}, name={}", targetId, targetName);
    }

    /**
     * Quietly deletes a file without throwing exceptions.
     */
    private void deleteFileQuietly(String path) {
        if (path == null || path.isBlank()) return;
        try {
            File file = new File(path);
            if (file.exists() && file.delete()) {
                log.debug("Deleted file: {}", path);
            }
        } catch (Exception e) {
            log.warn("Failed to delete file: {}", path, e);
        }
    }

    /**
     * Returns all active targets.
     */
    public List<TargetRegistry> getActiveTargets() {
        return targetDAO.findAllActive();
    }

    /**
     * Returns all targets (including deactivated).
     */
    public List<TargetRegistry> getAllTargets() {
        return targetDAO.findAll();
    }

    /**
     * Searches targets by query and optional category filter.
     */
    public List<TargetRegistry> searchTargets(String query, TargetCategory categoryFilter) {
        return targetDAO.search(query, categoryFilter);
    }

    /**
     * Returns a target by ID.
     */
    public Optional<TargetRegistry> getTargetById(int targetId) {
        return targetDAO.findById(targetId);
    }

    /**
     * Returns active target counts for the dashboard.
     */
    public int getActiveTargetCount() {
        return targetDAO.countActive();
    }

    public int getCriminalCount() {
        return targetDAO.countByCategory(TargetCategory.CRIMINAL);
    }

    public int getMissingPersonCount() {
        return targetDAO.countByCategory(TargetCategory.MISSING_PERSON);
    }

    /**
     * Initializes the recognizer model on startup.
     */
    public void initializeRecognizer() {
        CompletableFuture.runAsync(() -> {
            try {
                recognitionService.trainModel();
                log.info("Initial LBPH model training complete");
            } catch (Exception e) {
                log.warn("Initial model training failed (may be no targets registered yet)", e);
            }
        }, ThreadPools.getVideoInferencePool());
    }

    private void ensureDirectories() {
        new File(AppConstants.UPLOADS_DIR).mkdirs();
        new File(AppConstants.TEMPLATES_DIR).mkdirs();
        new File(AppConstants.SNAPSHOTS_DIR).mkdirs();
    }

    private String getFileExtension(String path) {
        int dotIndex = path.lastIndexOf('.');
        return (dotIndex >= 0) ? path.substring(dotIndex + 1).toLowerCase() : "png";
    }
}
