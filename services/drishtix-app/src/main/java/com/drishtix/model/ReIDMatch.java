package com.drishtix.model;

import java.time.LocalDateTime;

/**
 * Value object representing a cross-camera person re-identification match.
 * <p>
 * Created when a newly extracted person embedding has high cosine similarity
 * (above threshold) with an existing embedding from a different camera,
 * indicating the same person has been spotted across multiple camera feeds.
 * </p>
 */
public class ReIDMatch {

    private final PersonEmbedding sourceEmbedding;
    private final PersonEmbedding matchedEmbedding;
    private final double similarity;
    private final LocalDateTime matchTime;

    /**
     * Creates a new ReID match event.
     *
     * @param sourceEmbedding  the newly detected person's embedding
     * @param matchedEmbedding the existing embedding that matched
     * @param similarity       the cosine similarity score (0.0 to 1.0)
     */
    public ReIDMatch(PersonEmbedding sourceEmbedding, PersonEmbedding matchedEmbedding, double similarity) {
        this.sourceEmbedding = sourceEmbedding;
        this.matchedEmbedding = matchedEmbedding;
        this.similarity = similarity;
        this.matchTime = LocalDateTime.now();
    }

    public PersonEmbedding getSourceEmbedding() {
        return sourceEmbedding;
    }

    public PersonEmbedding getMatchedEmbedding() {
        return matchedEmbedding;
    }

    /**
     * Returns the cosine similarity between the two embeddings (0.0 to 1.0).
     * Values above 0.85 typically indicate a strong match.
     */
    public double getSimilarity() {
        return similarity;
    }

    /**
     * Returns the similarity as a percentage string (e.g., "92.3%").
     */
    public String getSimilarityPercentage() {
        return String.format("%.1f%%", similarity * 100);
    }

    public LocalDateTime getMatchTime() {
        return matchTime;
    }

    /**
     * Returns the source camera ID (where the person was just detected).
     */
    public Integer getSourceCameraId() {
        return sourceEmbedding != null ? sourceEmbedding.getCameraId() : null;
    }

    /**
     * Returns the matched camera ID (where the person was previously seen).
     */
    public Integer getMatchedCameraId() {
        return matchedEmbedding != null ? matchedEmbedding.getCameraId() : null;
    }

    @Override
    public String toString() {
        return "ReIDMatch{" +
                "source=" + (sourceEmbedding != null ? sourceEmbedding.getEmbeddingId() : "null") +
                ", matched=" + (matchedEmbedding != null ? matchedEmbedding.getEmbeddingId() : "null") +
                ", similarity=" + String.format("%.3f", similarity) +
                ", time=" + matchTime + '}';
    }
}
