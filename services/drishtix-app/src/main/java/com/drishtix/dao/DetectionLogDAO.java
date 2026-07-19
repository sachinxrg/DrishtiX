package com.drishtix.dao;

import com.drishtix.exception.DatabaseException;
import com.drishtix.model.DetectionLog;
import com.drishtix.model.TargetCategory;
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
