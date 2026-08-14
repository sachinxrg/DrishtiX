package com.drishtix.service;

import com.drishtix.exception.FaceNotFoundException;
import com.drishtix.model.FaceDetection;
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
import java.util.ArrayList;
import java.util.List;

import com.drishtix.model.FaceQuality;

import static org.bytedeco.opencv.global.opencv_imgcodecs.*;
import static org.bytedeco.opencv.global.opencv_imgproc.*;
import static org.bytedeco.opencv.global.opencv_core.*;
import static org.bytedeco.opencv.global.opencv_calib3d.estimateAffinePartial2D;

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
     * Extracts an expanded person crop from a frame for ReID embedding extraction.
     * <p>
     * Unlike {@link #extractFaceROI(Mat, Rect)} which returns a tight 200×200 grayscale
     * face crop for LBPH, this method returns a larger COLOR crop including the
     * upper body (shoulders, torso). This is critical for OSNet which relies on
     * clothing texture and body shape features for person re-identification.
     * </p>
     * <p>
     * The crop expands the face bounding box:
     * - Horizontally: 1.5× the face width on each side
     * - Vertically: 0.5× above the face, 2.5× below (to capture torso)
     * </p>
     *
     * @param frame    the full frame (BGR color, not modified)
     * @param faceRect the bounding rectangle of the detected face
     * @return a color Mat of the person crop (caller must release), or null if extraction fails
     */
    public Mat extractPersonCrop(Mat frame, Rect faceRect) {
        try {
            int frameW = frame.cols();
            int frameH = frame.rows();
            int fw = faceRect.width();
            int fh = faceRect.height();

            // Expand bounding box to capture upper body
            int expandX = (int) (fw * 1.5);  // Horizontal expansion
            int expandUp = (int) (fh * 0.5);  // Above face
            int expandDown = (int) (fh * 2.5); // Below face (torso)

            // Calculate expanded coordinates, clamped to frame boundaries
            int x1 = Math.max(0, faceRect.x() - expandX);
            int y1 = Math.max(0, faceRect.y() - expandUp);
            int x2 = Math.min(frameW, faceRect.x() + fw + expandX);
            int y2 = Math.min(frameH, faceRect.y() + fh + expandDown);

            int cropW = x2 - x1;
            int cropH = y2 - y1;

            // Sanity check: ensure the crop is reasonable
            if (cropW < 30 || cropH < 30) {
                log.debug("Person crop too small ({}×{}), skipping ReID", cropW, cropH);
                return null;
            }

            // Extract the person region (COLOR — not grayscale)
            Rect personRect = new Rect(x1, y1, cropW, cropH);
            Mat personCrop = new Mat(frame, personRect).clone(); // Clone so it's independent

            log.debug("Person crop extracted: {}×{} from face at ({},{})",
                    cropW, cropH, faceRect.x(), faceRect.y());

            return personCrop;

        } catch (Exception e) {
            log.warn("Failed to extract person crop for ReID: {}", e.getMessage());
            return null;
        }
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

    // ==================== Advanced Modules: Alignment & FQA ====================

    /**
     * Aligns a detected face for DNN recognition using 5-point landmarks via Affine Warp.
     * Maps the detected landmarks to ArcFace/SFace standard canonical coordinates for a 112x112 crop.
     */
    public Mat alignFaceForDnn(Mat frame, FaceDetection detection) {
        try {
            float[][] marks = detection.getLandmarks();
            if (marks == null || marks.length < 5) return null;

            // Detected landmarks (Right Eye, Left Eye, Nose Tip, Right Mouth, Left Mouth)
            // Note: YuNet landmarks might be ordered differently depending on the model version,
            // but the standard is [RightEye, LeftEye, Nose, RightMouth, LeftMouth] in image space.
            Mat srcPts = new Mat(5, 1, CV_32FC2);
            for (int i = 0; i < 5; i++) {
                srcPts.ptr(i).putFloat(0, marks[i][0]); // x
                srcPts.ptr(i).putFloat(4, marks[i][1]); // y
            }

            // Standard canonical landmarks for 112x112 (ArcFace/SFace standard)
            float[][] canonical = {
                {38.2946f, 51.6963f}, // Right Eye
                {73.5318f, 51.5014f}, // Left Eye
                {56.0252f, 71.7366f}, // Nose Tip
                {41.5493f, 92.3655f}, // Right Mouth
                {70.7299f, 92.2041f}  // Left Mouth
            };

            Mat dstPts = new Mat(5, 1, CV_32FC2);
            for (int i = 0; i < 5; i++) {
                dstPts.ptr(i).putFloat(0, canonical[i][0]);
                dstPts.ptr(i).putFloat(4, canonical[i][1]);
            }

            // Estimate affine transform (rotation, translation, scale)
            Mat transform = estimateAffinePartial2D(srcPts, dstPts);
            if (transform.empty()) {
                srcPts.release(); dstPts.release(); transform.release();
                return null;
            }

            // Apply warp
            Mat alignedFace = new Mat();
            warpAffine(frame, alignedFace, transform,
                    new Size(AppConstants.DNN_FACE_INPUT_SIZE, AppConstants.DNN_FACE_INPUT_SIZE));

            srcPts.release(); dstPts.release(); transform.release();
            return alignedFace;

        } catch (Exception e) {
            log.warn("Failed to align face for DNN: {}", e.getMessage());
            return null;
        }
    }

    /**
     * Module 1: Lightweight Blur Detection using Laplacian Variance.
     * Higher variance = sharper image.
     */
    public double calculateLaplacianVariance(Mat faceCrop) {
        if (faceCrop == null || faceCrop.empty()) return 0;
        Mat gray = new Mat();
        if (faceCrop.channels() == 3) {
            cvtColor(faceCrop, gray, COLOR_BGR2GRAY);
        } else {
            faceCrop.copyTo(gray);
        }

        Mat laplacian = new Mat();
        Laplacian(gray, laplacian, CV_64F);

        Mat mean = new Mat();
        Mat stddev = new Mat();
        meanStdDev(laplacian, mean, stddev);

        double std = stddev.ptr(0).getDouble(0);
        double variance = std * std;

        gray.release();
        laplacian.release();
        mean.release();
        stddev.release();

        return variance;
    }

    /**
     * Module 1: Head Pose Estimation (Yaw/Pitch/Roll) Filtering.
     * Uses the ratio of left-to-nose vs right-to-nose distances.
     */
    public boolean isExtremePose(float[][] landmarks) {
        if (landmarks == null || landmarks.length < 5) return false;

        // 0: Right Eye, 1: Left Eye, 2: Nose
        float rightEyeX = landmarks[0][0];
        float leftEyeX = landmarks[1][0];
        float noseX = landmarks[2][0];

        // Euclidean distance isn't strictly necessary for just horizontal yaw, X-dist works well
        float distRight = Math.abs(noseX - rightEyeX);
        float distLeft = Math.abs(leftEyeX - noseX);

        if (distRight == 0 || distLeft == 0) return true;

        float ratio = distLeft / distRight;

        // Ratio roughly corresponds to yaw. > 4.0 or < 0.25 indicates extreme profile (> ~45 degrees)
        return ratio > 4.0f || ratio < 0.25f;
    }

    /**
     * Module 2: Dynamic Lighting Normalization (CLAHE) on LAB color space.
     */
    public Mat applyCLAHE(Mat bgrFace) {
        if (bgrFace == null || bgrFace.empty() || bgrFace.channels() != 3) return bgrFace;

        Mat lab = new Mat();
        cvtColor(bgrFace, lab, COLOR_BGR2Lab);

        MatVector labChannels = new MatVector();
        split(lab, labChannels);

        // Apply CLAHE to L-channel
        Mat lChannel = labChannels.get(0);
        org.bytedeco.opencv.opencv_imgproc.CLAHE clahe = createCLAHE(2.0, new Size(8, 8));
        clahe.apply(lChannel, lChannel);

        // Merge back and convert
        merge(labChannels, lab);
        Mat result = new Mat();
        cvtColor(lab, result, COLOR_Lab2BGR);

        lab.release();
        labChannels.close(); 
        clahe.close();

        return result;
    }

    /**
     * Module 4: Silent Anti-Spoofing & Liveness Detection using FFT.
     * Analyzes high-frequency components to detect screen moire patterns.
     */
    public double detectLivenessFFT(Mat faceCrop) {
        if (faceCrop == null || faceCrop.empty()) return 0;

        Mat gray = new Mat();
        if (faceCrop.channels() == 3) {
            cvtColor(faceCrop, gray, COLOR_BGR2GRAY);
        } else {
            faceCrop.copyTo(gray);
        }

        // Resize to a small power of 2 for fast FFT
        Mat resized = new Mat();
        resize(gray, resized, new Size(64, 64));
        gray.release();

        Mat floatMat = new Mat();
        resized.convertTo(floatMat, CV_32F);
        resized.release();

        Mat dftResult = new Mat();
        dft(floatMat, dftResult, DFT_COMPLEX_OUTPUT, 0);
        floatMat.release();

        // Compute magnitude
        MatVector planes = new MatVector();
        split(dftResult, planes);
        Mat mag = new Mat();
        magnitude(planes.get(0), planes.get(1), mag);
        dftResult.release();

        // We skip shifting the quadrants for speed and just look at the raw magnitude array
        // High frequency is generally away from the origin (0,0).
        // Since we didn't shift, origin is at top-left.
        double totalEnergy = sumElems(mag).get(0);

        // Zero out the low frequencies (e.g. top-left corner)
        int cx = 10;
        int cy = 10;
        Mat roi = new Mat(mag, new Rect(0, 0, cx, cy));
        roi.setTo(new Mat(new double[]{0.0})); // Clear low frequencies

        double highFreqEnergy = sumElems(mag).get(0);
        mag.release();

        if (totalEnergy == 0) return 0;

        double ratio = highFreqEnergy / totalEnergy;

        // Normal live faces have fewer high-frequency spikes compared to screens with moire grids.
        // A very high ratio indicates a screen (SPOOF).
        // We'll map ratio: high ratio -> low liveness score.
        // Empirical tuning required, but typically ratio > 0.3 is suspect for 64x64 FFT.
        double liveness = 1.0 - (ratio * 2.0);
        return Math.max(0.0, Math.min(1.0, liveness));
    }

    /**
     * Consolidates the FQA modules into a single assessment.
     */
    public FaceQuality assessFaceQuality(Mat faceCrop, FaceDetection detection) {
        double laplacianVar = calculateLaplacianVariance(faceCrop);
        boolean blurred = laplacianVar < 50.0; // CFG_MIN_BLUR_THRESHOLD
        boolean extremePose = isExtremePose(detection.getLandmarks());
        double liveness = detectLivenessFFT(faceCrop);

        return new FaceQuality(blurred, extremePose, liveness, laplacianVar);
    }
}

