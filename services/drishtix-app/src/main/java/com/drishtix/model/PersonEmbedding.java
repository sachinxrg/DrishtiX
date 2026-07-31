package com.drishtix.model;

import java.time.LocalDateTime;
import java.util.Arrays;

/**
 * Entity representing a person's feature embedding extracted by the ReID service.
 * Maps to the {@code person_embeddings} collection in MongoDB.
 * <p>
 * Each embedding is a 512-dimensional vector capturing body shape and clothing
 * features, used for cross-camera person re-identification via cosine similarity.
 * </p>
 */
public class PersonEmbedding {

    private long embeddingId;
    private Integer targetId;       // nullable — unknown persons have no target
    private Integer cameraId;
    private double[] embedding;     // 512-dimensional feature vector
    private String snapshotPath;
    private LocalDateTime timestamp;

    // Transient fields for display
    private String cameraName;
    private String targetName;

    public PersonEmbedding() {
    }

    /**
     * Constructor for creating a new embedding record.
     *
     * @param targetId     the matched target ID, or null for unknown persons
     * @param cameraId     the camera that captured this sighting
     * @param embedding    the 512-dimensional feature vector
     * @param snapshotPath path to the person crop image
     */
    public PersonEmbedding(Integer targetId, Integer cameraId, double[] embedding, String snapshotPath) {
        this.targetId = targetId;
        this.cameraId = cameraId;
        this.embedding = embedding;
        this.snapshotPath = snapshotPath;
        this.timestamp = LocalDateTime.now();
    }

    // ==================== Getters & Setters ====================

    public long getEmbeddingId() {
        return embeddingId;
    }

    public void setEmbeddingId(long embeddingId) {
        this.embeddingId = embeddingId;
    }

    public Integer getTargetId() {
        return targetId;
    }

    public void setTargetId(Integer targetId) {
        this.targetId = targetId;
    }

    public Integer getCameraId() {
        return cameraId;
    }

    public void setCameraId(Integer cameraId) {
        this.cameraId = cameraId;
    }

    public double[] getEmbedding() {
        return embedding;
    }

    public void setEmbedding(double[] embedding) {
        this.embedding = embedding;
    }

    public String getSnapshotPath() {
        return snapshotPath;
    }

    public void setSnapshotPath(String snapshotPath) {
        this.snapshotPath = snapshotPath;
    }

    public LocalDateTime getTimestamp() {
        return timestamp;
    }

    public void setTimestamp(LocalDateTime timestamp) {
        this.timestamp = timestamp;
    }

    public String getCameraName() {
        return cameraName;
    }

    public void setCameraName(String cameraName) {
        this.cameraName = cameraName;
    }

    public String getTargetName() {
        return targetName;
    }

    public void setTargetName(String targetName) {
        this.targetName = targetName;
    }

    /**
     * Returns the dimensionality of the embedding vector.
     */
    public int getDimensions() {
        return embedding != null ? embedding.length : 0;
    }

    @Override
    public String toString() {
        return "PersonEmbedding{id=" + embeddingId +
                ", targetId=" + targetId +
                ", cameraId=" + cameraId +
                ", dims=" + getDimensions() +
                ", time=" + timestamp + '}';
    }
}
