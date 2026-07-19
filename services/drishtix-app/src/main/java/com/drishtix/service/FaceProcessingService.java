package com.drishtix.service;

import com.drishtix.exception.FaceNotFoundException;
import com.drishtix.util.AppConstants;
import com.drishtix.util.AutoCloseableMat;
import org.bytedeco.opencv.opencv_core.*;
import org.bytedeco.opencv.opencv_objdetect.CascadeClassifier;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.io.File;
import java.io.InputStream;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardCopyOption;

import static org.bytedeco.opencv.global.opencv_imgcodecs.*;
import static org.bytedeco.opencv.global.opencv_imgproc.*;

/**
 * Service responsible for face detection and template extraction using OpenCV.
 * <p>
 * Uses Haar Cascade classifier for face detection.
 * Extracts face regions of interest (ROI), converts to grayscale,
 * and resizes to a standard dimension for LBPH training.
 * </p>
 */
public class FaceProcessingService {

    private static final Logger log = LoggerFactory.getLogger(FaceProcessingService.class);
    private static volatile FaceProcessingService instance;

    private CascadeClassifier faceDetector;

    private FaceProcessingService() {
        initializeCascade();
    }

    public static FaceProcessingService getInstance() {
        if (instance == null) {
            synchronized (FaceProcessingService.class) {
                if (instance == null) {
                    instance = new FaceProcessingService();
                }
            }
        }
        return instance;
    }

    /**
     * Detects a single face in the given image file and extracts a grayscale template.
     *
     * @param imagePath path to the uploaded image file
     * @return the preprocessed face ROI as a grayscale Mat (200x200)
     * @throws FaceNotFoundException if no face is detected in the image
     */
    public Mat detectAndExtractFace(String imagePath) {
        Mat image = imread(imagePath);
        if (image.empty()) {
            throw new FaceNotFoundException("Failed to load image: " + imagePath);
        }

        try {
            RectVector faces = detectFaces(image);

            if (faces.size() == 0) {
                throw new FaceNotFoundException("No face detected in the uploaded image. " +
                        "Please upload a clear frontal photo.");
            }

            if (faces.size() > 1) {
                log.warn("Multiple faces ({}) detected in upload, using the largest face", faces.size());
            }

            // Use the largest detected face
            Rect bestFace = getLargestFace(faces);
            return extractFaceROI(image, bestFace);

        } finally {
            image.release();
        }
    }

    /**
     * Detects all faces in a frame and returns their bounding rectangles.
     *
     * @param frame the input frame (BGR color)
     * @return RectVector containing all detected face rectangles
     */
    public RectVector detectFaces(Mat frame) {
        if (faceDetector == null) {
            log.error("Face detector not initialized!");
            return new RectVector();
        }

        try (AutoCloseableMat grayFrame = new AutoCloseableMat()) {
            // Convert to grayscale for detection
            if (frame.channels() == 3) {
                cvtColor(frame, grayFrame.get(), COLOR_BGR2GRAY);
            } else {
                frame.copyTo(grayFrame.get());
            }

            // Equalize histogram for better detection under varying lighting
            equalizeHist(grayFrame.get(), grayFrame.get());

            int minFaceSize = ConfigurationService.getInstance().getMinFaceSize();

            RectVector faces = new RectVector();
            faceDetector.detectMultiScale(
                    grayFrame.get(),
                    faces,
                    1.1,          // scaleFactor
                    5,            // minNeighbors (higher = fewer false positives)
                    0,            // flags
                    new Size(minFaceSize, minFaceSize),  // minSize
                    new Size(0, 0)                        // maxSize (no limit)
            );

            return faces;
        }
    }

    /**
     * Extracts the face region of interest from a frame, converts to grayscale,
     * and resizes to the standard face template dimensions.
     *
     * @param frame the full frame
     * @param faceRect the bounding rectangle of the detected face
     * @return a grayscale, resized face ROI suitable for LBPH training/prediction
     */
    public Mat extractFaceROI(Mat frame, Rect faceRect) {
        // Crop the face region
        Mat faceROI = new Mat(frame, faceRect);

        // Convert to grayscale
        Mat grayFace = new Mat();
        if (faceROI.channels() == 3) {
            cvtColor(faceROI, grayFace, COLOR_BGR2GRAY);
        } else {
            faceROI.copyTo(grayFace);
        }

        // Resize to standard dimensions
        Mat resizedFace = new Mat();
        resize(grayFace, resizedFace, new Size(AppConstants.FACE_WIDTH, AppConstants.FACE_HEIGHT));

        // Equalize histogram for consistent lighting
        equalizeHist(resizedFace, resizedFace);

        // Clean up intermediate Mats
        faceROI.release();
        grayFace.release();

        return resizedFace;
    }

    /**
     * Saves a preprocessed face template to disk.
     *
     * @param faceMat the grayscale face ROI
     * @param outputPath the file path to save the template
     */
    public void saveTemplate(Mat faceMat, String outputPath) {
        File parentDir = new File(outputPath).getParentFile();
        if (parentDir != null && !parentDir.exists()) {
            parentDir.mkdirs();
        }

        boolean saved = imwrite(outputPath, faceMat);
        if (!saved) {
            throw new FaceNotFoundException("Failed to save face template to: " + outputPath);
        }
        log.debug("Face template saved: {}", outputPath);
    }

    /**
     * Returns the largest face rectangle from a set of detections.
     */
    private Rect getLargestFace(RectVector faces) {
        Rect largest = faces.get(0);
        for (long i = 1; i < faces.size(); i++) {
            Rect current = faces.get(i);
            if (current.area() > largest.area()) {
                largest = current;
            }
        }
        return largest;
    }

    /**
     * Initializes the Haar Cascade classifier.
     * Extracts the cascade XML from the classpath to a temp file for OpenCV to load.
     */
    private void initializeCascade() {
        try {
            // Extract cascade XML from classpath resources to a temp file
            String cascadeResource = "cascades/" + AppConstants.HAAR_CASCADE_FILE;
            InputStream is = getClass().getClassLoader().getResourceAsStream(cascadeResource);

            if (is == null) {
                // Try loading from the file system directly
                File cascadeFile = new File(cascadeResource);
                if (cascadeFile.exists()) {
                    faceDetector = new CascadeClassifier(cascadeFile.getAbsolutePath());
                    log.info("Haar Cascade loaded from file system: {}", cascadeFile.getAbsolutePath());
                    return;
                }
                log.error("Haar Cascade file not found: {}", cascadeResource);
                return;
            }

            // Copy to temp file since CascadeClassifier needs a file path
            Path tempFile = Files.createTempFile("drishtix_cascade_", ".xml");
            Files.copy(is, tempFile, StandardCopyOption.REPLACE_EXISTING);
            is.close();

            faceDetector = new CascadeClassifier(tempFile.toString());

            if (faceDetector.empty()) {
                log.error("Failed to load Haar Cascade classifier from: {}", tempFile);
                faceDetector = null;
            } else {
                log.info("Haar Cascade classifier initialized successfully from classpath");
            }

        } catch (Exception e) {
            log.error("Failed to initialize face detector", e);
        }
    }
}
