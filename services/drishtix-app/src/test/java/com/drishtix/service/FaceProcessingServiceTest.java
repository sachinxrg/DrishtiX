package com.drishtix.service;

import com.drishtix.model.FaceDetection;
import com.drishtix.model.FaceQuality;
import org.bytedeco.javacpp.Loader;
import org.bytedeco.opencv.opencv_core.Mat;
import org.bytedeco.opencv.opencv_core.Rect;
import org.bytedeco.opencv.opencv_core.Scalar;
import org.junit.jupiter.api.BeforeAll;
import org.junit.jupiter.api.Test;

import org.bytedeco.opencv.opencv_core.Size;
import org.bytedeco.opencv.opencv_core.Point;
import static org.bytedeco.opencv.global.opencv_core.*;
import static org.bytedeco.opencv.global.opencv_imgproc.GaussianBlur;
import static org.bytedeco.opencv.global.opencv_imgproc.line;
import static org.junit.jupiter.api.Assertions.*;

public class FaceProcessingServiceTest {

    private static FaceProcessingService faceService;

    @BeforeAll
    public static void setup() {
        // Load OpenCV native libraries before any tests run
        Loader.load(org.bytedeco.opencv.global.opencv_core.class);
        faceService = FaceProcessingService.getInstance();
    }

    @Test
    public void testAssessFaceQuality_SharpImage() {
        // Create a synthetic "sharp" image with a diagonal line
        try (Mat sharpImg = new Mat(100, 100, CV_8UC3, new Scalar(0, 0, 0, 0))) {
            line(sharpImg, new Point(0, 0), new Point(100, 100), new Scalar(255, 255, 255, 0), 5, 8, 0);
            
            // Dummy face detection for pose checking
            float[][] landmarks = new float[][]{
                {30f, 40f}, {70f, 40f}, // eyes
                {50f, 60f}, // nose
                {35f, 80f}, {65f, 80f} // mouth
            };
            FaceDetection detection = new FaceDetection(new Rect(0, 0, 100, 100), landmarks, 0.9f, null);

            FaceQuality quality = faceService.assessFaceQuality(sharpImg, detection);
            
            assertNotNull(quality);
            // Random noise will have very high laplacian variance
            assertTrue(quality.getLaplacianVariance() > 100.0);
            assertFalse(quality.isUnfavorable());
        }
    }

    @Test
    public void testAssessFaceQuality_BlurredImage() {
        // Create a synthetic image and blur it heavily
        try (Mat img = new Mat(100, 100, CV_8UC3, new Scalar(0, 0, 0, 0));
             Mat blurredImg = new Mat()) {
            line(img, new Point(0, 0), new Point(100, 100), new Scalar(255, 255, 255, 0), 5, 8, 0);
            GaussianBlur(img, blurredImg, new Size(15, 15), 0);
            
            float[][] landmarks = new float[][]{
                {30f, 40f}, {70f, 40f}, {50f, 60f}, {35f, 80f}, {65f, 80f}
            };
            FaceDetection detection = new FaceDetection(new Rect(0, 0, 100, 100), landmarks, 0.9f, null);

            FaceQuality quality = faceService.assessFaceQuality(blurredImg, detection);
            
            assertNotNull(quality);
            // Variance should be extremely low due to the 15x15 blur
            assertTrue(quality.getLaplacianVariance() < 50.0);
        }
    }
}
