package com.drishtix.util;

/**
 * Application-wide constants for DrishtiX.
 * Centralizes magic numbers, paths, and default values.
 */
public final class AppConstants {

    private AppConstants() {
        // Utility class — no instantiation
    }

    // ==================== Application ====================
    public static final String APP_NAME = "DrishtiX";
    public static final String APP_TAGLINE = "Advanced Facial Recognition & Alert System";
    public static final String APP_VERSION = "1.0.0";

    // ==================== File Paths ====================
    public static final String DATA_DIR = "data";
    public static final String UPLOADS_DIR = DATA_DIR + "/uploads";
    public static final String TEMPLATES_DIR = DATA_DIR + "/templates";
    public static final String SNAPSHOTS_DIR = DATA_DIR + "/snapshots";

    // ==================== OpenCV ====================
    public static final String HAAR_CASCADE_FILE = "haarcascade_frontalface_alt2.xml";
    public static final int FACE_WIDTH = 200;
    public static final int FACE_HEIGHT = 200;
    public static final int MIN_FACE_SIZE = 80;

    // ==================== Alert Defaults ====================
    public static final double DEFAULT_CONFIDENCE_THRESHOLD = 80.0;
    public static final int DEFAULT_COOLDOWN_SECONDS = 30;
    public static final int DEFAULT_FPS_TARGET = 15;

    // ==================== Colors (OpenCV BGR format) ====================
    /** RED for CRIMINAL bounding box (BGR: 0, 77, 255 → matches #FF4D00). */
    public static final int[] COLOR_CRIMINAL_BGR = {46, 77, 255};
    /** CYAN for MISSING_PERSON bounding box (BGR: 255, 212, 0 → matches #00D4FF). */
    public static final int[] COLOR_MISSING_BGR = {255, 212, 0};
    /** GREEN for unknown/civilian bounding box (BGR: 94, 197, 34). */
    public static final int[] COLOR_UNKNOWN_BGR = {136, 255, 68};

    // ==================== Config Keys ====================
    public static final String CFG_CONFIDENCE_THRESHOLD = "confidence_threshold";
    public static final String CFG_ALERT_COOLDOWN = "alert_cooldown_seconds";
    public static final String CFG_VIDEO_FPS = "video_fps_target";
    public static final String CFG_SNAPSHOT_RETENTION = "snapshot_retention_days";
    public static final String CFG_AUDIO_ENABLED = "audio_enabled";
    public static final String CFG_DETECTION_METHOD = "face_detection_method";
    public static final String CFG_MIN_FACE_SIZE = "min_face_size";
    public static final String CFG_AUTO_START_CAMERA = "auto_start_camera";

    // ==================== Audio ====================
    public static final String SOUND_CRIMINAL_ALARM = "sounds/alarm_criminal.wav";
    public static final String SOUND_MISSING_CHIME = "sounds/chime_missing.wav";

    // ==================== Audit Action Types ====================
    public static final String AUDIT_TARGET_ADDED = "TARGET_ADDED";
    public static final String AUDIT_TARGET_UPDATED = "TARGET_UPDATED";
    public static final String AUDIT_TARGET_DEACTIVATED = "TARGET_DEACTIVATED";
    public static final String AUDIT_ALERT_ACKNOWLEDGED = "ALERT_ACKNOWLEDGED";
    public static final String AUDIT_CONFIG_CHANGED = "CONFIG_CHANGED";
    public static final String AUDIT_RECOGNIZER_RETRAINED = "RECOGNIZER_RETRAINED";

    // ==================== Image Constraints ====================
    public static final long MAX_IMAGE_SIZE_BYTES = 10 * 1024 * 1024; // 10MB
    public static final int MAX_PHOTOS_PER_TARGET = 5;
    public static final int MAX_IMAGE_DIMENSION = 1024;
}
