package com.drishtix.model;

/**
 * Unified data transfer object representing a scraped wanted/missing person profile.
 * <p>
 * Used by all three ingestion scrapers (FBI, CBI, TrackChild) as a common
 * intermediate format before registration into the target_registry.
 * </p>
 */
public class WantedProfile {

    /**
     * Source agency identifier.
     */
    public enum SourceAgency {
        FBI, CBI, TRACKCHILD
    }

    private SourceAgency sourceAgency;
    private String externalId;       // Unique ID from the source (e.g., FBI UID, CBI case ID)
    private String fullName;
    private String caseNumber;
    private String description;
    private String imageUrl;         // Remote URL of the facial image
    private String localImagePath;   // Local path after download
    private TargetCategory category; // CRIMINAL or MISSING_PERSON

    public WantedProfile() {
    }

    public WantedProfile(SourceAgency sourceAgency, String externalId, String fullName,
                         String caseNumber, String description, String imageUrl,
                         TargetCategory category) {
        this.sourceAgency = sourceAgency;
        this.externalId = externalId;
        this.fullName = fullName;
        this.caseNumber = caseNumber;
        this.description = description;
        this.imageUrl = imageUrl;
        this.category = category;
    }

    // ==================== Getters & Setters ====================

    public SourceAgency getSourceAgency() {
        return sourceAgency;
    }

    public void setSourceAgency(SourceAgency sourceAgency) {
        this.sourceAgency = sourceAgency;
    }

    public String getExternalId() {
        return externalId;
    }

    public void setExternalId(String externalId) {
        this.externalId = externalId;
    }

    public String getFullName() {
        return fullName;
    }

    public void setFullName(String fullName) {
        this.fullName = fullName;
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

    public String getImageUrl() {
        return imageUrl;
    }

    public void setImageUrl(String imageUrl) {
        this.imageUrl = imageUrl;
    }

    public String getLocalImagePath() {
        return localImagePath;
    }

    public void setLocalImagePath(String localImagePath) {
        this.localImagePath = localImagePath;
    }

    public TargetCategory getCategory() {
        return category;
    }

    public void setCategory(TargetCategory category) {
        this.category = category;
    }

    @Override
    public String toString() {
        return "WantedProfile{" +
                "source=" + sourceAgency +
                ", id='" + externalId + '\'' +
                ", name='" + fullName + '\'' +
                ", case='" + caseNumber + '\'' +
                ", category=" + category +
                '}';
    }
}
