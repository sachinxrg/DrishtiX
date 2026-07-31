package com.drishtix.service;

import com.drishtix.model.FaceDetection;
import com.drishtix.model.LockedTarget;
import com.drishtix.model.TrackedFace;
import com.drishtix.util.AppConstants;
import org.bytedeco.opencv.opencv_core.Mat;
import org.bytedeco.opencv.opencv_core.Rect;
import org.bytedeco.opencv.opencv_video.Tracker;
import org.bytedeco.opencv.opencv_tracking.TrackerCSRT;
import org.bytedeco.opencv.opencv_tracking.TrackerKCF;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import java.util.concurrent.atomic.AtomicInteger;

/**
 * Manages a pool of lightweight OpenCV object trackers (KCF/CSRT) for
 * inter-frame face tracking between full DNN inference cycles.
 * <p>
 * On full-inference frames (every Nth frame): trackers are initialized
 * from YuNet detection results. On intermediate frames: trackers
 * extrapolate bounding box positions without running the heavy DNN pipeline,
 * maintaining smooth visual tracking at 30+ FPS.
 * </p>
 * <p>
 * KCF (~0.3ms per update) is preferred for edge laptop thermal constraints.
 * CSRT (~1.5ms) is available for higher accuracy when needed.
 * </p>
 * <p>
 * Thread safety: This class is NOT thread-safe. It must be called from
 * a single thread (the video capture thread), consistent with the existing
 * DashboardController architecture.
 * </p>
 */
public class FaceTrackingManager {

    private static final Logger log = LoggerFactory.getLogger(FaceTrackingManager.class);

    private final List<TrackedFace> activeTracks = new ArrayList<>();
    private final List<LockedTarget> lockedTargets = new ArrayList<>();
    private final AtomicInteger nextTrackerId = new AtomicInteger(0);
    private final AtomicInteger nextLockId = new AtomicInteger(0);

    /** The tracker type to use: "KCF" or "CSRT" */
    private String trackerType;

    public FaceTrackingManager() {
        this.trackerType = ConfigurationService.getInstance().getTrackerType();
        log.info("FaceTrackingManager initialized with tracker type: {}", trackerType);
    }

    /**
     * Initializes (or reinitializes) trackers from fresh YuNet detection results.
     * Called on every Nth frame when full DNN inference is performed.
     * <p>
     * Existing trackers are discarded and replaced with new ones based on the
     * latest detection results. Each tracker is initialized with the detection
     * bounding box on the current frame.
     * </p>
     *
     * @param frame         the current video frame (used to initialize trackers)
     * @param detections    the list of face detections from YuNet
     * @param currentFrame  the current frame index
     */
    public void initTrackers(Mat frame, List<FaceDetection> detections, long currentFrame) {
        // Snapshot previous labels BEFORE clearing — enables IoU-based label carry-over
        List<TrackedFace> previousTracks = new ArrayList<>(activeTracks);

        // Release old trackers
        clearTrackers();

        for (FaceDetection detection : detections) {
            try {
                Rect box = detection.getBoundingBox();

                // Validate bounding box is within frame bounds
                if (box.x() < 0 || box.y() < 0 ||
                        box.x() + box.width() > frame.cols() ||
                        box.y() + box.height() > frame.rows() ||
                        box.width() <= 0 || box.height() <= 0) {
                    continue;
                }

                // Create a new tracker
                Tracker tracker = createTracker();
                if (tracker == null) continue;

                // Initialize the tracker with the detection bounding box (Rect, not Rect2d)
                tracker.init(frame, box);

                // Carry over labels from spatially-overlapping previous tracks (eliminates flicker)
                TrackedFace bestPrev = findBestOverlap(previousTracks, box);
                String initialLabel = (bestPrev != null && !"Analyzing...".equals(bestPrev.getLabel()))
                        ? bestPrev.getLabel() : "Analyzing...";
                int[] initialColor = (bestPrev != null && !"Analyzing...".equals(bestPrev.getLabel()))
                        ? bestPrev.getColor() : AppConstants.COLOR_UNKNOWN_BGR;

                TrackedFace trackedFace = new TrackedFace(
                        nextTrackerId.getAndIncrement(),
                        box,
                        initialLabel,
                        initialColor,
                        tracker,
                        currentFrame
                );

                activeTracks.add(trackedFace);

            } catch (Exception e) {
                log.debug("Failed to initialize tracker for detection: {}", e.getMessage());
            }
        }

        log.debug("Initialized {} trackers from {} detections (carried over {} labels)",
                activeTracks.size(), detections.size(),
                activeTracks.stream().filter(t -> !"Analyzing...".equals(t.getLabel())).count());
    }

    /**
     * Updates all active trackers on the current frame without running DNN inference.
     * Called on intermediate frames (non-Nth frames).
     * <p>
     * Each tracker predicts the new bounding box position based on the frame content.
     * Failed trackers (lost targets) are removed from the active pool.
     * </p>
     *
     * @param frame the current video frame
     * @return list of currently tracked faces with updated bounding boxes
     */
    public List<TrackedFace> updateTrackers(Mat frame) {
        if (activeTracks.isEmpty()) {
            return Collections.emptyList();
        }

        List<TrackedFace> toRemove = new ArrayList<>();

        for (TrackedFace tracked : activeTracks) {
            try {
                Tracker tracker = tracked.getTracker();
                if (tracker == null) {
                    toRemove.add(tracked);
                    continue;
                }

                // OpenCV 4.9/JavaCV 1.5.10: Tracker.update() uses Rect (not Rect2d)
                Rect updatedBox = new Rect();
                boolean success = tracker.update(frame, updatedBox);

                if (success) {
                    // Update the bounding box with the tracker's prediction
                    int x = Math.max(0, updatedBox.x());
                    int y = Math.max(0, updatedBox.y());
                    int w = updatedBox.width();
                    int h = updatedBox.height();

                    // Clamp to frame boundaries
                    if (x + w > frame.cols()) w = frame.cols() - x;
                    if (y + h > frame.rows()) h = frame.rows() - y;

                    if (w > 0 && h > 0) {
                        tracked.setBoundingBox(new Rect(x, y, w, h));
                        tracked.setTrackerPredicted(true); // Mark as interpolated, not live DNN
                    } else {
                        toRemove.add(tracked);
                    }
                } else {
                    // Tracker lost the target
                    toRemove.add(tracked);
                }

            } catch (Exception e) {
                log.debug("Tracker update failed for track {}: {}", tracked.getTrackerId(), e.getMessage());
                toRemove.add(tracked);
            }
        }

        // Remove failed trackers
        activeTracks.removeAll(toRemove);

        return Collections.unmodifiableList(new ArrayList<>(activeTracks));
    }

    /**
     * Updates the label and color for a tracked face after recognition completes.
     * Called asynchronously when the SFace embedding result arrives.
     *
     * @param trackerId the ID of the tracked face
     * @param label     the display label (e.g., "John Doe | CASE-001")
     * @param color     the BGR color for the bounding box
     */
    public void updateTrackLabel(int trackerId, String label, int[] color) {
        for (TrackedFace tracked : activeTracks) {
            if (tracked.getTrackerId() == trackerId) {
                tracked.setLabel(label);
                tracked.setColor(color);
                return;
            }
        }
    }

    /**
     * Returns the current list of actively tracked faces (read-only view).
     */
    public List<TrackedFace> getActiveTracks() {
        return Collections.unmodifiableList(new ArrayList<>(activeTracks));
    }

    /**
     * Returns the number of actively tracked faces.
     */
    public int getActiveTrackCount() {
        return activeTracks.size();
    }

    /**
     * Clears all active trackers. Called when reinitializing on inference frames
     * or when the camera stops.
     */
    public void clearTrackers() {
        activeTracks.clear();
    }

    // ==================== Body Lock Management ====================

    /**
     * Acquires a persistent body lock for a positively identified target.
     * <p>
     * The face bounding box is expanded downward by {@code BODY_LOCK_EXPANSION_RATIO}
     * to capture the upper torso. A dedicated CSRT tracker is initialized on this
     * expanded region. The lock persists across face tracker re-initializations.
     * </p>
     *
     * @param frame          the current video frame
     * @param faceBox        the face bounding box from YuNet
     * @param targetId       the database target ID
     * @param label          display label (e.g., "John Doe | CASE-001")
     * @param color          BGR color for the bounding box
     * @param faceEmbedding  the SFace embedding that confirmed identity
     * @param faceSimilarity the SFace match score
     * @param currentFrame   the current frame index
     * @return the newly created LockedTarget, or null if initialization fails
     */
    public LockedTarget acquireBodyLock(Mat frame, Rect faceBox,
                                        int targetId, String label, int[] color,
                                        float[] faceEmbedding, double faceSimilarity,
                                        long currentFrame) {
        // Don't create duplicate locks for the same target
        if (hasActiveBodyLock(targetId)) {
            log.debug("Body lock already active for targetId={}, skipping", targetId);
            return null;
        }

        try {
            // Expand face box to torso region
            Rect torsoBox = DnnBodyReIdService.expandFaceToTorso(
                    faceBox, frame.cols(), frame.rows(),
                    AppConstants.BODY_LOCK_EXPANSION_RATIO);

            // Validate torso box
            if (torsoBox.width() <= 0 || torsoBox.height() <= 0 ||
                    torsoBox.x() + torsoBox.width() > frame.cols() ||
                    torsoBox.y() + torsoBox.height() > frame.rows()) {
                log.debug("Invalid torso box for body lock, skipping");
                return null;
            }

            // Initialize CSRT tracker on the expanded torso region
            TrackerCSRT csrt = TrackerCSRT.create();
            csrt.init(frame, torsoBox);

            LockedTarget lock = new LockedTarget(
                    targetId, label, color,
                    csrt, torsoBox,
                    faceEmbedding, faceSimilarity,
                    currentFrame
            );

            lockedTargets.add(lock);
            log.info("Body lock ACQUIRED: targetId={}, label='{}', torso={}x{} at ({},{})",
                    targetId, label, torsoBox.width(), torsoBox.height(),
                    torsoBox.x(), torsoBox.y());

            return lock;

        } catch (Exception e) {
            log.error("Failed to acquire body lock for targetId={}", targetId, e);
            return null;
        }
    }

    /**
     * Updates all active body locks on the current frame.
     * <p>
     * For each lock:
     * 1. Runs CSRT.update() to predict the new torso bounding box
     * 2. Checks if any current YuNet detection overlaps the lock (face re-confirmation)
     * 3. Recomputes fused confidence (α·face + β·body)
     * 4. Releases locks that meet termination conditions
     * </p>
     * Called on EVERY frame (both inference and intermediate) from the capture thread.
     *
     * @param frame        the current video frame
     * @param currentFrame the current frame index
     * @param faceBoxes    face bounding boxes from current YuNet detection (null on intermediate frames)
     * @return list of active locked targets with updated positions
     */
    public List<LockedTarget> updateBodyLocks(Mat frame, long currentFrame, List<Rect> faceBoxes) {
        if (lockedTargets.isEmpty()) {
            return Collections.emptyList();
        }

        List<LockedTarget> toRemove = new ArrayList<>();

        for (LockedTarget lock : lockedTargets) {
            if (!lock.isActive()) {
                toRemove.add(lock);
                continue;
            }

            try {
                // 1. CSRT tracker update
                TrackerCSRT tracker = lock.getBodyTracker();
                Rect updatedBox = new Rect();
                boolean csrtSuccess = tracker.update(frame, updatedBox);

                if (!csrtSuccess) {
                    log.info("Body lock RELEASED (CSRT lost): targetId={}", lock.getTargetId());
                    lock.setActive(false);
                    toRemove.add(lock);
                    continue;
                }

                // Clamp to frame boundaries
                int x = Math.max(0, updatedBox.x());
                int y = Math.max(0, updatedBox.y());
                int w = Math.min(updatedBox.width(), frame.cols() - x);
                int h = Math.min(updatedBox.height(), frame.rows() - y);
                if (w <= 0 || h <= 0) {
                    toRemove.add(lock);
                    continue;
                }
                lock.setBodyBox(new Rect(x, y, w, h));

                // 2. Check for face re-confirmation via spatial overlap
                boolean faceReconfirmed = false;
                if (faceBoxes != null) {
                    for (Rect faceBox : faceBoxes) {
                        if (calculateIoU(lock.getBodyBox(), faceBox) > 0.15) {
                            // Face is within the body lock region — face is visible
                            faceReconfirmed = true;
                            break;
                        }
                    }
                }

                if (faceReconfirmed) {
                    // Will be updated with fresh embedding by DashboardController
                    lock.reconfirmFace(lock.getFaceEmbedding(), lock.getLastFaceSimilarity(), currentFrame);
                } else if (lock.isFaceCurrentlyVisible()) {
                    lock.markFaceLost();
                }

                // 3. Recompute fused confidence
                lock.recomputeFusedConfidence(currentFrame);

                // 4. Check release conditions
                if (lock.shouldRelease(currentFrame)) {
                    log.info("Body lock RELEASED (confidence/timeout): targetId={}, fused={}",
                            lock.getTargetId(), String.format("%.3f", lock.getFusedConfidence()));
                    lock.setActive(false);
                    toRemove.add(lock);
                }

            } catch (Exception e) {
                log.debug("Body lock update failed for targetId={}: {}", lock.getTargetId(), e.getMessage());
                toRemove.add(lock);
            }
        }

        lockedTargets.removeAll(toRemove);
        return Collections.unmodifiableList(new ArrayList<>(lockedTargets));
    }

    /**
     * Returns whether a body lock already exists for the given target ID.
     */
    public boolean hasActiveBodyLock(int targetId) {
        for (LockedTarget lock : lockedTargets) {
            if (lock.getTargetId() == targetId && lock.isActive()) {
                return true;
            }
        }
        return false;
    }

    /**
     * Returns the active body lock for the given target ID, or null.
     */
    public LockedTarget getBodyLock(int targetId) {
        for (LockedTarget lock : lockedTargets) {
            if (lock.getTargetId() == targetId && lock.isActive()) {
                return lock;
            }
        }
        return null;
    }

    /**
     * Returns all active body locks (read-only view).
     */
    public List<LockedTarget> getActiveBodyLocks() {
        return Collections.unmodifiableList(new ArrayList<>(lockedTargets));
    }

    /**
     * Clears all body locks. Called when camera stops.
     */
    public void clearBodyLocks() {
        lockedTargets.clear();
        log.debug("All body locks cleared");
    }

    /**
     * Clears both face trackers and body locks.
     */
    public void clearAll() {
        clearTrackers();
        clearBodyLocks();
    }

    /**
     * Creates a new tracker instance based on the configured tracker type.
     * <p>
     * Uses the opencv_tracking module's TrackerKCF/TrackerCSRT which extend
     * the opencv_video.Tracker base class.
     * </p>
     */
    private Tracker createTracker() {
        try {
            // Refresh tracker type from config (allows runtime changes)
            trackerType = ConfigurationService.getInstance().getTrackerType();

            if ("CSRT".equalsIgnoreCase(trackerType)) {
                return TrackerCSRT.create();
            } else {
                // Default to KCF — fastest option for edge constraints
                return TrackerKCF.create();
            }
        } catch (Exception e) {
            log.error("Failed to create {} tracker: {}", trackerType, e.getMessage());
            // Last resort: try KCF
            try {
                return TrackerKCF.create();
            } catch (Exception e2) {
                log.error("Failed to create fallback KCF tracker", e2);
                return null;
            }
        }
    }

    /**
     * Finds the previous tracked face with the highest spatial overlap (IoU) to a new detection box.
     * Used for label carry-over: transfers previously resolved recognition labels to new trackers
     * that cover the same physical face, preventing the "Analyzing..." flicker on tracker re-initialization.
     *
     * @param previousTracks the list of tracks from the previous inference frame
     * @param newBox         the new detection bounding box to match against
     * @return the best overlapping previous track, or null if no track has ≥30% IoU
     */
    private TrackedFace findBestOverlap(List<TrackedFace> previousTracks, Rect newBox) {
        TrackedFace best = null;
        double bestIoU = 0.3; // Minimum 30% overlap to consider a spatial match
        for (TrackedFace prev : previousTracks) {
            double iou = calculateIoU(prev.getBoundingBox(), newBox);
            if (iou > bestIoU) {
                bestIoU = iou;
                best = prev;
            }
        }
        return best;
    }

    /**
     * Calculates Intersection over Union (IoU) between two rectangles.
     * Standard metric for spatial overlap in object detection.
     *
     * @return IoU value in [0.0, 1.0] — 0 means no overlap, 1 means perfect overlap
     */
    private double calculateIoU(Rect a, Rect b) {
        int x1 = Math.max(a.x(), b.x());
        int y1 = Math.max(a.y(), b.y());
        int x2 = Math.min(a.x() + a.width(), b.x() + b.width());
        int y2 = Math.min(a.y() + a.height(), b.y() + b.height());

        if (x2 <= x1 || y2 <= y1) return 0.0;

        double intersection = (double) (x2 - x1) * (y2 - y1);
        double areaA = (double) a.width() * a.height();
        double areaB = (double) b.width() * b.height();
        double union = areaA + areaB - intersection;

        return union > 0 ? intersection / union : 0.0;
    }
}
