package com.drishtix.model;

/**
 * Encapsulates the Face Quality Assessment (FQA) metrics for a detected face crop.
 * Used to determine if a face is suitable for deep embedding extraction and watchlist matching.
 */
public class FaceQuality {

    private final boolean isBlurred;
    private final boolean isExtremePose;
    private final double livenessScore;
    private final double laplacianVariance;
    private final boolean isSpoofAttempt;

    public FaceQuality(boolean isBlurred, boolean isExtremePose, double livenessScore, double laplacianVariance) {
        this.isBlurred = isBlurred;
        this.isExtremePose = isExtremePose;
        this.livenessScore = livenessScore;
        this.laplacianVariance = laplacianVariance;
        this.isSpoofAttempt = livenessScore < 0.35;
    }

    public boolean isBlurred() {
        return isBlurred;
    }

    public boolean isExtremePose() {
        return isExtremePose;
    }

    public double getLivenessScore() {
        return livenessScore;
    }

    public double getLaplacianVariance() {
        return laplacianVariance;
    }

    public boolean isSpoofAttempt() {
        return isSpoofAttempt;
    }

    /**
     * @return true if the face is too degraded or positioned poorly to be matched reliably
     */
    public boolean isUnfavorable() {
        return isBlurred || isExtremePose;
    }
}
