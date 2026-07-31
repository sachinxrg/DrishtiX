package com.drishtix.model;

import org.bytedeco.opencv.opencv_core.Rect;
import org.bytedeco.opencv.opencv_video.Tracker;

/**
 * Value object holding the state of a tracked face between full inference frames.
 * <p>
 * On full-inference frames (every Nth frame), trackers are initialized from
 * YuNet detections. On intermediate frames, the tracker updates the bounding
 * box position without running the expensive DNN pipeline.
 * </p>
 */
public class TrackedFace {

    private Rect boundingBox;
    private String label;
    private int[] color;
    private Tracker tracker;
    private final int trackerId;
    private long lastInferenceFrame;
    private RecognitionResult lastResult;

    /** ID of the associated LockedTarget, or -1 if not body-locked. */
    private int lockedTargetId = -1;

    /** True if this box was derived from a KCF/CSRT tracker prediction, not live DNN inference. */
    private boolean trackerPredicted;

    /**
     * @param trackerId          unique ID for this tracked face within the current session
     * @param boundingBox        initial bounding box from YuNet detection
     * @param label              display label (e.g., "John Doe | CASE-001" or "Analyzing...")
     * @param color              BGR color for bounding box rendering
     * @param tracker            the OpenCV tracker instance (KCF/CSRT)
     * @param lastInferenceFrame the frame index at which full inference was last run
     */
    public TrackedFace(int trackerId, Rect boundingBox, String label, int[] color,
                       Tracker tracker, long lastInferenceFrame) {
        this.trackerId = trackerId;
        this.boundingBox = boundingBox;
        this.label = label;
        this.color = color;
        this.tracker = tracker;
        this.lastInferenceFrame = lastInferenceFrame;
    }

    // ==================== Getters & Setters ====================

    public Rect getBoundingBox() {
        return boundingBox;
    }

    public void setBoundingBox(Rect boundingBox) {
        this.boundingBox = boundingBox;
    }

    public String getLabel() {
        return label;
    }

    public void setLabel(String label) {
        this.label = label;
    }

    public int[] getColor() {
        return color;
    }

    public void setColor(int[] color) {
        this.color = color;
    }

    public Tracker getTracker() {
        return tracker;
    }

    public void setTracker(Tracker tracker) {
        this.tracker = tracker;
    }

    public int getTrackerId() {
        return trackerId;
    }

    public long getLastInferenceFrame() {
        return lastInferenceFrame;
    }

    public void setLastInferenceFrame(long lastInferenceFrame) {
        this.lastInferenceFrame = lastInferenceFrame;
    }

    public RecognitionResult getLastResult() {
        return lastResult;
    }

    public void setLastResult(RecognitionResult lastResult) {
        this.lastResult = lastResult;
    }

    /**
     * Returns true if this bounding box is a tracker prediction (interpolated),
     * false if it came from a live DNN inference frame.
     */
    public boolean isTrackerPredicted() {
        return trackerPredicted;
    }

    public void setTrackerPredicted(boolean trackerPredicted) {
        this.trackerPredicted = trackerPredicted;
    }

    /**
     * Returns the associated LockedTarget ID, or -1 if this track is not body-locked.
     */
    public int getLockedTargetId() {
        return lockedTargetId;
    }

    public void setLockedTargetId(int lockedTargetId) {
        this.lockedTargetId = lockedTargetId;
    }

    @Override
    public String toString() {
        return "TrackedFace{id=" + trackerId +
                ", box=" + boundingBox.x() + "," + boundingBox.y() +
                " " + boundingBox.width() + "x" + boundingBox.height() +
                ", label='" + label + "'" +
                ", predicted=" + trackerPredicted + "}";
    }
}
