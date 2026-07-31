package com.drishtix.dao;

import com.drishtix.model.TargetCategory;
import com.drishtix.model.TargetRegistry;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Disabled;
import org.junit.jupiter.api.Test;

import java.util.Optional;

import static org.junit.jupiter.api.Assertions.*;

@Disabled("Requires Docker for Testcontainers. Edge node does not have Docker.")
public class TargetDAOTest extends DatabaseTestConfig {

    private TargetDAO targetDAO;

    @BeforeEach
    public void setupDAO() {
        targetDAO = new TargetDAO();
        // Clear targets collection before each test
        DatabaseManager.getInstance().getCollection("targets").drop();
        DatabaseManager.getInstance().getCollection("counters").drop();
    }

    @Test
    public void testInsertAndFindById() {
        TargetRegistry target = new TargetRegistry();
        target.setFullName("John Doe");
        target.setCategory(TargetCategory.CRIMINAL);
        target.setCaseNumber("CASE-123");
        target.setRecognizerLabel(1);

        int id = targetDAO.insert(target);
        assertTrue(id > 0);

        Optional<TargetRegistry> retrieved = targetDAO.findById(id);
        assertTrue(retrieved.isPresent());
        assertEquals("John Doe", retrieved.get().getFullName());
        assertEquals(TargetCategory.CRIMINAL, retrieved.get().getCategory());
        assertEquals("CASE-123", retrieved.get().getCaseNumber());
    }

    @Test
    public void testDeactivate() {
        TargetRegistry target = new TargetRegistry();
        target.setFullName("Jane Doe");
        target.setCategory(TargetCategory.MISSING_PERSON);
        int id = targetDAO.insert(target);

        targetDAO.deactivate(id);

        Optional<TargetRegistry> retrieved = targetDAO.findById(id);
        assertTrue(retrieved.isPresent());
        assertFalse(retrieved.get().isActive());
    }

    @Test
    public void testNextRecognizerLabel() {
        assertEquals(1, targetDAO.getNextRecognizerLabel());

        TargetRegistry target = new TargetRegistry();
        target.setFullName("Test Target");
        target.setRecognizerLabel(10);
        targetDAO.insert(target);

        assertEquals(11, targetDAO.getNextRecognizerLabel());
    }
}
