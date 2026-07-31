package com.drishtix.model;

import java.util.ArrayList;
import java.util.List;

/**
 * Holds multiple feature embeddings for a single target (e.g., from multiple enrolled photos)
 * and their aggregated, normalized centroid (mean vector).
 * Used for Multi-Template Centroid Matching to handle varying poses and lighting.
 */
public class TargetEmbeddings {

    public static final int MAX_TEMPLATES = 5;

    private final List<float[]> templates;
    private float[] centroid;

    public TargetEmbeddings() {
        this.templates = new ArrayList<>();
    }

    public void addTemplate(float[] embedding) {
        if (embedding != null && embedding.length > 0) {
            if (this.templates.size() >= MAX_TEMPLATES) {
                // Drop the oldest template (FIFO) to make room
                this.templates.remove(0);
            }
            this.templates.add(embedding);
            recalculateCentroid();
        }
    }

    public List<float[]> getTemplates() {
        return templates;
    }

    public float[] getCentroid() {
        return centroid;
    }

    /**
     * Recalculates the normalized centroid (mean vector) whenever a new template is added.
     * E_centroid = sum(e_i) / ||sum(e_i)||
     */
    private void recalculateCentroid() {
        if (templates.isEmpty()) {
            this.centroid = null;
            return;
        }

        int dim = templates.get(0).length;
        float[] sumVector = new float[dim];

        // Sum all templates
        for (float[] template : templates) {
            for (int i = 0; i < dim; i++) {
                sumVector[i] += template[i];
            }
        }

        // Calculate L2 norm (magnitude)
        double norm = 0.0;
        for (int i = 0; i < dim; i++) {
            norm += sumVector[i] * sumVector[i];
        }
        norm = Math.sqrt(norm);

        // Normalize
        if (norm > 0) {
            for (int i = 0; i < dim; i++) {
                sumVector[i] = (float) (sumVector[i] / norm);
            }
        }

        this.centroid = sumVector;
    }
}
