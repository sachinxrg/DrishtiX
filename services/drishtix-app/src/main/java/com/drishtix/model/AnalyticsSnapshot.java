package com.drishtix.model;

import java.util.Collections;
import java.util.List;
import java.util.Map;

/**
 * Immutable container holding a complete analytics snapshot for the dashboard.
 * Aggregates all analytics data produced by a single query to
 * {@code DetectionAnalyticsService.generateSnapshot()}.
 *
 * <p>All collections returned by getters are unmodifiable.</p>
 */
public class AnalyticsSnapshot {

    // ==================== Distributions ====================
    private final List<HourlyDetectionCount> hourlyDistribution;
    private final List<DailyDetectionCount> dailyTrend;
    private final List<TargetDetectionSummary> topTargets;

    // ==================== Breakdowns ====================
    /** Category → count (e.g., CRIMINAL → 42, MISSING_PERSON → 17). */
    private final Map<TargetCategory, Long> categoryBreakdown;

    /** Confidence bucket label → count (e.g., "90-100%" → 35). */
    private final Map<String, Long> confidenceDistribution;

    // ==================== Summary Scalars ====================
    private final long totalDetections;
    private final int uniqueTargetsDetected;
    private final double avgConfidence;
    private final int peakHour;

    /**
     * Constructs a fully populated AnalyticsSnapshot.
     *
     * @param hourlyDistribution     detection counts by hour (0–23)
     * @param dailyTrend             detection counts by day
     * @param topTargets             most frequently detected targets
     * @param categoryBreakdown      detection counts per category
     * @param confidenceDistribution detection counts per confidence bucket
     * @param totalDetections        total detection events in the range
     * @param uniqueTargetsDetected  count of distinct targets detected
     * @param avgConfidence          mean confidence score across all detections
     * @param peakHour               hour of day with the highest detection count
     */
    public AnalyticsSnapshot(List<HourlyDetectionCount> hourlyDistribution,
                             List<DailyDetectionCount> dailyTrend,
                             List<TargetDetectionSummary> topTargets,
                             Map<TargetCategory, Long> categoryBreakdown,
                             Map<String, Long> confidenceDistribution,
                             long totalDetections,
                             int uniqueTargetsDetected,
                             double avgConfidence,
                             int peakHour) {
        this.hourlyDistribution = hourlyDistribution != null
                ? Collections.unmodifiableList(hourlyDistribution)
                : Collections.emptyList();
        this.dailyTrend = dailyTrend != null
                ? Collections.unmodifiableList(dailyTrend)
                : Collections.emptyList();
        this.topTargets = topTargets != null
                ? Collections.unmodifiableList(topTargets)
                : Collections.emptyList();
        this.categoryBreakdown = categoryBreakdown != null
                ? Collections.unmodifiableMap(categoryBreakdown)
                : Collections.emptyMap();
        this.confidenceDistribution = confidenceDistribution != null
                ? Collections.unmodifiableMap(confidenceDistribution)
                : Collections.emptyMap();
        this.totalDetections = totalDetections;
        this.uniqueTargetsDetected = uniqueTargetsDetected;
        this.avgConfidence = avgConfidence;
        this.peakHour = peakHour;
    }

    // ==================== Getters ====================

    public List<HourlyDetectionCount> getHourlyDistribution() {
        return hourlyDistribution;
    }

    public List<DailyDetectionCount> getDailyTrend() {
        return dailyTrend;
    }

    public List<TargetDetectionSummary> getTopTargets() {
        return topTargets;
    }

    public Map<TargetCategory, Long> getCategoryBreakdown() {
        return categoryBreakdown;
    }

    public Map<String, Long> getConfidenceDistribution() {
        return confidenceDistribution;
    }

    public long getTotalDetections() {
        return totalDetections;
    }

    public int getUniqueTargetsDetected() {
        return uniqueTargetsDetected;
    }

    public double getAvgConfidence() {
        return avgConfidence;
    }

    /**
     * Returns the average confidence as a formatted percentage string.
     */
    public String getAvgConfidenceDisplay() {
        double pct = avgConfidence;
        if (pct <= 1.0) pct = pct * 100.0;
        return String.format("%.1f%%", pct);
    }

    public int getPeakHour() {
        return peakHour;
    }

    /**
     * Returns the peak hour as a formatted label (e.g., "14:00").
     */
    public String getPeakHourDisplay() {
        return String.format("%02d:00", peakHour);
    }

    @Override
    public String toString() {
        return "AnalyticsSnapshot{total=" + totalDetections +
                ", uniqueTargets=" + uniqueTargetsDetected +
                ", avgConf=" + String.format("%.3f", avgConfidence) +
                ", peakHour=" + peakHour +
                ", hourlyBars=" + hourlyDistribution.size() +
                ", dailyPoints=" + dailyTrend.size() +
                ", topTargets=" + topTargets.size() + '}';
    }
}
