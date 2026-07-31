package com.drishtix.util;

/**
 * Mathematical utility for vector operations used in Person Re-Identification.
 * <p>
 * Provides cosine similarity computation for comparing 512-dimensional
 * feature embeddings extracted by the OSNet model.
 * </p>
 */
public final class VectorMathUtil {

    private VectorMathUtil() {
        // Utility class — no instantiation
    }

    /**
     * Computes the cosine similarity between two vectors.
     * <p>
     * Cosine similarity measures the angle between two vectors in high-dimensional space.
     * A value of 1.0 means identical direction (same person), 0.0 means orthogonal
     * (completely different), and -1.0 means opposite direction.
     * </p>
     * <p>
     * For person ReID, a threshold of 0.85 (85%) is typically used to declare a match.
     * </p>
     *
     * @param a first embedding vector
     * @param b second embedding vector
     * @return cosine similarity in range [-1.0, 1.0]
     * @throws IllegalArgumentException if vectors are null or have different dimensions
     */
    public static double cosineSimilarity(double[] a, double[] b) {
        if (a == null || b == null) {
            throw new IllegalArgumentException("Vectors must not be null");
        }
        if (a.length != b.length) {
            throw new IllegalArgumentException(
                    "Vector dimensions must match: " + a.length + " vs " + b.length);
        }
        if (a.length == 0) {
            throw new IllegalArgumentException("Vectors must not be empty");
        }

        double dotProduct = 0.0;
        double normA = 0.0;
        double normB = 0.0;

        for (int i = 0; i < a.length; i++) {
            dotProduct += a[i] * b[i];
            normA += a[i] * a[i];
            normB += b[i] * b[i];
        }

        double denominator = Math.sqrt(normA) * Math.sqrt(normB);
        if (denominator == 0.0) {
            return 0.0; // Zero vector — no meaningful similarity
        }

        return dotProduct / denominator;
    }

    /**
     * Finds the index of the most similar embedding in a list of candidates.
     *
     * @param query      the query embedding to compare
     * @param candidates array of candidate embeddings
     * @param threshold  minimum similarity required for a match (e.g., 0.85)
     * @return the index of the best match, or -1 if no match exceeds the threshold
     */
    public static int findBestMatch(double[] query, double[][] candidates, double threshold) {
        if (query == null || candidates == null || candidates.length == 0) {
            return -1;
        }

        int bestIndex = -1;
        double bestSimilarity = threshold; // Only consider matches above threshold

        for (int i = 0; i < candidates.length; i++) {
            if (candidates[i] == null || candidates[i].length != query.length) {
                continue;
            }
            double similarity = cosineSimilarity(query, candidates[i]);
            if (similarity > bestSimilarity) {
                bestSimilarity = similarity;
                bestIndex = i;
            }
        }

        return bestIndex;
    }
}
