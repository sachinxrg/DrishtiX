package com.drishtix.model;

/**
 * Value object representing the result of a face recognition attempt.
 * Supports both LBPH distance-based and DNN cosine-similarity-based results.
 * <p>
 * LBPH mode: lower confidence = better match (distance metric)
 * DNN mode:  higher matchScore = better match (cosine similarity, 0.0–1.0)
 * </p>
 */
public class RecognitionResult {

    private final int predictedLabel;
    private final double confidence;    // LBPH distance (lower = better)
    private final double matchScore;    // DNN cosine similarity (higher = better, 0–1)
    private final boolean matched;
    private final boolean dnnMode;

    // Populated after database lookup
    private TargetRegistry matchedTarget;

    // Transport field: carries the probe embedding through the async pipeline
    // for body lock handoff (set after matchAgainstGallery, consumed by acquireBodyLock)
    private float[] probeEmbedding;

    /**
     * Creates a recognition result (legacy LBPH mode).
     */
    public RecognitionResult(int predictedLabel, double confidence, boolean matched) {
        this.predictedLabel = predictedLabel;
        this.confidence = confidence;
        this.matchScore = 0.0;
        this.matched = matched;
        this.dnnMode = false;
    }

    /**
     * Creates a recognition result (DNN mode).
     */
    private RecognitionResult(int predictedLabel, double confidence, double matchScore,
                              boolean matched, boolean dnnMode) {
        this.predictedLabel = predictedLabel;
        this.confidence = confidence;
        this.matchScore = matchScore;
        this.matched = matched;
        this.dnnMode = dnnMode;
    }

    /**
     * Factory method for an unmatched (unknown) face.
     */
    public static RecognitionResult unknown(double confidence) {
        return new RecognitionResult(-1, confidence, false);
    }

    /**
     * Factory method for an unmatched face in DNN mode.
     */
    public static RecognitionResult unknownDnn(double bestScore) {
        return new RecognitionResult(-1, 0, bestScore, false, true);
    }

    /**
     * Factory method for a matched face (LBPH mode).
     */
    public static RecognitionResult matched(int label, double confidence) {
        return new RecognitionResult(label, confidence, true);
    }

    /**
     * Factory method for a matched face (DNN mode).
     *
     * @param targetId        the matched target's ID
     * @param cosineSimilarity the cosine similarity score (0.0–1.0, higher = better)
     */
    public static RecognitionResult matchedDnn(int targetId, double cosineSimilarity) {
        return new RecognitionResult(targetId, 0, cosineSimilarity, true, true);
    }

    public int getPredictedLabel() {
        return predictedLabel;
    }

    /**
     * Returns the LBPH distance (legacy mode). Lower values indicate a better match.
     */
    public double getConfidence() {
        return confidence;
    }

    /**
     * Returns the DNN cosine similarity score (0.0–1.0). Higher = better match.
     */
    public double getMatchScore() {
        return matchScore;
    }

    /**
     * Returns true if this face was recognized as a registered target.
     */
    public boolean isMatched() {
        return matched;
    }

    /**
     * Returns true if this result was produced by the DNN pipeline.
     */
    public boolean isDnnMode() {
        return dnnMode;
    }

    public TargetRegistry getMatchedTarget() {
        return matchedTarget;
    }

    public void setMatchedTarget(TargetRegistry matchedTarget) {
        this.matchedTarget = matchedTarget;
    }

    /**
     * Returns the probe SFace embedding that produced this result.
     * Used for body lock handoff (Facial-to-Spatial Tracking).
     */
    public float[] getProbeEmbedding() {
        return probeEmbedding;
    }

    public void setProbeEmbedding(float[] probeEmbedding) {
        this.probeEmbedding = probeEmbedding;
    }

    /**
     * Returns the similarity score (DNN: matchScore, LBPH: inverted confidence).
     * Convenience method for body lock fusion weighting.
     */
    public double getSimilarity() {
        return dnnMode ? matchScore : Math.max(0, (100 - confidence) / 100.0);
    }

    /**
     * Returns a human-readable confidence percentage.
     * <p>
     * DNN mode: cosine similarity × 100 (higher = better)
     * LBPH mode: inverted distance (higher = better)
     * </p>
     */
    public String getConfidencePercentage() {
        if (dnnMode) {
            return String.format("%.1f%%", matchScore * 100.0);
        }
        double pct = Math.max(0, 100 - (confidence * 0.5));
        return String.format("%.1f%%", pct);
    }

    @Override
    public String toString() {
        if (dnnMode) {
            return "RecognitionResult{DNN, targetId=" + predictedLabel +
                    ", similarity=" + String.format("%.3f", matchScore) +
                    ", matched=" + matched +
                    (matchedTarget != null ? ", target=" + matchedTarget.getFullName() : "") +
                    '}';
        }
        return "RecognitionResult{LBPH, label=" + predictedLabel +
                ", confidence=" + confidence +
                ", matched=" + matched +
                (matchedTarget != null ? ", target=" + matchedTarget.getFullName() : "") +
                '}';
    }
}
