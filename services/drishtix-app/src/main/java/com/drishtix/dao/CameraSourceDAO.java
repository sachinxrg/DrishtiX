package com.drishtix.dao;

import com.drishtix.exception.DatabaseException;
import com.drishtix.model.CameraSource;
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

import static com.mongodb.client.model.Filters.eq;

/**
 * Data Access Object for the {@code camera_sources} collection.
 */
public class CameraSourceDAO {

    private static final Logger log = LoggerFactory.getLogger(CameraSourceDAO.class);
    private static final String COLLECTION = "camera_sources";

    private MongoCollection<Document> collection() {
        return DatabaseManager.getInstance().getCollection(COLLECTION);
    }

    public List<CameraSource> findAllActive() {
        try {
            List<CameraSource> cameras = new ArrayList<>();
            try (MongoCursor<Document> cursor = collection()
                    .find(eq("is_active", true))
                    .sort(Sorts.ascending("_id"))
                    .iterator()) {
                while (cursor.hasNext()) {
                    cameras.add(mapDocument(cursor.next()));
                }
            }
            return cameras;

        } catch (Exception e) {
            throw new DatabaseException("Failed to load camera sources", e);
        }
    }

    public int insert(CameraSource camera) {
        try {
            int id = DatabaseManager.getInstance().getNextSequence(COLLECTION);
            Document doc = new Document("_id", id)
                    .append("camera_name", camera.getCameraName())
                    .append("source_uri", camera.getSourceUri())
                    .append("is_active", camera.isActive())
                    .append("created_at", new Date());

            collection().insertOne(doc);
            camera.setCameraId(id);
            return id;

        } catch (Exception e) {
            throw new DatabaseException("Failed to insert camera source", e);
        }
    }

    private CameraSource mapDocument(Document doc) {
        CameraSource cam = new CameraSource();
        cam.setCameraId(doc.getInteger("_id"));
        cam.setCameraName(doc.getString("camera_name"));
        cam.setSourceUri(doc.getString("source_uri"));
        cam.setActive(doc.getBoolean("is_active", true));
        cam.setCreatedAt(dateToLocalDateTime(doc.getDate("created_at")));
        return cam;
    }

    private LocalDateTime dateToLocalDateTime(Date date) {
        if (date == null) return LocalDateTime.now();
        return date.toInstant().atZone(ZoneId.systemDefault()).toLocalDateTime();
    }
}
