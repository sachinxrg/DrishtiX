package com.drishtix.dao;

import com.mongodb.client.MongoClient;
import com.mongodb.client.MongoClients;
import com.mongodb.client.MongoDatabase;
import org.junit.jupiter.api.AfterAll;
import org.junit.jupiter.api.BeforeAll;
import org.testcontainers.containers.MongoDBContainer;
import org.testcontainers.junit.jupiter.Container;
import org.testcontainers.junit.jupiter.Testcontainers;

import java.lang.reflect.Field;

/**
 * Base configuration class for database tests.
 * Uses Testcontainers to spin up an ephemeral MongoDB instance.
 * Replaces the singleton instance in DatabaseManager via reflection.
 */
@Testcontainers
public abstract class DatabaseTestConfig {

    @Container
    protected static final MongoDBContainer mongoDBContainer = new MongoDBContainer("mongo:5.1.0")
            .withExposedPorts(27017);

    protected static MongoClient mongoClient;
    protected static MongoDatabase database;

    @BeforeAll
    public static void setUpDatabase() throws Exception {
        // Create client connecting to the test container
        mongoClient = MongoClients.create(mongoDBContainer.getReplicaSetUrl());
        database = mongoClient.getDatabase("drishtix_test_db");

        // Use reflection to overwrite the singleton fields in DatabaseManager
        DatabaseManager dbManager = DatabaseManager.getInstance();

        Field clientField = DatabaseManager.class.getDeclaredField("mongoClient");
        clientField.setAccessible(true);
        clientField.set(dbManager, mongoClient);

        Field dbField = DatabaseManager.class.getDeclaredField("database");
        dbField.setAccessible(true);
        dbField.set(dbManager, database);
        
        // Clear old test data
        dbManager.clearSystemData();
    }

    @AfterAll
    public static void tearDownDatabase() {
        if (mongoClient != null) {
            mongoClient.close();
        }
    }
}
