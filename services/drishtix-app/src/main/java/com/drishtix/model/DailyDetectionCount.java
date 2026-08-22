package com.drishtix.model;

import java.time.LocalDate;
import java.time.format.DateTimeFormatter;
import java.util.Objects;

/**
 * Value object representing the detection count for a single calendar day.
 * Used by the Analytics Dashboard to render the daily trend line chart.
 *
 * <p>Each instance maps one date to its total detection count.</p>
 */
public class DailyDetectionCount {

    private static final DateTimeFormatter DISPLAY_FORMAT = DateTimeFormatter.ofPattern("dd MMM");

    /** The calendar date. */
    private final LocalDate date;

    /** Total number of detections recorded on this date. */
    private final long count;

    /**
     * Constructs a DailyDetectionCount.
     *
     * @param date  the calendar date (must not be null)
     * @param count the detection count for that date
     * @throws IllegalArgumentException if date is null or count is negative
     */
    public DailyDetectionCount(LocalDate date, long count) {
        if (date == null) {
            throw new IllegalArgumentException("Date must not be null");
        }
        if (count < 0) {
            throw new IllegalArgumentException("Count must be non-negative, got: " + count);
        }
        this.date = date;
        this.count = count;
    }

    public LocalDate getDate() {
        return date;
    }

    public long getCount() {
        return count;
    }

    /**
     * Returns a short display label for the date (e.g., "22 Aug").
     */
    public String getDateLabel() {
        return date.format(DISPLAY_FORMAT);
    }

    @Override
    public boolean equals(Object o) {
        if (this == o) return true;
        if (o == null || getClass() != o.getClass()) return false;
        DailyDetectionCount that = (DailyDetectionCount) o;
        return count == that.count && date.equals(that.date);
    }

    @Override
    public int hashCode() {
        return Objects.hash(date, count);
    }

    @Override
    public String toString() {
        return "DailyDetectionCount{date=" + date + ", count=" + count + '}';
    }
}
