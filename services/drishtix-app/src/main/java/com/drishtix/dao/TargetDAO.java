package com.drishtix.dao;

import com.drishtix.exception.DatabaseException;
import com.drishtix.model.TargetCategory;
import com.drishtix.model.TargetRegistry;
import com.mongodb.client.MongoCollection;
import com.mongodb.client.MongoCursor;
import com.mongodb.client.model.Sorts;
import org.bson.Document;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.time.LocalDateTime;
import java.time.ZoneId;
import java.util.*;
import java.util.regex.Pattern;

import static com.mongodb.client.model.Filters.*;

/**
 * Data Access Object for the {@code targets} collection.
 * Handles all CRUD operations for watchlist targets.
 */
public class TargetDAO {

    private static final Logger log = LoggerFactory.getLogger(TargetDAO.class);
    private static final String COLLECTION = "targets";

    private MongoCollection<Document> collection() {
        return DatabaseManager.getInstance().getCollection(COLLECTION);
    }

    /**
     * Inserts a new target and returns the generated target_id.
     */
    public int insert(TargetRegistry target) {
        try {
            int id = DatabaseManager.getInstance().getNextSequence(COLLECTION);
            Document doc = new Document("_id", id)
                    .append("full_name", target.getFullName())
                    .append("category", target.getCategory().getDbValue())
                    .append("case_number", target.getCaseNumber())
                    .append("description", target.getDescription())
                    .append("profile_image_path", target.getProfileImagePath())
                    .append("is_active", target.isActive())
                    .append("recognizer_label", target.getRecognizerLabel())
                    .append("created_at", new Date())
                    .append("updated_at", new Date());

            collection().insertOne(doc);
            target.setTargetId(id);
            log.info("Target inserted: id={}, name={}, category={}", id,
                    target.getFullName(), target.getCategory());
            return id;

        } catch (Exception e) {
            throw new DatabaseException("Failed to insert target: " + target.getFullName(), e);
        }
    }

    /**
     * Updates an existing target's metadata.
     */
    public void update(TargetRegistry target) {
        try {
            Document update = new Document("$set", new Document()
                    .append("full_name", target.getFullName())
                    .append("category", target.getCategory().getDbValue())
                    .append("case_number", target.getCaseNumber())
                    .append("description", target.getDescription())
                    .append("profile_image_path", target.getProfileImagePath())
                    .append("is_active", target.isActive())
                    .append("updated_at", new Date()));

            collection().updateOne(eq("_id", target.getTargetId()), update);
            log.info("Target updated: id={}, name={}", target.getTargetId(), target.getFullName());

        } catch (Exception e) {
            throw new DatabaseException("Failed to update target: " + target.getTargetId(), e);
        }
    }

    /**
     * Soft-deletes a target by setting is_active = false.
     */
    public void deactivate(int targetId) {
        try {
            collection().updateOne(
                    eq("_id", targetId),
                    new Document("$set", new Document("is_active", false).append("updated_at", new Date()))
            );
            log.info("Target deactivated: id={}", targetId);

        } catch (Exception e) {
            throw new DatabaseException("Failed to deactivate target: " + targetId, e);
        }
    }

    /**
     * Permanently deletes a target from the database.
     * Callers must handle cascading deletes (images, logs, files) before calling this.
     */
    public void delete(int targetId) {
        try {
            long deleted = collection().deleteOne(eq("_id", targetId)).getDeletedCount();
            if (deleted > 0) {
                log.info("Target permanently deleted: id={}", targetId);
            } else {
                log.warn("Target not found for deletion: id={}", targetId);
            }
        } catch (Exception e) {
            throw new DatabaseException("Failed to delete target: " + targetId, e);
        }
    }

    /**
     * Finds a target by its primary key.
     */
    public Optional<TargetRegistry> findById(int targetId) {
        try {
            Document doc = collection().find(eq("_id", targetId)).first();
            if (doc != null) {
                return Optional.of(mapDocument(doc));
            }
            return Optional.empty();

        } catch (Exception e) {
            throw new DatabaseException("Failed to find target by id: " + targetId, e);
        }
    }

    /**
     * Finds a target by its LBPH recognizer label.
     */
    public Optional<TargetRegistry> findByRecognizerLabel(int label) {
        try {
            Document doc = collection().find(
                    and(eq("recognizer_label", label), eq("is_active", true))
            ).first();
            if (doc != null) {
                return Optional.of(mapDocument(doc));
            }
            return Optional.empty();

        } catch (Exception e) {
            throw new DatabaseException("Failed to find target by label: " + label, e);
        }
    }

    /**
     * Returns all active targets in the watchlist.
     */
    public List<TargetRegistry> findAllActive() {
        try {
            return executeQuery(eq("is_active", true));
        } catch (Exception e) {
            throw new DatabaseException("Failed to find all active targets", e);
        }
    }

    /**
     * Returns all targets (including deactivated) for management views.
     */
    public List<TargetRegistry> findAll() {
        try {
            List<TargetRegistry> results = new ArrayList<>();
            try (MongoCursor<Document> cursor = collection()
                    .find()
                    .sort(Sorts.descending("created_at"))
                    .iterator()) {
                while (cursor.hasNext()) {
                    results.add(mapDocument(cursor.next()));
                }
            }
            return results;
        } catch (Exception e) {
            throw new DatabaseException("Failed to find all targets", e);
        }
    }

    /**
     * Searches targets by name, case number, or category.
     */
    public List<TargetRegistry> search(String query, TargetCategory categoryFilter) {
        try {
            List<org.bson.conversions.Bson> filters = new ArrayList<>();

            if (query != null && !query.isBlank()) {
                Pattern regex = Pattern.compile(Pattern.quote(query.trim()), Pattern.CASE_INSENSITIVE);
                filters.add(or(
                        regex("full_name", regex),
                        regex("case_number", regex)
                ));
            }

            if (categoryFilter != null) {
                filters.add(eq("category", categoryFilter.getDbValue()));
            }

            org.bson.conversions.Bson filter = filters.isEmpty()
                    ? new Document()
                    : and(filters);

            List<TargetRegistry> results = new ArrayList<>();
            try (MongoCursor<Document> cursor = collection()
                    .find(filter)
                    .sort(Sorts.descending("created_at"))
                    .iterator()) {
                while (cursor.hasNext()) {
                    results.add(mapDocument(cursor.next()));
                }
            }
            return results;

        } catch (Exception e) {
            throw new DatabaseException("Failed to search targets", e);
        }
    }

    /**
     * Returns the next available recognizer label (max + 1).
     */
    public int getNextRecognizerLabel() {
        try {
            Document doc = collection()
                    .find()
                    .sort(Sorts.descending("recognizer_label"))
                    .projection(new Document("recognizer_label", 1))
                    .first();

            if (doc != null && doc.containsKey("recognizer_label")) {
                return doc.getInteger("recognizer_label") + 1;
            }
            return 1;

        } catch (Exception e) {
            throw new DatabaseException("Failed to get next recognizer label", e);
        }
    }

    /**
     * Returns the count of active targets.
     */
    public int countActive() {
        try {
            return (int) collection().countDocuments(eq("is_active", true));
        } catch (Exception e) {
            throw new DatabaseException("Failed to count active targets", e);
        }
    }

    /**
     * Returns the count of active targets by category.
     */
    public int countByCategory(TargetCategory category) {
        try {
            return (int) collection().countDocuments(
                    and(eq("is_active", true), eq("category", category.getDbValue()))
            );
        } catch (Exception e) {
            throw new DatabaseException("Failed to count targets by category", e);
        }
    }

    // ==================== Private Helpers ====================

    private List<TargetRegistry> executeQuery(org.bson.conversions.Bson filter) {
        List<TargetRegistry> results = new ArrayList<>();
        try (MongoCursor<Document> cursor = collection()
                .find(filter)
                .sort(Sorts.descending("created_at"))
                .iterator()) {
            while (cursor.hasNext()) {
                results.add(mapDocument(cursor.next()));
            }
        }
        return results;
    }

    private TargetRegistry mapDocument(Document doc) {
        TargetRegistry target = new TargetRegistry();
        target.setTargetId(doc.getInteger("_id"));
        target.setFullName(doc.getString("full_name"));
        target.setCategory(TargetCategory.fromDbValue(doc.getString("category")));
        target.setCaseNumber(doc.getString("case_number"));
        target.setDescription(doc.getString("description"));
        target.setProfileImagePath(doc.getString("profile_image_path"));
        target.setActive(doc.getBoolean("is_active", true));
        target.setRecognizerLabel(doc.getInteger("recognizer_label", 0));
        target.setCreatedAt(dateToLocalDateTime(doc.getDate("created_at")));
        target.setUpdatedAt(dateToLocalDateTime(doc.getDate("updated_at")));
        return target;
    }

    private LocalDateTime dateToLocalDateTime(Date date) {
        if (date == null) return LocalDateTime.now();
        return date.toInstant().atZone(ZoneId.systemDefault()).toLocalDateTime();
    }
}
