package com.drishtix.service;

import com.drishtix.dao.AuditLogDAO;
import com.drishtix.dao.DetectionLogDAO;
import com.drishtix.model.AuditLogEntry;
import com.drishtix.model.DetectionLog;
import com.drishtix.model.TargetCategory;
import com.drishtix.util.AppConstants;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.io.File;
import java.time.LocalDate;
import java.util.List;
import java.util.Optional;

/**
 * Service layer for detection log operations.
 * Provides querying, filtering, deletion, and count methods for the dashboard and log views.
 */
public class DetectionLogService {

    private static final Logger log = LoggerFactory.getLogger(DetectionLogService.class);
    private static volatile DetectionLogService instance;

    private final DetectionLogDAO detectionLogDAO;
    private final AuditLogDAO auditLogDAO;

    private DetectionLogService() {
        this.detectionLogDAO = new DetectionLogDAO();
        this.auditLogDAO = new AuditLogDAO();
    }

    public static DetectionLogService getInstance() {
        if (instance == null) {
            synchronized (DetectionLogService.class) {
                if (instance == null) {
                    instance = new DetectionLogService();
                }
            }
        }
        return instance;
    }

    /**
     * Logs a detection event.
     */
    public long logDetection(DetectionLog detection) {
        return detectionLogDAO.insert(detection);
    }

    /**
     * Returns the most recent detections for the dashboard feed.
     */
    public List<DetectionLog> getRecentDetections(int limit) {
        return detectionLogDAO.findRecent(limit);
    }

    /**
     * Returns detections for a specific target.
     */
    public List<DetectionLog> getDetectionsByTarget(int targetId) {
        return detectionLogDAO.findByTargetId(targetId);
    }

    /**
     * Returns detections within a date range with optional category filter.
     */
    public List<DetectionLog> getDetectionsByDateRange(LocalDate from, LocalDate to,
                                                       TargetCategory categoryFilter) {
        return detectionLogDAO.findByDateRange(from, to, categoryFilter);
    }

    /**
     * Returns today's detection count.
     */
    public int getTodayCount() {
        return detectionLogDAO.countToday();
    }

    /**
     * Returns the total detection count.
     */
    public int getTotalCount() {
        return detectionLogDAO.countAll();
    }

    /**
     * Purges old detection logs based on retention policy.
     */
    public int purgeOldLogs(int retentionDays) {
        int deleted = detectionLogDAO.deleteOlderThan(retentionDays);
        log.info("Purged {} detection logs older than {} days", deleted, retentionDays);
        return deleted;
    }

    /**
     * Deletes a single detection log entry by its ID.
     * Also removes the associated snapshot file from disk and records an audit entry.
     *
     * @param logId the ID of the detection log entry to delete
     * @throws IllegalArgumentException if the log entry is not found
     */
    public void deleteLog(long logId) {
        // Find the log entry to get snapshot path and target info for audit
        Optional<DetectionLog> logOpt = detectionLogDAO.findById(logId);
        if (logOpt.isEmpty()) {
            throw new IllegalArgumentException("Detection log not found: " + logId);
        }
        DetectionLog entry = logOpt.get();

        // Delete associated snapshot file
        if (entry.getSnapshotPath() != null && !entry.getSnapshotPath().isBlank()) {
            try {
                File snapFile = new File(entry.getSnapshotPath());
                if (snapFile.exists() && snapFile.delete()) {
                    log.debug("Deleted snapshot file: {}", entry.getSnapshotPath());
                }
            } catch (Exception e) {
                log.warn("Failed to delete snapshot file: {}", entry.getSnapshotPath(), e);
            }
        }

        // Delete the document from MongoDB
        detectionLogDAO.deleteById(logId);

        // Audit log
        auditLogDAO.insert(AuditLogEntry.targetAction(
                AppConstants.AUDIT_DETECTION_LOG_DELETED, entry.getTargetId(),
                String.format("{\"logId\":%d,\"targetName\":\"%s\",\"timestamp\":\"%s\"}",
                        logId,
                        entry.getTargetName() != null ? entry.getTargetName() : "unknown",
                        entry.getDetectionTimestamp())));

        log.info("Detection log deleted: logId={}, targetId={}", logId, entry.getTargetId());
    }
}
