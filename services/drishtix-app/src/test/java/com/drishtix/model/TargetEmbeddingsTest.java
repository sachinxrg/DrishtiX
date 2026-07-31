package com.drishtix.model;

import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;

import java.util.List;

public class TargetEmbeddingsTest {

    @Test
    public void testAddTemplate_AddsSuccessfully() {
        TargetEmbeddings target = new TargetEmbeddings();
        float[] template1 = {0.1f, 0.2f, 0.3f};
        float[] template2 = {0.4f, 0.5f, 0.6f};

        target.addTemplate(template1);
        target.addTemplate(template2);

        List<float[]> templates = target.getTemplates();
        assertEquals(2, templates.size());
        assertArrayEquals(template1, templates.get(0));
        assertArrayEquals(template2, templates.get(1));
    }

    @Test
    public void testAddTemplate_IgnoresNull() {
        TargetEmbeddings target = new TargetEmbeddings();
        target.addTemplate(null);
        assertTrue(target.getTemplates().isEmpty());
    }

    @Test
    public void testAddTemplate_MaxLimit() {
        TargetEmbeddings target = new TargetEmbeddings();
        for (int i = 0; i < 10; i++) {
            target.addTemplate(new float[]{0.1f * i});
        }
        
        // Assuming MAX_TEMPLATES is 5, as discussed in the blueprint
        // Even if we add 10, it should only hold 5
        assertEquals(5, target.getTemplates().size());
    }

    @Test
    public void testCentroid_CorrectCalculation() {
        TargetEmbeddings target = new TargetEmbeddings();
        float[] template1 = {1.0f, 2.0f, 3.0f};
        float[] template2 = {3.0f, 2.0f, 1.0f};

        target.addTemplate(template1);
        target.addTemplate(template2);

        float[] centroid = target.getCentroid();
        assertNotNull(centroid);
        assertEquals(3, centroid.length);
        
        // Sum vector before norm: (4, 4, 4)
        // Norm: sqrt(16 + 16 + 16) = sqrt(48) = 6.9282
        // Normalized values: 4 / 6.9282 = 0.57735
        assertEquals(0.57735f, centroid[0], 0.001);
        assertEquals(0.57735f, centroid[1], 0.001);
        assertEquals(0.57735f, centroid[2], 0.001);
    }
}
