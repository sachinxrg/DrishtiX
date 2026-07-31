package com.drishtix.model;

import com.drishtix.util.AppConstants;
import org.bytedeco.opencv.opencv_core.Rect;
import org.bytedeco.opencv.opencv_tracking.TrackerCSRT;

/**
 * Represents a positively identified target with an active body lock.
 * <p>
 * Created when SFace confirms a target identity above threshold. The body lock
 * persists across frames using a CSRT tracker initialized on the target's
 * expanded torso region, maintaining the bounding box and alert label even
 * when YuNet loses the face (head turned, back to camera).
 * </p>
 * <p>
 * Implements dynamic confidence fusion: when the face is visible, facial
 * confidence dominates (α=0.8). When the face is lost, body appearance
 * (OSNet embedding) takes over (β=1.0). The lock is released when CSRT
 * loses the target, fused confidence drops below threshold, or the maximum
 * lock duration expires without face re-confirmation.
 * </p>
 */
public class LockedTarget {

    private final int targetId;
    private final String label;
    private final int[] color;

    // Persistent CSRT tracker for body/torso tracking
    private TrackerCSRT bodyTracker;
    private Rect bodyBox;

    // Embeddings for fusion scoring
    private float[] faceEmbedding;    // Last SFace embedding (128-dim), null when face lost
    private float[] bodyEmbedding;    // Last OSNet embedding (512-dim)

    // Confidence scores
    private double lastFaceSimilarity;  // Last SFace match score
    private double lastBodySimilarity;  // Last OSNet match score
    private double fusedConfidence;     // α·face + β·body

    // Frame tracking
    private final long lockAcquiredFrame;
    private long lastFaceVisibleFrame;
    private long lastBodyVerifyFrame;
    private int consecutiveLowConfFrames;

    // State
    private boolean faceCurrentlyVisible;
    private boolean active;

    /**
     * Creates a new body lock for a confirmed target.
     *
     * @param targetId         the database target ID
     * @param label            display label (e.g., "John Doe | CASE-001")
     * @param color            BGR color for bounding box
     * @param bodyTracker      initialized CSRT tracker on expanded torso region
     * @param bodyBox          the expanded torso bounding box
     * @param faceEmbedding    the SFace embedding that confirmed identity
     * @param faceSimilarity   the SFace match score at time of lock
     * @param currentFrame     the frame index when the lock was acquired
     */
    public LockedTarget(int targetId, String label, int[] color,
                        TrackerCSRT bodyTracker, Rect bodyBox,
                        float[] faceEmbedding, double faceSimilarity,
                        long currentFrame) {
        this.targetId = targetId;
        this.label = label;
        this.color = color;
        this.bodyTracker = bodyTracker;
        this.bodyBox = bodyBox;
        this.faceEmbedding = faceEmbedding;
        this.lastFaceSimilarity = faceSimilarity;
        this.fusedConfidence = faceSimilarity;
        this.lockAcquiredFrame = currentFrame;
        this.lastFaceVisibleFrame = currentFrame;
        this.lastBodyVerifyFrame = currentFrame;
        this.faceCurrentlyVisible = true;
        this.active = true;
        this.consecutiveLowConfFrames = 0;
    }

    /**
     * Computes the dynamic fused confidence based on face visibility state.
     * <p>
     * Weighting transitions:
     * - Face visible:        α=0.8, β=0.2
     * - Face lost < 30 frames (grace period): α=0.4, β=0.6
     * - Face lost ≥ 30 frames: α=0.0, β=1.0
     * </p>
     *
     * @param currentFrame the current frame index
     */
    public void recomputeFusedConfidence(long currentFrame) {
        long framesSinceFace = currentFrame - lastFaceVisibleFrame;
        double alpha, beta;

        if (faceCurrentlyVisible) {
            alpha = AppConstants.FUSION_ALPHA_FACE_VISIBLE;
            beta = AppConstants.FUSION_BETA_FACE_VISIBLE;
        } else if (framesSinceFace < AppConstants.BODY_LOCK_GRACE_FRAMES) {
            alpha = AppConstants.FUSION_ALPHA_GRACE;
            beta = AppConstants.FUSION_BETA_GRACE;
        } else {
            alpha = AppConstants.FUSION_ALPHA_BODY_ONLY;
            beta = AppConstants.FUSION_BETA_BODY_ONLY;
        }

        this.fusedConfidence = alpha * lastFaceSimilarity + beta * lastBodySimilarity;

        // Track consecutive low-confidence frames
        if (fusedConfidence < AppConstants.BODY_LOCK_MIN_CONFIDENCE) {
            consecutiveLowConfFrames++;
        } else {
            consecutiveLowConfFrames = 0;
        }
    }

    /**
     * Determines whether this lock should be released.
     *
     * @param currentFrame the current frame index
     * @return true if the lock should be released
     */
    public boolean shouldRelease(long currentFrame) {
        if (!active) return true;

        // Condition 1: Exceeded max lock duration without face re-confirmation
        long lockDuration = currentFrame - lockAcquiredFrame;
        long framesSinceFace = currentFrame - lastFaceVisibleFrame;
        if (lockDuration > AppConstants.BODY_LOCK_MAX_FRAMES && framesSinceFace > AppConstants.BODY_LOCK_GRACE_FRAMES) {
            return true;
        }

        // Condition 2: Consecutive low-confidence frames exceeded threshold
        if (consecutiveLowConfFrames >= AppConstants.BODY_LOCK_LOW_CONF_FRAMES) {
            return true;
        }

        return false;
    }

    /**
     * Returns whether the OSNet body embedding should be re-verified on this frame.
     */
    public boolean needsBodyReverification(long currentFrame) {
        return !faceCurrentlyVisible &&
                (currentFrame - lastBodyVerifyFrame) >= AppConstants.BODY_LOCK_REVERIFY_INTERVAL;
    }

    /**
     * Returns the label with a [BODY] suffix when face is not visible.
     */
    public String getDisplayLabel() {
        if (faceCurrentlyVisible) {
            return label;
        }
        return label + " [BODY]";
    }

    /**
     * Returns the display color — uses original target color when face is visible,
     * amber/orange when in body-only mode.
     */
    public int[] getDisplayColor() {
        if (faceCurrentlyVisible) {
            return color;
        }
        return AppConstants.COLOR_BODY_LOCK_BGR;
    }

    // ==================== Face Re-confirmation ====================

    /**
     * Called when YuNet re-detects the face within this lock's spatial region.
     * Refreshes face state and resets the face-lost counter.
     */
    public void reconfirmFace(float[] newFaceEmbedding, double similarity, long currentFrame) {
        this.faceEmbedding = newFaceEmbedding;
        this.lastFaceSimilarity = similarity;
        this.lastFaceVisibleFrame = currentFrame;
        this.faceCurrentlyVisible = true;
        this.consecutiveLowConfFrames = 0;
    }

    /**
     * Marks the face as no longer visible (YuNet lost the landmarks).
     */
    public void markFaceLost() {
        this.faceCurrentlyVisible = false;
    }

    // ==================== Getters & Setters ====================

    public int getTargetId() { return targetId; }
    public String getLabel() { return label; }
    public int[] getColor() { return color; }
    public TrackerCSRT getBodyTracker() { return bodyTracker; }

    public Rect getBodyBox() { return bodyBox; }
    public void setBodyBox(Rect bodyBox) { this.bodyBox = bodyBox; }

    public float[] getFaceEmbedding() { return faceEmbedding; }
    public float[] getBodyEmbedding() { return bodyEmbedding; }
    public void setBodyEmbedding(float[] bodyEmbedding) { this.bodyEmbedding = bodyEmbedding; }

    public double getLastFaceSimilarity() { return lastFaceSimilarity; }
    public double getLastBodySimilarity() { return lastBodySimilarity; }
    public void setLastBodySimilarity(double sim) { this.lastBodySimilarity = sim; }

    public double getFusedConfidence() { return fusedConfidence; }

    public long getLockAcquiredFrame() { return lockAcquiredFrame; }
    public long getLastFaceVisibleFrame() { return lastFaceVisibleFrame; }
    public long getLastBodyVerifyFrame() { return lastBodyVerifyFrame; }
    public void setLastBodyVerifyFrame(long frame) { this.lastBodyVerifyFrame = frame; }

    public boolean isFaceCurrentlyVisible() { return faceCurrentlyVisible; }
    public boolean isActive() { return active; }
    public void setActive(boolean active) { this.active = active; }

    @Override
    public String toString() {
        return "LockedTarget{id=" + targetId +
                ", label='" + label + '\'' +
                ", faceVisible=" + faceCurrentlyVisible +
                ", fused=" + String.format("%.3f", fusedConfidence) +
                ", active=" + active + '}';
    }
}
