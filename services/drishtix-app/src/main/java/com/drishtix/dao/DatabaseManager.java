package com.drishtix.dao;

import com.mongodb.client.MongoClient;
import com.mongodb.client.MongoClients;
import com.mongodb.client.MongoCollection;
import com.mongodb.client.MongoDatabase;
import com.mongodb.client.model.FindOneAndUpdateOptions;
import com.mongodb.client.model.ReturnDocument;
import org.bson.Document;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.io.FileInputStream;
import java.io.IOException;
import java.io.InputStream;
import java.util.Properties;

import static com.mongodb.client.model.Filters.eq;
import static com.mongodb.client.model.Updates.inc;

/**
 * Singleton database connection manager using MongoDB Java Driver.
 * <p>
 * Reads configuration from {@code config.properties} in the working directory.
 * Provides thread-safe access to the MongoDB database and collections.
 * </p>
 */
public final class DatabaseManager {

    private static final Logger log = LoggerFactory.getLogger(DatabaseManager.class);
    private static final String CONFIG_FILE = "config.properties";

    private static volatile DatabaseManager instance;
    private final MongoClient mongoClient;
    private final MongoDatabase database;

    private DatabaseManager() {
        Properties props = loadProperties();

        String uri = props.getProperty("db.uri", "mongodb://localhost:27017");
        String dbName = props.getProperty("db.name", "drishtix_db");

        MongoClient tempClient = null;
        MongoDatabase tempDb = null;
        try {
            tempClient = MongoClients.create(uri);
            tempDb = tempClient.getDatabase(dbName);
            // Validate the connection by running a ping command
            tempDb.runCommand(new Document("ping", 1));
            log.info("MongoDB connection initialized — uri: {}, database: {}", uri, dbName);
        } catch (Exception e) {
            log.error("Failed to initialize MongoDB connection. " +
                    "URI: {}, Database: {}. Cause: {}. " +
                    "Ensure MongoDB is running and the URI in config.properties is correct.",
                    uri, dbName, e.getMessage());
        }
        this.mongoClient = tempClient;
        this.database = tempDb;
    }

    /**
     * Returns the singleton DatabaseManager instance (double-checked locking).
     */
    public static DatabaseManager getInstance() {
        if (instance == null) {
            synchronized (DatabaseManager.class) {
                if (instance == null) {
                    instance = new DatabaseManager();
                }
            }
        }
        return instance;
    }

    /**
     * Returns the MongoDB database instance.
     *
     * @return the MongoDatabase, or null if connection failed
     */
    public MongoDatabase getDatabase() {
        return database;
    }

    /**
     * Returns a MongoDB collection by name.
     *
     * @param collectionName the name of the collection
     * @return the MongoCollection
     * @throws IllegalStateException if the database is not initialized
     */
    public MongoCollection<Document> getCollection(String collectionName) {
        if (database == null) {
            throw new IllegalStateException(
                    "MongoDB is not initialized (Database may be offline or URI invalid).");
        }
        return database.getCollection(collectionName);
    }

    /**
     * Atomically gets the next integer sequence value for the given collection name.
     * Uses a "counters" collection to simulate auto-increment IDs.
     *
     * @param sequenceName the name of the sequence (e.g., "targets", "target_images")
     * @return the next integer ID
     */
    public int getNextSequence(String sequenceName) {
        MongoCollection<Document> counters = getCollection("counters");
        Document result = counters.findOneAndUpdate(
                eq("_id", sequenceName),
                inc("seq", 1),
                new FindOneAndUpdateOptions()
                        .returnDocument(ReturnDocument.AFTER)
                        .upsert(true)
        );
        return result.getInteger("seq");
    }

    /**
     * Atomically gets the next long sequence value for the given collection name.
     *
     * @param sequenceName the name of the sequence
     * @return the next long ID
     */
    public long getNextSequenceLong(String sequenceName) {
        MongoCollection<Document> counters = getCollection("counters");
        Document result = counters.findOneAndUpdate(
                eq("_id", sequenceName),
                inc("seq", 1L),
                new FindOneAndUpdateOptions()
                        .returnDocument(ReturnDocument.AFTER)
                        .upsert(true)
        );
        return result.getLong("seq");
    }

    /**
     * Tests the database connection and returns true if successful.
     */
    public boolean testConnection() {
        try {
            if (database == null) return false;
            database.runCommand(new Document("ping", 1));
            return true;
        } catch (Exception e) {
            log.error("MongoDB connection test failed", e);
            return false;
        }
    }

    /**
     * Clears all system data (targets, images, logs) and resets counters.
     * Does NOT clear camera_sources or alert_config.
     */
    public void clearSystemData() {
        if (database != null) {
            getCollection("targets").deleteMany(new Document());
            getCollection("target_images").deleteMany(new Document());
            getCollection("detection_logs").deleteMany(new Document());
            getCollection("audit_log").deleteMany(new Document());
            
            MongoCollection<Document> counters = getCollection("counters");
            counters.updateOne(eq("_id", "targets"), new Document("$set", new Document("seq", 0)));
            counters.updateOne(eq("_id", "target_images"), new Document("$set", new Document("seq", 0)));
            counters.updateOne(eq("_id", "detection_logs"), new Document("$set", new Document("seq", 0)));
            counters.updateOne(eq("_id", "audit_log"), new Document("$set", new Document("seq", 0)));
            
            log.warn("System data (registry and logs) has been completely wiped.");
        }
    }

    /**
     * Closes the MongoDB client. Called during application shutdown.
     */
    public void shutdown() {
        if (mongoClient != null) {
            mongoClient.close();
            log.info("MongoDB client closed");
        }
    }

    /**
     * Loads database configuration from the config.properties file.
     */
    private Properties loadProperties() {
        Properties props = new Properties();

        // Try loading from working directory first
        try (InputStream is = new FileInputStream(CONFIG_FILE)) {
            props.load(is);
            log.info("Loaded configuration from {}", CONFIG_FILE);
        } catch (IOException e) {
            log.warn("config.properties not found in working directory, trying classpath...");
            // Try classpath
            try (InputStream is = getClass().getClassLoader().getResourceAsStream(CONFIG_FILE)) {
                if (is != null) {
                    props.load(is);
                    log.info("Loaded configuration from classpath");
                } else {
                    log.warn("No config.properties found — using defaults. " +
                            "Copy config.properties.example to config.properties and update values.");
                }
            } catch (IOException ex) {
                log.error("Failed to load configuration", ex);
            }
        }

        return props;
    }
}
