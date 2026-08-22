package com.drishtix.dao;

import com.drishtix.exception.DatabaseException;
import com.drishtix.model.DailyDetectionCount;
import com.drishtix.model.DetectionLog;
import com.drishtix.model.HourlyDetectionCount;
import com.drishtix.model.TargetCategory;
import com.drishtix.model.TargetDetectionSummary;
import com.mongodb.client.MongoCollection;
import com.mongodb.client.MongoCursor;
import com.mongodb.client.model.Sorts;
import org.bson.Document;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.time.*;
import java.util.*;

import static com.mongodb.client.model.Filters.*;

/**
 * Data Access Object for the {@code detection_logs} collection.
 * Handles insertion of detection events and querying of historical logs.
 */
public class DetectionLogDAO {

    private static final Logger log = LoggerFactory.getLogger(DetectionLogDAO.class);
    private static final String COLLECTION = "detection_logs";

    private MongoCollection<Document> collection() {
        return DatabaseManager.getInstance().getCollection(COLLECTION);
    }

    /**
     * Inserts a new detection log entry.
     */
    public long insert(DetectionLog detection) {
        try {
            long id = DatabaseManager.getInstance().getNextSequenceLong(COLLECTION);
            Document doc = new Document("_id", id)
                    .append("target_id", detection.getTargetId())
                    .append("detection_timestamp", Date.from(detection.getDetectionTimestamp()
                            .atZone(ZoneId.systemDefault()).toInstant()))
                    .append("match_confidence_score", detection.getMatchConfidenceScore())
                    .append("snapshot_path", detection.getSnapshotPath())
                    .append("camera_id", detection.getCameraId())
                    .append("location_tag", detection.getLocationTag())
                    .append("created_at", new Date());

            collection().insertOne(doc);
            detection.setLogId(id);
            log.debug("Detection logged: logId={}, targetId={}, confidence={}",
                    id, detection.getTargetId(), detection.getMatchConfidenceScore());
            return id;

        } catch (Exception e) {
            throw new DatabaseException("Failed to insert detection log", e);
        }
    }

    /**
     * Returns recent detections with target metadata, limited to the specified count.
     * Enriches detection logs with target and camera data via in-memory lookup (replaces SQL JOINs).
     */
    public List<DetectionLog> findRecent(int limit) {
        try {
            List<DetectionLog> results = new ArrayList<>();
            try (MongoCursor<Document> cursor = collection()
                    .find()
                    .sort(Sorts.descending("detection_timestamp"))
                    .limit(limit)
                    .iterator()) {
                while (cursor.hasNext()) {
                    results.add(mapDocument(cursor.next()));
                }
            }
            enrichWithTargetData(results);
            return results;

        } catch (Exception e) {
            throw new DatabaseException("Failed to find recent detections", e);
        }
    }

    /**
     * Returns detections for a specific target.
     */
    public List<DetectionLog> findByTargetId(int targetId) {
        try {
            List<DetectionLog> results = new ArrayList<>();
            try (MongoCursor<Document> cursor = collection()
                    .find(eq("target_id", targetId))
                    .sort(Sorts.descending("detection_timestamp"))
                    .iterator()) {
                while (cursor.hasNext()) {
                    results.add(mapDocument(cursor.next()));
                }
            }
            enrichWithTargetData(results);
            return results;

        } catch (Exception e) {
            throw new DatabaseException("Failed to find detections for target: " + targetId, e);
        }
    }

    /**
     * Returns detections within a date range, optionally filtered by category.
     */
    public List<DetectionLog> findByDateRange(LocalDate from, LocalDate to, TargetCategory categoryFilter) {
        try {
            Date fromDate = Date.from(from.atStartOfDay(ZoneId.systemDefault()).toInstant());
            Date toDate = Date.from(to.plusDays(1).atStartOfDay(ZoneId.systemDefault()).toInstant());

            List<DetectionLog> results = new ArrayList<>();
            try (MongoCursor<Document> cursor = collection()
                    .find(and(
                            gte("detection_timestamp", fromDate),
                            lt("detection_timestamp", toDate)
                    ))
                    .sort(Sorts.descending("detection_timestamp"))
                    .iterator()) {
                while (cursor.hasNext()) {
                    results.add(mapDocument(cursor.next()));
                }
            }

            enrichWithTargetData(results);

            // Filter by category if specified (done in-memory after enrichment)
            if (categoryFilter != null) {
                results.removeIf(dl -> dl.getTargetCategory() != categoryFilter);
            }

            return results;

        } catch (Exception e) {
            throw new DatabaseException("Failed to find detections by date range", e);
        }
    }

    /**
     * Returns the total count of detections today.
     */
    public int countToday() {
        try {
            Date todayStart = Date.from(LocalDate.now()
                    .atStartOfDay(ZoneId.systemDefault()).toInstant());
            return (int) collection().countDocuments(
                    gte("detection_timestamp", todayStart)
            );
        } catch (Exception e) {
            throw new DatabaseException("Failed to count today's detections", e);
        }
    }

    /**
     * Returns the total count of all detections.
     */
    public int countAll() {
        try {
            return (int) collection().countDocuments();
        } catch (Exception e) {
            throw new DatabaseException("Failed to count all detections", e);
        }
    }

    /**
     * Deletes detection logs older than the specified number of days.
     */
    public int deleteOlderThan(int days) {
        try {
            Date cutoff = Date.from(LocalDateTime.now().minusDays(days)
                    .atZone(ZoneId.systemDefault()).toInstant());
            long deleted = collection().deleteMany(
                    lt("detection_timestamp", cutoff)
            ).getDeletedCount();
            log.info("Purged {} detection logs older than {} days", deleted, days);
            return (int) deleted;

        } catch (Exception e) {
            throw new DatabaseException("Failed to purge old detection logs", e);
        }
    }

    /**
     * Finds a single detection log entry by its ID.
     */
    public Optional<DetectionLog> findById(long logId) {
        try {
            Document doc = collection().find(eq("_id", logId)).first();
            if (doc != null) {
                DetectionLog dl = mapDocument(doc);
                enrichWithTargetData(List.of(dl));
                return Optional.of(dl);
            }
            return Optional.empty();
        } catch (Exception e) {
            throw new DatabaseException("Failed to find detection log by id: " + logId, e);
        }
    }

    /**
     * Deletes a single detection log entry by its ID.
     *
     * @return true if a document was deleted, false if not found
     */
    public boolean deleteById(long logId) {
        try {
            long deleted = collection().deleteOne(eq("_id", logId)).getDeletedCount();
            if (deleted > 0) {
                log.info("Detection log deleted: logId={}", logId);
                return true;
            }
            log.warn("Detection log not found for deletion: logId={}", logId);
            return false;
        } catch (Exception e) {
            throw new DatabaseException("Failed to delete detection log: " + logId, e);
        }
    }

    /**
     * Deletes all detection log entries for a specific target.
     * Used during cascading target deletion.
     *
     * @return number of logs deleted
     */
    public int deleteByTargetId(int targetId) {
        try {
            long deleted = collection().deleteMany(eq("target_id", targetId)).getDeletedCount();
            log.info("Deleted {} detection logs for target: {}", deleted, targetId);
            return (int) deleted;
        } catch (Exception e) {
            throw new DatabaseException("Failed to delete detection logs for target: " + targetId, e);
        }
    }

    /**
     * Aggregates detection counts by hour of day (0–23) for the given date range.
     * Returns a complete 24-element list where every hour is represented.
     *
     * @param from start date (inclusive)
     * @param to   end date (inclusive)
     * @return 24-element list of HourlyDetectionCount sorted from hour 0 to 23
     */
    public List<HourlyDetectionCount> aggregateHourlyDistribution(LocalDate from, LocalDate to) {
        try {
            Date fromDate = Date.from(from.atStartOfDay(ZoneId.systemDefault()).toInstant());
            Date toDate = Date.from(to.plusDays(1).atStartOfDay(ZoneId.systemDefault()).toInstant());

            // Initialize all 24 hours with 0 counts
            long[] hourCounts = new long[24];

            List<Document> pipeline = List.of(
                    new Document("$match", and(
                            gte("detection_timestamp", fromDate),
                            lt("detection_timestamp", toDate)
                    )),
                    new Document("$group", new Document("_id",
                            new Document("$hour", new Document("date", "$detection_timestamp")
                                    .append("timezone", ZoneId.systemDefault().getId())))
                            .append("count", new Document("$sum", 1))),
                    new Document("$sort", new Document("_id", 1))
            );

            try (MongoCursor<Document> cursor = collection().aggregate(pipeline).iterator()) {
                while (cursor.hasNext()) {
                    Document doc = cursor.next();
                    Object idVal = doc.get("_id");
                    if (idVal instanceof Number) {
                        int hour = ((Number) idVal).intValue();
                        long count = ((Number) doc.get("count")).longValue();
                        if (hour >= 0 && hour < 24) {
                            hourCounts[hour] = count;
                        }
                    }
                }
            }

            List<HourlyDetectionCount> result = new ArrayList<>(24);
            for (int h = 0; h < 24; h++) {
                result.add(new HourlyDetectionCount(h, hourCounts[h]));
            }
            return result;

        } catch (Exception e) {
            throw new DatabaseException("Failed to aggregate hourly detection distribution", e);
        }
    }

    /**
     * Aggregates daily detection counts for the trailing N days up to today.
     * Returns an ordered list of DailyDetectionCount objects with every day in the range represented.
     *
     * @param lastNDays number of trailing days to include (e.g. 7 or 30)
     * @return chronologically sorted list of DailyDetectionCount
     */
    public List<DailyDetectionCount> aggregateDailyTrend(int lastNDays) {
        try {
            if (lastNDays <= 0) lastNDays = 7;

            LocalDate today = LocalDate.now();
            LocalDate startDate = today.minusDays(lastNDays - 1);

            Date fromDate = Date.from(startDate.atStartOfDay(ZoneId.systemDefault()).toInstant());
            Date toDate = Date.from(today.plusDays(1).atStartOfDay(ZoneId.systemDefault()).toInstant());

            // Initialize all dates with 0 counts
            Map<LocalDate, Long> dayCounts = new LinkedHashMap<>();
            for (int i = 0; i < lastNDays; i++) {
                dayCounts.put(startDate.plusDays(i), 0L);
            }

            List<Document> pipeline = List.of(
                    new Document("$match", and(
                            gte("detection_timestamp", fromDate),
                            lt("detection_timestamp", toDate)
                    )),
                    new Document("$group", new Document("_id",
                            new Document("$dateToString", new Document("format", "%Y-%m-%d")
                                    .append("date", "$detection_timestamp")
                                    .append("timezone", ZoneId.systemDefault().getId())))
                            .append("count", new Document("$sum", 1))),
                    new Document("$sort", new Document("_id", 1))
            );

            try (MongoCursor<Document> cursor = collection().aggregate(pipeline).iterator()) {
                while (cursor.hasNext()) {
                    Document doc = cursor.next();
                    String dateStr = doc.getString("_id");
                    if (dateStr != null) {
                        try {
                            LocalDate parsed = LocalDate.parse(dateStr);
                            long count = ((Number) doc.get("count")).longValue();
                            dayCounts.put(parsed, count);
                        } catch (Exception ignored) {
                        }
                    }
                }
            }

            List<DailyDetectionCount> result = new ArrayList<>(dayCounts.size());
            for (Map.Entry<LocalDate, Long> entry : dayCounts.entrySet()) {
                result.add(new DailyDetectionCount(entry.getKey(), entry.getValue()));
            }
            return result;

        } catch (Exception e) {
            throw new DatabaseException("Failed to aggregate daily detection trend", e);
        }
    }

    /**
     * Aggregates the most frequently detected targets within a date range.
     * Enriches the grouped results with target names and categories.
     *
     * @param limit maximum number of top targets to return (e.g. 5 or 10)
     * @param from  start date (inclusive)
     * @param to    end date (inclusive)
     * @return sorted list of TargetDetectionSummary in descending order of detection count
     */
    public List<TargetDetectionSummary> aggregateTopTargets(int limit, LocalDate from, LocalDate to) {
        try {
            if (limit <= 0) limit = 10;

            Date fromDate = Date.from(from.atStartOfDay(ZoneId.systemDefault()).toInstant());
            Date toDate = Date.from(to.plusDays(1).atStartOfDay(ZoneId.systemDefault()).toInstant());

            List<Document> pipeline = List.of(
                    new Document("$match", and(
                            gte("detection_timestamp", fromDate),
                            lt("detection_timestamp", toDate)
                    )),
                    new Document("$group", new Document("_id", "$target_id")
                            .append("totalCount", new Document("$sum", 1))
                            .append("lastSeen", new Document("$max", "$detection_timestamp"))
                            .append("avgConfidence", new Document("$avg", "$match_confidence_score"))),
                    new Document("$sort", new Document("totalCount", -1)),
                    new Document("$limit", limit)
            );

            List<TargetDetectionSummary> rawList = new ArrayList<>();
            Set<Integer> targetIds = new HashSet<>();

            try (MongoCursor<Document> cursor = collection().aggregate(pipeline).iterator()) {
                while (cursor.hasNext()) {
                    Document doc = cursor.next();
                    int targetId = doc.getInteger("_id");
                    long count = ((Number) doc.get("totalCount")).longValue();
                    Date lastSeenDate = doc.getDate("lastSeen");
                    LocalDateTime lastSeen = dateToLocalDateTime(lastSeenDate);
                    double avgConf = doc.getDouble("avgConfidence") != null ? doc.getDouble("avgConfidence") : 0.0;

                    targetIds.add(targetId);
                    rawList.add(new TargetDetectionSummary(targetId, null, null, count, lastSeen, avgConf));
                }
            }

            if (rawList.isEmpty()) {
                return Collections.emptyList();
            }

            // Batch load targets from targets collection
            Map<Integer, Document> targetMap = new HashMap<>();
            MongoCollection<Document> targets = DatabaseManager.getInstance().getCollection("targets");
            try (MongoCursor<Document> cursor = targets
                    .find(in("_id", targetIds))
                    .projection(new Document("full_name", 1).append("category", 1))
                    .iterator()) {
                while (cursor.hasNext()) {
                    Document doc = cursor.next();
                    targetMap.put(doc.getInteger("_id"), doc);
                }
            }

            List<TargetDetectionSummary> enrichedList = new ArrayList<>(rawList.size());
            for (TargetDetectionSummary raw : rawList) {
                Document targetDoc = targetMap.get(raw.getTargetId());
                String name = targetDoc != null ? targetDoc.getString("full_name") : "Target #" + raw.getTargetId();
                String catStr = targetDoc != null ? targetDoc.getString("category") : null;
                TargetCategory category = catStr != null ? TargetCategory.fromDbValue(catStr) : TargetCategory.CRIMINAL;

                enrichedList.add(new TargetDetectionSummary(
                        raw.getTargetId(),
                        name,
                        category,
                        raw.getTotalDetections(),
                        raw.getLastSeen(),
                        raw.getAvgConfidence()
                ));
            }

            return enrichedList;

        } catch (Exception e) {
            throw new DatabaseException("Failed to aggregate top targets", e);
        }
    }

    /**
     * Aggregates detection counts by TargetCategory for the given date range.
     *
     * @param from start date (inclusive)
     * @param to   end date (inclusive)
     * @return Map of TargetCategory to total detection count
     */
    public Map<TargetCategory, Long> aggregateCategoryBreakdown(LocalDate from, LocalDate to) {
        try {
            Date fromDate = Date.from(from.atStartOfDay(ZoneId.systemDefault()).toInstant());
            Date toDate = Date.from(to.plusDays(1).atStartOfDay(ZoneId.systemDefault()).toInstant());

            Map<TargetCategory, Long> breakdown = new EnumMap<>(TargetCategory.class);
            breakdown.put(TargetCategory.CRIMINAL, 0L);
            breakdown.put(TargetCategory.MISSING_PERSON, 0L);

            // Group detections by target_id first
            List<Document> pipeline = List.of(
                    new Document("$match", and(
                            gte("detection_timestamp", fromDate),
                            lt("detection_timestamp", toDate)
                    )),
                    new Document("$group", new Document("_id", "$target_id")
                            .append("count", new Document("$sum", 1)))
            );

            Map<Integer, Long> targetCounts = new HashMap<>();
            try (MongoCursor<Document> cursor = collection().aggregate(pipeline).iterator()) {
                while (cursor.hasNext()) {
                    Document doc = cursor.next();
                    int targetId = doc.getInteger("_id");
                    long count = ((Number) doc.get("count")).longValue();
                    targetCounts.put(targetId, count);
                }
            }

            if (!targetCounts.isEmpty()) {
                MongoCollection<Document> targets = DatabaseManager.getInstance().getCollection("targets");
                try (MongoCursor<Document> cursor = targets
                        .find(in("_id", targetCounts.keySet()))
                        .projection(new Document("category", 1))
                        .iterator()) {
                    while (cursor.hasNext()) {
                        Document doc = cursor.next();
                        int targetId = doc.getInteger("_id");
                        String catStr = doc.getString("category");
                        TargetCategory category = catStr != null ? TargetCategory.fromDbValue(catStr) : TargetCategory.CRIMINAL;
                        long count = targetCounts.getOrDefault(targetId, 0L);
                        breakdown.put(category, breakdown.getOrDefault(category, 0L) + count);
                    }
                }
            }

            return breakdown;

        } catch (Exception e) {
            throw new DatabaseException("Failed to aggregate category breakdown", e);
        }
    }

    /**
     * Aggregates detection counts bucketed into confidence score ranges.
     *
     * @param from start date (inclusive)
     * @param to   end date (inclusive)
     * @return Map of confidence bucket label (e.g. "90-100%") to detection count
     */
    public Map<String, Long> aggregateConfidenceDistribution(LocalDate from, LocalDate to) {
        try {
            Date fromDate = Date.from(from.atStartOfDay(ZoneId.systemDefault()).toInstant());
            Date toDate = Date.from(to.plusDays(1).atStartOfDay(ZoneId.systemDefault()).toInstant());

            Map<String, Long> buckets = new LinkedHashMap<>();
            buckets.put("< 50%", 0L);
            buckets.put("50% - 70%", 0L);
            buckets.put("70% - 80%", 0L);
            buckets.put("80% - 90%", 0L);
            buckets.put("90% - 100%", 0L);

            List<Document> pipeline = List.of(
                    new Document("$match", and(
                            gte("detection_timestamp", fromDate),
                            lt("detection_timestamp", toDate)
                    )),
                    new Document("$project", new Document("score", "$match_confidence_score"))
            );

            try (MongoCursor<Document> cursor = collection().aggregate(pipeline).iterator()) {
                while (cursor.hasNext()) {
                    Document doc = cursor.next();
                    Double score = doc.getDouble("score");
                    if (score != null) {
                        double pct = score <= 1.0 ? score * 100.0 : score;
                        if (pct >= 90.0) {
                            buckets.put("90% - 100%", buckets.get("90% - 100%") + 1);
                        } else if (pct >= 80.0) {
                            buckets.put("80% - 90%", buckets.get("80% - 90%") + 1);
                        } else if (pct >= 70.0) {
                            buckets.put("70% - 80%", buckets.get("70% - 80%") + 1);
                        } else if (pct >= 50.0) {
                            buckets.put("50% - 70%", buckets.get("50% - 70%") + 1);
                        } else {
                            buckets.put("< 50%", buckets.get("< 50%") + 1);
                        }
                    }
                }
            }

            return buckets;

        } catch (Exception e) {
            throw new DatabaseException("Failed to aggregate confidence distribution", e);
        }
    }

    // ==================== Private Helpers ====================

    /**
     * Enriches detection logs with target name, category, case number, and camera name.
     * Replaces the SQL JOINs with in-memory lookups.
     */
    private void enrichWithTargetData(List<DetectionLog> logs) {
        if (logs.isEmpty()) return;

        try {
            // Collect unique target IDs and camera IDs
            Set<Integer> targetIds = new HashSet<>();
            Set<Integer> cameraIds = new HashSet<>();
            for (DetectionLog dl : logs) {
                targetIds.add(dl.getTargetId());
                if (dl.getCameraId() != null) cameraIds.add(dl.getCameraId());
            }

            // Batch-load targets
            Map<Integer, Document> targetMap = new HashMap<>();
            MongoCollection<Document> targets = DatabaseManager.getInstance().getCollection("targets");
            try (MongoCursor<Document> cursor = targets
                    .find(in("_id", targetIds))
                    .projection(new Document("full_name", 1).append("category", 1).append("case_number", 1))
                    .iterator()) {
                while (cursor.hasNext()) {
                    Document doc = cursor.next();
                    targetMap.put(doc.getInteger("_id"), doc);
                }
            }

            // Batch-load cameras
            Map<Integer, String> cameraMap = new HashMap<>();
            if (!cameraIds.isEmpty()) {
                MongoCollection<Document> cameras = DatabaseManager.getInstance().getCollection("camera_sources");
                try (MongoCursor<Document> cursor = cameras
                        .find(in("_id", cameraIds))
                        .projection(new Document("camera_name", 1))
                        .iterator()) {
                    while (cursor.hasNext()) {
                        Document doc = cursor.next();
                        cameraMap.put(doc.getInteger("_id"), doc.getString("camera_name"));
                    }
                }
            }

            // Enrich
            for (DetectionLog dl : logs) {
                Document targetDoc = targetMap.get(dl.getTargetId());
                if (targetDoc != null) {
                    dl.setTargetName(targetDoc.getString("full_name"));
                    dl.setTargetCategory(TargetCategory.fromDbValue(targetDoc.getString("category")));
                    dl.setCaseNumber(targetDoc.getString("case_number"));
                }
                if (dl.getCameraId() != null) {
                    dl.setCameraName(cameraMap.get(dl.getCameraId()));
                }
            }
        } catch (Exception e) {
            log.warn("Failed to enrich detection logs with target/camera data", e);
        }
    }

    private DetectionLog mapDocument(Document doc) {
        DetectionLog dl = new DetectionLog();
        // Handle both Long and Integer _id from the counter
        Object idVal = doc.get("_id");
        if (idVal instanceof Long) {
            dl.setLogId((Long) idVal);
        } else if (idVal instanceof Integer) {
            dl.setLogId(((Integer) idVal).longValue());
        }
        dl.setTargetId(doc.getInteger("target_id"));
        dl.setDetectionTimestamp(dateToLocalDateTime(doc.getDate("detection_timestamp")));
        dl.setMatchConfidenceScore(doc.getDouble("match_confidence_score"));
        dl.setSnapshotPath(doc.getString("snapshot_path"));
        dl.setCameraId(doc.getInteger("camera_id"));
        dl.setLocationTag(doc.getString("location_tag"));
        dl.setCreatedAt(dateToLocalDateTime(doc.getDate("created_at")));
        return dl;
    }

    private LocalDateTime dateToLocalDateTime(Date date) {
        if (date == null) return LocalDateTime.now();
        return date.toInstant().atZone(ZoneId.systemDefault()).toLocalDateTime();
    }
}
