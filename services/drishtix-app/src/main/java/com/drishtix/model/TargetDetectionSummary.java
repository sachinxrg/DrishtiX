package com.drishtix.model;

import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;
import java.util.Objects;

/**
 * Value object representing aggregated detection statistics for a single target.
 * Used by the Analytics Dashboard to render the "Top-N Most Detected Targets" table.
 *
 * <p>Each instance summarizes one target's detection history within a queried date range:
 * how many times they were detected, when they were last seen, and their average
 * match confidence.</p>
 */
public class TargetDetectionSummary {

    private static final DateTimeFormatter DISPLAY_FORMAT =
            DateTimeFormatter.ofPattern("dd/MM/yyyy HH:mm");

    private final int targetId;
    private final String targetName;
    private final TargetCategory category;
    private final long totalDetections;
    private final LocalDateTime lastSeen;
    private final double avgConfidence;

    /**
     * Constructs a TargetDetectionSummary.
     *
     * @param targetId        the target's database ID
     * @param targetName      the target's full name
     * @param category        CRIMINAL or MISSING_PERSON
     * @param totalDetections total number of times this target was detected
     * @param lastSeen        timestamp of the most recent detection (may be null)
     * @param avgConfidence   average cosine similarity score across all detections
     */
    public TargetDetectionSummary(int targetId, String targetName, TargetCategory category,
                                  long totalDetections, LocalDateTime lastSeen,
                                  double avgConfidence) {
        this.targetId = targetId;
        this.targetName = targetName;
        this.category = category;
        this.totalDetections = totalDetections;
        this.lastSeen = lastSeen;
        this.avgConfidence = avgConfidence;
    }

    public int getTargetId() {
        return targetId;
    }

    public String getTargetName() {
        return targetName;
    }

    public TargetCategory getCategory() {
        return category;
    }

    public long getTotalDetections() {
        return totalDetections;
    }

    public LocalDateTime getLastSeen() {
        return lastSeen;
    }

    public double getAvgConfidence() {
        return avgConfidence;
    }

    /**
     * Returns a formatted "last seen" string for display (e.g., "22/08/2026 14:30").
     */
    public String getLastSeenDisplay() {
        if (lastSeen == null) return "Never";
        return lastSeen.format(DISPLAY_FORMAT);
    }

    /**
     * Returns the average confidence as a formatted percentage string.
     */
    public String getAvgConfidenceDisplay() {
        double pct = avgConfidence;
        if (pct <= 1.0) pct = pct * 100.0;
        return String.format("%.1f%%", pct);
    }

    @Override
    public boolean equals(Object o) {
        if (this == o) return true;
        if (o == null || getClass() != o.getClass()) return false;
        TargetDetectionSummary that = (TargetDetectionSummary) o;
        return targetId == that.targetId && totalDetections == that.totalDetections;
    }

    @Override
    public int hashCode() {
        return Objects.hash(targetId, totalDetections);
    }

    @Override
    public String toString() {
        return "TargetDetectionSummary{targetId=" + targetId +
                ", name='" + targetName + '\'' +
                ", category=" + category +
                ", detections=" + totalDetections +
                ", avgConf=" + String.format("%.3f", avgConfidence) + '}';
    }
}
