package com.drishtix.dao;

import com.drishtix.exception.DatabaseException;
import com.drishtix.model.TargetImage;
import com.mongodb.client.MongoCollection;
import com.mongodb.client.MongoCursor;
import com.mongodb.client.model.Sorts;
import org.bson.Document;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.time.LocalDateTime;
import java.time.ZoneId;
import java.util.ArrayList;
import java.util.Date;
import java.util.List;
import java.util.Set;
import java.util.stream.Collectors;

import static com.mongodb.client.model.Filters.*;

/**
 * Data Access Object for the {@code target_images} collection.
 * Manages multi-photo enrollment per target.
 */
public class TargetImageDAO {

    private static final Logger log = LoggerFactory.getLogger(TargetImageDAO.class);
    private static final String COLLECTION = "target_images";

    private MongoCollection<Document> collection() {
        return DatabaseManager.getInstance().getCollection(COLLECTION);
    }

    /**
     * Inserts a new target image record and returns the generated image_id.
     */
    public int insert(TargetImage image) {
        try {
            int id = DatabaseManager.getInstance().getNextSequence(COLLECTION);
            Document doc = new Document("_id", id)
                    .append("target_id", image.getTargetId())
                    .append("image_path", image.getImagePath())
                    .append("template_path", image.getTemplatePath())
                    .append("image_order", image.getImageOrder())
                    .append("uploaded_at", new Date());

            collection().insertOne(doc);
            image.setImageId(id);
            log.info("Target image inserted: imageId={}, targetId={}", id, image.getTargetId());
            return id;

        } catch (Exception e) {
            throw new DatabaseException("Failed to insert target image", e);
        }
    }

    /**
     * Returns all images for a specific target, ordered by image_order.
     */
    public List<TargetImage> findByTargetId(int targetId) {
        try {
            List<TargetImage> images = new ArrayList<>();
            try (MongoCursor<Document> cursor = collection()
                    .find(eq("target_id", targetId))
                    .sort(Sorts.ascending("image_order"))
                    .iterator()) {
                while (cursor.hasNext()) {
                    images.add(mapDocument(cursor.next()));
                }
            }
            return images;

        } catch (Exception e) {
            throw new DatabaseException("Failed to find images for target: " + targetId, e);
        }
    }

    /**
     * Returns all template images for active targets (used during LBPH training).
     * Replaces the SQL JOIN with a two-step query:
     * 1. Get active target IDs from the targets collection
     * 2. Find images where target_id is in that set and template_path is not null
     */
    public List<TargetImage> findAllActiveTemplates() {
        try {
            // Step 1: Get active target IDs
            MongoCollection<Document> targets = DatabaseManager.getInstance().getCollection("targets");
            Set<Integer> activeIds;
            try (MongoCursor<Document> cursor = targets
                    .find(eq("is_active", true))
                    .projection(new Document("_id", 1))
                    .iterator()) {
                activeIds = new java.util.HashSet<>();
                while (cursor.hasNext()) {
                    activeIds.add(cursor.next().getInteger("_id"));
                }
            }

            if (activeIds.isEmpty()) {
                return new ArrayList<>();
            }

            // Step 2: Find templates for those targets
            List<TargetImage> templates = new ArrayList<>();
            try (MongoCursor<Document> cursor = collection()
                    .find(and(
                            in("target_id", activeIds),
                            ne("template_path", null)
                    ))
                    .sort(Sorts.ascending("target_id", "image_order"))
                    .iterator()) {
                while (cursor.hasNext()) {
                    templates.add(mapDocument(cursor.next()));
                }
            }
            log.debug("Loaded {} active templates for training", templates.size());
            return templates;

        } catch (Exception e) {
            throw new DatabaseException("Failed to load active templates", e);
        }
    }

    /**
     * Returns the count of images for a specific target.
     */
    public int countByTargetId(int targetId) {
        try {
            return (int) collection().countDocuments(eq("target_id", targetId));
        } catch (Exception e) {
            throw new DatabaseException("Failed to count images for target: " + targetId, e);
        }
    }

    /**
     * Deletes all images for a specific target.
     */
    public void deleteByTargetId(int targetId) {
        try {
            long deleted = collection().deleteMany(eq("target_id", targetId)).getDeletedCount();
            log.info("Deleted {} images for target: {}", deleted, targetId);
        } catch (Exception e) {
            throw new DatabaseException("Failed to delete images for target: " + targetId, e);
        }
    }

    private TargetImage mapDocument(Document doc) {
        TargetImage image = new TargetImage();
        image.setImageId(doc.getInteger("_id"));
        image.setTargetId(doc.getInteger("target_id"));
        image.setImagePath(doc.getString("image_path"));
        image.setTemplatePath(doc.getString("template_path"));
        image.setImageOrder(doc.getInteger("image_order", 1));
        image.setUploadedAt(dateToLocalDateTime(doc.getDate("uploaded_at")));
        return image;
    }

    private LocalDateTime dateToLocalDateTime(Date date) {
        if (date == null) return LocalDateTime.now();
        return date.toInstant().atZone(ZoneId.systemDefault()).toLocalDateTime();
    }
}
