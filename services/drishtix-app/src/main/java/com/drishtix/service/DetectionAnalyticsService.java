package com.drishtix.service;

import com.drishtix.dao.DetectionLogDAO;
import com.drishtix.model.*;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.time.LocalDate;
import java.time.temporal.ChronoUnit;
import java.util.List;
import java.util.Map;

/**
 * Service layer for aggregating and generating analytics intelligence from historical detection logs.
 * Orchestrates DAO aggregation pipelines into cohesive {@link AnalyticsSnapshot} data objects.
 */
public class DetectionAnalyticsService {

    private static final Logger log = LoggerFactory.getLogger(DetectionAnalyticsService.class);
    private static volatile DetectionAnalyticsService instance;

    private final DetectionLogDAO detectionLogDAO;

    private DetectionAnalyticsService() {
        this.detectionLogDAO = new DetectionLogDAO();
    }

    public static DetectionAnalyticsService getInstance() {
        if (instance == null) {
            synchronized (DetectionAnalyticsService.class) {
                if (instance == null) {
                    instance = new DetectionAnalyticsService();
                }
            }
        }
        return instance;
    }

    /**
     * Generates a complete analytics snapshot for the specified date range.
     *
     * @param from start date of the analytics window (inclusive)
     * @param to   end date of the analytics window (inclusive)
     * @return populated {@link AnalyticsSnapshot}
     */
    public AnalyticsSnapshot generateSnapshot(LocalDate from, LocalDate to) {
        if (from == null) from = LocalDate.now().minusDays(7);
        if (to == null) to = LocalDate.now();
        if (from.isAfter(to)) {
            LocalDate temp = from;
            from = to;
            to = temp;
        }

        log.info("Generating analytics snapshot from {} to {}", from, to);

        // 1. Hourly Distribution (24 bars)
        List<HourlyDetectionCount> hourlyDistribution = detectionLogDAO.aggregateHourlyDistribution(from, to);

        // 2. Daily Trend (number of days in the selected range)
        int days = (int) ChronoUnit.DAYS.between(from, to) + 1;
        List<DailyDetectionCount> dailyTrend = detectionLogDAO.aggregateDailyTrend(Math.max(days, 1));

        // 3. Top Targets (limit to 10)
        List<TargetDetectionSummary> topTargets = detectionLogDAO.aggregateTopTargets(10, from, to);

        // 4. Category Breakdown
        Map<TargetCategory, Long> categoryBreakdown = detectionLogDAO.aggregateCategoryBreakdown(from, to);

        // 5. Confidence Distribution
        Map<String, Long> confidenceDistribution = detectionLogDAO.aggregateConfidenceDistribution(from, to);

        // 6. Compute scalars
        long totalDetections = categoryBreakdown.values().stream().mapToLong(Long::longValue).sum();

        int uniqueTargets = topTargets.size();

        // Calculate weighted avg confidence across detections
        double avgConfidence = 0.0;
        if (!topTargets.isEmpty()) {
            double totalWeightedConf = topTargets.stream()
                    .mapToDouble(t -> t.getAvgConfidence() * t.getTotalDetections())
                    .sum();
            long totalTopDetections = topTargets.stream()
                    .mapToLong(TargetDetectionSummary::getTotalDetections)
                    .sum();
            avgConfidence = totalTopDetections > 0 ? (totalWeightedConf / totalTopDetections) : 0.0;
        }

        // Peak hour identification
        int peakHour = 0;
        long maxHourCount = -1;
        for (HourlyDetectionCount h : hourlyDistribution) {
            if (h.getCount() > maxHourCount) {
                maxHourCount = h.getCount();
                peakHour = h.getHour();
            }
        }

        AnalyticsSnapshot snapshot = new AnalyticsSnapshot(
                hourlyDistribution,
                dailyTrend,
                topTargets,
                categoryBreakdown,
                confidenceDistribution,
                totalDetections,
                uniqueTargets,
                avgConfidence,
                peakHour
        );

        log.info("Analytics snapshot generated: totalDetections={}, peakHour={}:00, uniqueTargets={}",
                totalDetections, peakHour, uniqueTargets);

        return snapshot;
    }
}
