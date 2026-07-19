package com.drishtix.model;

import java.time.LocalDateTime;

/**
 * Entity representing a camera source.
 * Maps to the {@code camera_sources} table in the database.
 */
public class CameraSource {

    private int cameraId;
    private String cameraName;
    private String sourceUri;
    private boolean active;
    private LocalDateTime createdAt;

    public CameraSource() {
    }

    public CameraSource(String cameraName, String sourceUri) {
        this.cameraName = cameraName;
        this.sourceUri = sourceUri;
        this.active = true;
    }

    public int getCameraId() {
        return cameraId;
    }

    public void setCameraId(int cameraId) {
        this.cameraId = cameraId;
    }

    public String getCameraName() {
        return cameraName;
    }

    public void setCameraName(String cameraName) {
        this.cameraName = cameraName;
    }

    public String getSourceUri() {
        return sourceUri;
    }

    public void setSourceUri(String sourceUri) {
        this.sourceUri = sourceUri;
    }

    public boolean isActive() {
        return active;
    }

    public void setActive(boolean active) {
        this.active = active;
    }

    public LocalDateTime getCreatedAt() {
        return createdAt;
    }

    public void setCreatedAt(LocalDateTime createdAt) {
        this.createdAt = createdAt;
    }

    /**
     * Returns the source as an integer device index if it's numeric,
     * otherwise returns -1 (indicating an RTSP/URL source).
     */
    public int getDeviceIndex() {
        try {
            return Integer.parseInt(sourceUri.trim());
        } catch (NumberFormatException e) {
            return -1;
        }
    }

    @Override
    public String toString() {
        return cameraName + " (" + sourceUri + ")";
    }
}
