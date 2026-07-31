package com.drishtix.dao;

import com.drishtix.exception.DatabaseException;
import com.drishtix.model.PersonEmbedding;
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
 * Data Access Object for the {@code person_embeddings} collection.
 * Stores 512-dimensional feature vectors extracted by the ReID service
 * for cross-camera person re-identification matching.
 */
public class PersonEmbeddingDAO {

    private static final Logger log = LoggerFactory.getLogger(PersonEmbeddingDAO.class);
    private static final String COLLECTION = "person_embeddings";

    private MongoCollection<Document> collection() {
        return DatabaseManager.getInstance().getCollection(COLLECTION);
    }

    /**
     * Inserts a new person embedding.
     *
     * @return the generated embedding ID
     */
    public long insert(PersonEmbedding embedding) {
        try {
            long id = DatabaseManager.getInstance().getNextSequenceLong(COLLECTION);

            // Convert double[] to List<Double> for BSON array storage
            List<Double> embeddingList = new ArrayList<>(embedding.getEmbedding().length);
            for (double val : embedding.getEmbedding()) {
                embeddingList.add(val);
            }

            Document doc = new Document("_id", id)
                    .append("target_id", embedding.getTargetId())
                    .append("camera_id", embedding.getCameraId())
                    .append("embedding", embeddingList)
                    .append("snapshot_path", embedding.getSnapshotPath())
                    .append("timestamp", Date.from(embedding.getTimestamp()
                            .atZone(ZoneId.systemDefault()).toInstant()));

            collection().insertOne(doc);
            embedding.setEmbeddingId(id);
            log.debug("Person embedding stored: id={}, targetId={}, cameraId={}, dims={}",
                    id, embedding.getTargetId(), embedding.getCameraId(), embedding.getDimensions());
            return id;

        } catch (Exception e) {
            throw new DatabaseException("Failed to insert person embedding", e);
        }
    }

    /**
     * Returns the most recent embeddings, ordered by timestamp descending.
     *
     * @param limit maximum number of embeddings to return
     */
    public List<PersonEmbedding> findRecent(int limit) {
        try {
            List<PersonEmbedding> results = new ArrayList<>();
            try (MongoCursor<Document> cursor = collection()
                    .find()
                    .sort(Sorts.descending("timestamp"))
                    .limit(limit)
                    .iterator()) {
                while (cursor.hasNext()) {
                    results.add(mapDocument(cursor.next()));
                }
            }
            return results;

        } catch (Exception e) {
            throw new DatabaseException("Failed to find recent embeddings", e);
        }
    }

    /**
     * Returns recent embeddings from cameras OTHER than the specified camera.
     * Used for cross-camera matching — we only want to match across different feeds.
     *
     * @param excludeCameraId camera ID to exclude from results
     * @param limit           maximum number of embeddings to return
     */
    public List<PersonEmbedding> findRecentExcludingCamera(int excludeCameraId, int limit) {
        try {
            List<PersonEmbedding> results = new ArrayList<>();
            try (MongoCursor<Document> cursor = collection()
                    .find(ne("camera_id", excludeCameraId))
                    .sort(Sorts.descending("timestamp"))
                    .limit(limit)
                    .iterator()) {
                while (cursor.hasNext()) {
                    results.add(mapDocument(cursor.next()));
                }
            }
            return results;

        } catch (Exception e) {
            throw new DatabaseException("Failed to find embeddings excluding camera: " + excludeCameraId, e);
        }
    }

    /**
     * Returns embeddings for a specific target.
     */
    public List<PersonEmbedding> findByTargetId(int targetId) {
        try {
            List<PersonEmbedding> results = new ArrayList<>();
            try (MongoCursor<Document> cursor = collection()
                    .find(eq("target_id", targetId))
                    .sort(Sorts.descending("timestamp"))
                    .iterator()) {
                while (cursor.hasNext()) {
                    results.add(mapDocument(cursor.next()));
                }
            }
            return results;

        } catch (Exception e) {
            throw new DatabaseException("Failed to find embeddings for target: " + targetId, e);
        }
    }

    /**
     * Deletes embeddings older than the specified number of days.
     *
     * @return number of embeddings deleted
     */
    public int deleteOlderThan(int days) {
        try {
            Date cutoff = Date.from(LocalDateTime.now().minusDays(days)
                    .atZone(ZoneId.systemDefault()).toInstant());
            long deleted = collection().deleteMany(
                    lt("timestamp", cutoff)
            ).getDeletedCount();
            log.info("Purged {} person embeddings older than {} days", deleted, days);
            return (int) deleted;

        } catch (Exception e) {
            throw new DatabaseException("Failed to purge old embeddings", e);
        }
    }

    /**
     * Deletes all embeddings for a specific target.
     * Used during cascading target deletion.
     */
    public int deleteByTargetId(int targetId) {
        try {
            long deleted = collection().deleteMany(eq("target_id", targetId)).getDeletedCount();
            log.info("Deleted {} embeddings for target: {}", deleted, targetId);
            return (int) deleted;
        } catch (Exception e) {
            throw new DatabaseException("Failed to delete embeddings for target: " + targetId, e);
        }
    }

    /**
     * Returns the total count of stored embeddings.
     */
    public int countAll() {
        try {
            return (int) collection().countDocuments();
        } catch (Exception e) {
            throw new DatabaseException("Failed to count embeddings", e);
        }
    }

    // ==================== Private Helpers ====================

    @SuppressWarnings("unchecked")
    private PersonEmbedding mapDocument(Document doc) {
        PersonEmbedding pe = new PersonEmbedding();

        // Handle both Long and Integer _id from the counter
        Object idVal = doc.get("_id");
        if (idVal instanceof Long) {
            pe.setEmbeddingId((Long) idVal);
        } else if (idVal instanceof Integer) {
            pe.setEmbeddingId(((Integer) idVal).longValue());
        }

        pe.setTargetId(doc.getInteger("target_id"));
        pe.setCameraId(doc.getInteger("camera_id"));
        pe.setSnapshotPath(doc.getString("snapshot_path"));
        pe.setTimestamp(dateToLocalDateTime(doc.getDate("timestamp")));

        // Convert BSON List<Double> back to double[]
        List<Number> embeddingList = (List<Number>) doc.get("embedding");
        if (embeddingList != null) {
            double[] embeddingArray = new double[embeddingList.size()];
            for (int i = 0; i < embeddingList.size(); i++) {
                embeddingArray[i] = embeddingList.get(i).doubleValue();
            }
            pe.setEmbedding(embeddingArray);
        }

        return pe;
    }

    private LocalDateTime dateToLocalDateTime(Date date) {
        if (date == null) return LocalDateTime.now();
        return date.toInstant().atZone(ZoneId.systemDefault()).toLocalDateTime();
    }
}
