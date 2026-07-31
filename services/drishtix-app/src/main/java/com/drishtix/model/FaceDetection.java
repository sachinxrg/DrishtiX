package com.drishtix.model;

import org.bytedeco.opencv.opencv_core.Rect;

/**
 * Encapsulates a single face detection result from the DNN-based YuNet detector.
 * <p>
 * Contains the bounding box, 5-point facial landmarks (for alignment),
 * and the detection confidence score.
 * </p>
 */
public class FaceDetection {

    private final Rect boundingBox;
    private final float[][] landmarks; // 5 points × 2 (x, y)
    private final float detectionScore;
    private final float[] detectionRow; // Raw 15-column YuNet output for alignCrop()

    /**
     * @param boundingBox    the face bounding rectangle
     * @param landmarks      5-point facial landmarks [rightEye, leftEye, noseTip, rightMouth, leftMouth]
     * @param detectionScore YuNet detection confidence (0.0–1.0)
     * @param detectionRow   raw 15-value detection row from FaceDetectorYN for use with alignCrop()
     */
    public FaceDetection(Rect boundingBox, float[][] landmarks, float detectionScore, float[] detectionRow) {
        this.boundingBox = boundingBox;
        this.landmarks = landmarks;
        this.detectionScore = detectionScore;
        this.detectionRow = detectionRow;
    }

    public Rect getBoundingBox() {
        return boundingBox;
    }

    /**
     * Returns the 5-point facial landmarks as a float[5][2] array.
     * <p>
     * Point order: [0]=rightEye, [1]=leftEye, [2]=noseTip, [3]=rightMouth, [4]=leftMouth
     * </p>
     */
    public float[][] getLandmarks() {
        return landmarks;
    }

    public float getDetectionScore() {
        return detectionScore;
    }

    /**
     * Returns the raw 15-value detection row from FaceDetectorYN.
     * <p>
     * This is required by {@code FaceRecognizerSF.alignCrop()} to produce
     * the exact alignment that SFace was trained on — eliminating distribution
     * shift from manual warpAffine alignment.
     * </p>
     */
    public float[] getDetectionRow() {
        return detectionRow;
    }

    @Override
    public String toString() {
        return "FaceDetection{box=" + boundingBox.x() + "," + boundingBox.y() +
                " " + boundingBox.width() + "x" + boundingBox.height() +
                ", score=" + String.format("%.3f", detectionScore) + '}';
    }
}
