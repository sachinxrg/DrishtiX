package com.drishtix.model;

import java.time.LocalDateTime;

/**
 * Entity representing an individual photo associated with a target.
 * Maps to the {@code target_images} table in the database.
 * Supports up to 5 photos per target for improved recognition accuracy.
 */
public class TargetImage {

    private int imageId;
    private int targetId;
    private String imagePath;
    private String templatePath;
    private int imageOrder;
    private LocalDateTime uploadedAt;

    public TargetImage() {
    }

    public TargetImage(int targetId, String imagePath, String templatePath, int imageOrder) {
        this.targetId = targetId;
        this.imagePath = imagePath;
        this.templatePath = templatePath;
        this.imageOrder = imageOrder;
    }

    public int getImageId() {
        return imageId;
    }

    public void setImageId(int imageId) {
        this.imageId = imageId;
    }

    public int getTargetId() {
        return targetId;
    }

    public void setTargetId(int targetId) {
        this.targetId = targetId;
    }

    public String getImagePath() {
        return imagePath;
    }

    public void setImagePath(String imagePath) {
        this.imagePath = imagePath;
    }

    public String getTemplatePath() {
        return templatePath;
    }

    public void setTemplatePath(String templatePath) {
        this.templatePath = templatePath;
    }

    public int getImageOrder() {
        return imageOrder;
    }

    public void setImageOrder(int imageOrder) {
        this.imageOrder = imageOrder;
    }

    public LocalDateTime getUploadedAt() {
        return uploadedAt;
    }

    public void setUploadedAt(LocalDateTime uploadedAt) {
        this.uploadedAt = uploadedAt;
    }

    @Override
    public String toString() {
        return "TargetImage{imageId=" + imageId + ", targetId=" + targetId +
                ", imageOrder=" + imageOrder + '}';
    }
}
