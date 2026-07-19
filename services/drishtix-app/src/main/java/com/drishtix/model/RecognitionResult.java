package com.drishtix.model;

/**
 * Value object representing the result of a face recognition attempt.
 * Produced by the RecognitionService after comparing a detected face
 * against the trained LBPH model.
 */
public class RecognitionResult {

    private final int predictedLabel;
    private final double confidence;
    private final boolean matched;

    // Populated after database lookup
    private TargetRegistry matchedTarget;

    /**
     * Creates a recognition result for a matched face.
     *
     * @param predictedLabel the LBPH recognizer label that was predicted
     * @param confidence     the LBPH distance (lower = better match)
     * @param matched        true if the confidence is within the threshold
     */
    public RecognitionResult(int predictedLabel, double confidence, boolean matched) {
        this.predictedLabel = predictedLabel;
        this.confidence = confidence;
        this.matched = matched;
    }

    /**
     * Factory method for an unmatched (unknown) face.
     */
    public static RecognitionResult unknown(double confidence) {
        return new RecognitionResult(-1, confidence, false);
    }

    /**
     * Factory method for a matched face.
     */
    public static RecognitionResult matched(int label, double confidence) {
        return new RecognitionResult(label, confidence, true);
    }

    public int getPredictedLabel() {
        return predictedLabel;
    }

    /**
     * Returns the LBPH distance. Lower values indicate a better match.
     */
    public double getConfidence() {
        return confidence;
    }

    /**
     * Returns true if this face was recognized as a registered target.
     */
    public boolean isMatched() {
        return matched;
    }

    public TargetRegistry getMatchedTarget() {
        return matchedTarget;
    }

    public void setMatchedTarget(TargetRegistry matchedTarget) {
        this.matchedTarget = matchedTarget;
    }

    /**
     * Returns a human-readable confidence percentage.
     * Converts LBPH distance to an inverted percentage (higher = better).
     */
    public String getConfidencePercentage() {
        double pct = Math.max(0, 100 - (confidence * 0.5));
        return String.format("%.1f%%", pct);
    }

    @Override
    public String toString() {
        return "RecognitionResult{label=" + predictedLabel +
                ", confidence=" + confidence +
                ", matched=" + matched +
                (matchedTarget != null ? ", target=" + matchedTarget.getFullName() : "") +
                '}';
    }
}
