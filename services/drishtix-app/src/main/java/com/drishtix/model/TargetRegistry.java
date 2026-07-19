package com.drishtix.model;

import java.time.LocalDateTime;

/**
 * Entity representing a registered target in the watchlist.
 * Maps to the {@code target_registry} table in the database.
 */
public class TargetRegistry {

    private int targetId;
    private String fullName;
    private TargetCategory category;
    private String caseNumber;
    private String description;
    private String profileImagePath;
    private boolean active;
    private int recognizerLabel;
    private LocalDateTime createdAt;
    private LocalDateTime updatedAt;

    /** Default constructor for DAO hydration. */
    public TargetRegistry() {
    }

    /**
     * Constructor for creating a new target (before DB insertion).
     */
    public TargetRegistry(String fullName, TargetCategory category, String caseNumber,
                          String description, String profileImagePath, int recognizerLabel) {
        this.fullName = fullName;
        this.category = category;
        this.caseNumber = caseNumber;
        this.description = description;
        this.profileImagePath = profileImagePath;
        this.recognizerLabel = recognizerLabel;
        this.active = true;
    }

    // ==================== Getters & Setters ====================

    public int getTargetId() {
        return targetId;
    }

    public void setTargetId(int targetId) {
        this.targetId = targetId;
    }

    public String getFullName() {
        return fullName;
    }

    public void setFullName(String fullName) {
        this.fullName = fullName;
    }

    public TargetCategory getCategory() {
        return category;
    }

    public void setCategory(TargetCategory category) {
        this.category = category;
    }

    public String getCaseNumber() {
        return caseNumber;
    }

    public void setCaseNumber(String caseNumber) {
        this.caseNumber = caseNumber;
    }

    public String getDescription() {
        return description;
    }

    public void setDescription(String description) {
        this.description = description;
    }

    public String getProfileImagePath() {
        return profileImagePath;
    }

    public void setProfileImagePath(String profileImagePath) {
        this.profileImagePath = profileImagePath;
    }

    public boolean isActive() {
        return active;
    }

    public void setActive(boolean active) {
        this.active = active;
    }

    public int getRecognizerLabel() {
        return recognizerLabel;
    }

    public void setRecognizerLabel(int recognizerLabel) {
        this.recognizerLabel = recognizerLabel;
    }

    public LocalDateTime getCreatedAt() {
        return createdAt;
    }

    public void setCreatedAt(LocalDateTime createdAt) {
        this.createdAt = createdAt;
    }

    public LocalDateTime getUpdatedAt() {
        return updatedAt;
    }

    public void setUpdatedAt(LocalDateTime updatedAt) {
        this.updatedAt = updatedAt;
    }

    @Override
    public String toString() {
        return "TargetRegistry{" +
                "targetId=" + targetId +
                ", fullName='" + fullName + '\'' +
                ", category=" + category +
                ", caseNumber='" + caseNumber + '\'' +
                ", active=" + active +
                ", recognizerLabel=" + recognizerLabel +
                '}';
    }
}
