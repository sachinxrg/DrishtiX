package com.drishtix.service;

import com.drishtix.dao.DetectionLogDAO;
import com.drishtix.model.DetectionLog;
import com.drishtix.model.TargetCategory;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.time.LocalDate;
import java.util.List;

/**
 * Service layer for detection log operations.
 * Provides querying, filtering, and count methods for the dashboard and log views.
 */
public class DetectionLogService {

    private static final Logger log = LoggerFactory.getLogger(DetectionLogService.class);
    private static volatile DetectionLogService instance;

    private final DetectionLogDAO detectionLogDAO;

    private DetectionLogService() {
        this.detectionLogDAO = new DetectionLogDAO();
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
}
