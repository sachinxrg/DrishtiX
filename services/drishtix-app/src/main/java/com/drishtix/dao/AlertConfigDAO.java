package com.drishtix.dao;

import com.drishtix.exception.DatabaseException;
import com.mongodb.client.MongoCollection;
import com.mongodb.client.MongoCursor;
import org.bson.Document;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.util.HashMap;
import java.util.Map;
import java.util.Optional;

import static com.mongodb.client.model.Filters.eq;

/**
 * Data Access Object for the {@code alert_config} collection.
 * Provides runtime-configurable application settings.
 */
public class AlertConfigDAO {

    private static final Logger log = LoggerFactory.getLogger(AlertConfigDAO.class);
    private static final String COLLECTION = "alert_config";

    private MongoCollection<Document> collection() {
        return DatabaseManager.getInstance().getCollection(COLLECTION);
    }

    /**
     * Returns the value for a specific config key.
     */
    public Optional<String> getValue(String key) {
        try {
            Document doc = collection().find(eq("config_key", key)).first();
            if (doc != null) {
                return Optional.of(doc.getString("config_value"));
            }
            return Optional.empty();

        } catch (Exception e) {
            throw new DatabaseException("Failed to get config value for key: " + key, e);
        }
    }

    /**
     * Updates the value for a specific config key.
     */
    public void updateValue(String key, String value) {
        try {
            collection().updateOne(
                    eq("config_key", key),
                    new Document("$set", new Document("config_value", value)
                            .append("updated_at", new java.util.Date()))
            );
            log.info("Config updated: {} = {}", key, value);

        } catch (Exception e) {
            throw new DatabaseException("Failed to update config: " + key, e);
        }
    }

    /**
     * Returns all configuration entries as a key-value map.
     */
    public Map<String, String> loadAll() {
        Map<String, String> configs = new HashMap<>();

        try (MongoCursor<Document> cursor = collection().find().iterator()) {
            while (cursor.hasNext()) {
                Document doc = cursor.next();
                configs.put(doc.getString("config_key"), doc.getString("config_value"));
            }
            log.debug("Loaded {} configuration entries", configs.size());
            return configs;

        } catch (Exception e) {
            throw new DatabaseException("Failed to load all configurations", e);
        }
    }
}
