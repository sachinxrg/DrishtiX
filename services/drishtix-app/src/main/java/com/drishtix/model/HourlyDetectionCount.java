package com.drishtix.model;

import java.util.Objects;

/**
 * Value object representing the detection count for a single hour of the day.
 * Used by the Analytics Dashboard to render the hourly distribution heatmap (BarChart).
 *
 * <p>Each instance maps one hour (0–23) to its total detection count within a queried date range.</p>
 */
public class HourlyDetectionCount {

    /** Hour of the day (0 = midnight, 23 = 11 PM). */
    private final int hour;

    /** Total number of detections recorded during this hour. */
    private final long count;

    /**
     * Constructs an HourlyDetectionCount.
     *
     * @param hour  the hour of the day (0–23)
     * @param count the detection count for that hour
     * @throws IllegalArgumentException if hour is outside 0–23 or count is negative
     */
    public HourlyDetectionCount(int hour, long count) {
        if (hour < 0 || hour > 23) {
            throw new IllegalArgumentException("Hour must be between 0 and 23, got: " + hour);
        }
        if (count < 0) {
            throw new IllegalArgumentException("Count must be non-negative, got: " + count);
        }
        this.hour = hour;
        this.count = count;
    }

    public int getHour() {
        return hour;
    }

    public long getCount() {
        return count;
    }

    /**
     * Returns a human-readable label for the hour (e.g., "00:00", "14:00").
     */
    public String getHourLabel() {
        return String.format("%02d:00", hour);
    }

    @Override
    public boolean equals(Object o) {
        if (this == o) return true;
        if (o == null || getClass() != o.getClass()) return false;
        HourlyDetectionCount that = (HourlyDetectionCount) o;
        return hour == that.hour && count == that.count;
    }

    @Override
    public int hashCode() {
        return Objects.hash(hour, count);
    }

    @Override
    public String toString() {
        return "HourlyDetectionCount{hour=" + hour + ", count=" + count + '}';
    }
}
