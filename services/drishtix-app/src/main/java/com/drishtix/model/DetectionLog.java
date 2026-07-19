package com.drishtix.model;

import java.time.LocalDateTime;

/**
 * Entity representing a detection event in the system log.
 * Maps to the {@code detection_logs} table in the database.
 * Created each time a recognized target is spotted on camera or in a scanned image.
 */
public class DetectionLog {

    private long logId;
    private int targetId;
    private LocalDateTime detectionTimestamp;
    private double matchConfidenceScore;
    private String snapshotPath;
    private Integer cameraId;
    private String locationTag;
    private LocalDateTime createdAt;

    // Transient fields for display (populated via JOINs)
    private String targetName;
    private TargetCategory targetCategory;
    private String caseNumber;
    private String cameraName;

    public DetectionLog() {
    }

    /**
     * Constructor for creating a new detection log entry.
     */
    public DetectionLog(int targetId, double matchConfidenceScore, String snapshotPath,
                        Integer cameraId, String locationTag) {
        this.targetId = targetId;
        this.matchConfidenceScore = matchConfidenceScore;
        this.snapshotPath = snapshotPath;
        this.cameraId = cameraId;
        this.locationTag = locationTag;
        this.detectionTimestamp = LocalDateTime.now();
    }

    // ==================== Getters & Setters ====================

    public long getLogId() {
        return logId;
    }

    public void setLogId(long logId) {
        this.logId = logId;
    }

    public int getTargetId() {
        return targetId;
    }

    public void setTargetId(int targetId) {
        this.targetId = targetId;
    }

    public LocalDateTime getDetectionTimestamp() {
        return detectionTimestamp;
    }

    public void setDetectionTimestamp(LocalDateTime detectionTimestamp) {
        this.detectionTimestamp = detectionTimestamp;
    }

    public double getMatchConfidenceScore() {
        return matchConfidenceScore;
    }

    public void setMatchConfidenceScore(double matchConfidenceScore) {
        this.matchConfidenceScore = matchConfidenceScore;
    }

    public String getSnapshotPath() {
        return snapshotPath;
    }

    public void setSnapshotPath(String snapshotPath) {
        this.snapshotPath = snapshotPath;
    }

    public Integer getCameraId() {
        return cameraId;
    }

    public void setCameraId(Integer cameraId) {
        this.cameraId = cameraId;
    }

    public String getLocationTag() {
        return locationTag;
    }

    public void setLocationTag(String locationTag) {
        this.locationTag = locationTag;
    }

    public LocalDateTime getCreatedAt() {
        return createdAt;
    }

    public void setCreatedAt(LocalDateTime createdAt) {
        this.createdAt = createdAt;
    }

    public String getTargetName() {
        return targetName;
    }

    public void setTargetName(String targetName) {
        this.targetName = targetName;
    }

    public TargetCategory getTargetCategory() {
        return targetCategory;
    }

    public void setTargetCategory(TargetCategory targetCategory) {
        this.targetCategory = targetCategory;
    }

    public String getCaseNumber() {
        return caseNumber;
    }

    public void setCaseNumber(String caseNumber) {
        this.caseNumber = caseNumber;
    }

    public String getCameraName() {
        return cameraName;
    }

    public void setCameraName(String cameraName) {
        this.cameraName = cameraName;
    }

    /**
     * Returns a human-readable confidence percentage (inverted from LBPH distance).
     * Lower LBPH distance = higher confidence.
     */
    public String getConfidenceDisplay() {
        double confidence = Math.max(0, 100 - (matchConfidenceScore * 0.5));
        return String.format("%.1f%%", confidence);
    }

    @Override
    public String toString() {
        return "DetectionLog{logId=" + logId + ", targetId=" + targetId +
                ", confidence=" + matchConfidenceScore + ", time=" + detectionTimestamp + '}';
    }
}
