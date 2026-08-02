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
    public static final String APP_VERSION = "3.0.0";

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

    // ==================== DNN Models ====================
    public static final String MODELS_DIR = DATA_DIR + "/models";
    public static final String YUNET_MODEL_FILE = "face_detection_yunet_2023mar.onnx";
    public static final String SFACE_MODEL_FILE = "face_recognition_sface_2021dec.onnx";
    public static final int DNN_FACE_INPUT_SIZE = 112;  // SFace aligned face input
    public static final int DNN_MAX_FACES = 50;  // Scaled for 40+ face throughput

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

    // ==================== DNN Config Keys ====================
    public static final String CFG_DNN_SCORE_THRESHOLD = "dnn_score_threshold";
    public static final String CFG_DNN_NMS_THRESHOLD = "dnn_nms_threshold";
    public static final String CFG_DNN_COSINE_THRESHOLD = "dnn_cosine_threshold";
    public static final String CFG_DNN_MODEL_DIR = "dnn_model_dir";

    // ==================== DNN Defaults ====================
    public static final double DEFAULT_DNN_SCORE_THRESHOLD = 0.6;
    public static final double DEFAULT_DNN_NMS_THRESHOLD = 0.3;
    public static final double DEFAULT_DNN_COSINE_THRESHOLD = 0.363;  // SFace recommended threshold

    // ==================== Audio ====================
    public static final String SOUND_CRIMINAL_ALARM = "sounds/alarm_criminal.wav";
    public static final String SOUND_MISSING_CHIME = "sounds/chime_missing.wav";

    // ==================== Audit Action Types ====================
    public static final String AUDIT_TARGET_ADDED = "TARGET_ADDED";
    public static final String AUDIT_TARGET_UPDATED = "TARGET_UPDATED";
    public static final String AUDIT_TARGET_DEACTIVATED = "TARGET_DEACTIVATED";
    public static final String AUDIT_TARGET_DELETED = "TARGET_DELETED";
    public static final String AUDIT_DETECTION_LOG_DELETED = "DETECTION_LOG_DELETED";
    public static final String AUDIT_ALERT_ACKNOWLEDGED = "ALERT_ACKNOWLEDGED";
    public static final String AUDIT_CONFIG_CHANGED = "CONFIG_CHANGED";
    public static final String AUDIT_RECOGNIZER_RETRAINED = "RECOGNIZER_RETRAINED";

    // ==================== Image Constraints ====================
    public static final long MAX_IMAGE_SIZE_BYTES = 10 * 1024 * 1024; // 10MB
    public static final int MAX_PHOTOS_PER_TARGET = 5;
    public static final int MAX_IMAGE_DIMENSION = 1024;

    // ==================== ReID Config Keys ====================
    public static final String CFG_REID_SERVICE_URL = "reid_service_url";
    public static final String CFG_REID_ENABLED = "reid_enabled";
    public static final String CFG_REID_SIMILARITY_THRESHOLD = "reid_similarity_threshold";
    public static final String CFG_REID_MATCH_WINDOW = "reid_match_window";

    // ==================== Telegram & Officer Dispatch Config Keys ====================
    public static final String CFG_TELEGRAM_ENABLED = "telegram_enabled";
    public static final String CFG_TELEGRAM_BOT_TOKEN = "telegram_bot_token";
    public static final String CFG_TELEGRAM_CHAT_ID = "telegram_chat_id";
    public static final String CFG_OFFICER_EMAIL = "officer_email";
    public static final String CFG_OFFICER_DISPATCH_ENABLED = "officer_dispatch_enabled";

    // ==================== Notification Config Keys ====================
    public static final String CFG_NOTIFICATION_MODE = "notification_mode";

    // ==================== ReID Defaults ====================
    public static final String DEFAULT_REID_SERVICE_URL = "http://localhost:8100";
    public static final double DEFAULT_REID_SIMILARITY_THRESHOLD = 0.85;
    public static final int DEFAULT_REID_MATCH_WINDOW = 100;

    // ==================== Additional Audit Actions ====================
    public static final String AUDIT_REID_MATCH = "REID_MATCH";
    public static final String AUDIT_TELEGRAM_SENT = "TELEGRAM_ALERT_SENT";
    public static final String AUDIT_INGESTION_SYNC = "INGESTION_SYNC";

    // ==================== Background Ingestion ====================
    public static final String INGESTION_DIR = DATA_DIR + "/ingestion";
    public static final String INGESTION_FBI_DIR = INGESTION_DIR + "/fbi";
    public static final String INGESTION_CBI_DIR = INGESTION_DIR + "/cbi";
    public static final String INGESTION_TRACKCHILD_DIR = INGESTION_DIR + "/trackchild";

    public static final String FBI_API_BASE_URL = "https://api.fbi.gov/wanted/v1/list";
    public static final String CBI_WANTED_URL = "https://cbi.gov.in/wanted-persons";
    public static final String TRACKCHILD_URL = "https://trackthemissingchild.gov.in/trackchild/photograph_missing.php";

    public static final String CFG_INGESTION_ENABLED = "ingestion_enabled";
    public static final String CFG_INGESTION_INTERVAL_HOURS = "ingestion_interval_hours";
    public static final String CFG_FBI_API_KEY = "fbi_api_key";
    public static final int DEFAULT_INGESTION_INTERVAL_HOURS = 6;
    public static final int INGESTION_RATE_LIMIT_MS = 2000; // 2 second delay between HTTP requests

    // ==================== Frame Skipping & Tracking ====================
    public static final String CFG_INFERENCE_FRAME_INTERVAL = "inference_frame_interval";
    public static final int DEFAULT_INFERENCE_FRAME_INTERVAL = 2; // Run full inference every 2nd frame (YuNet is ~2ms)
    public static final String CFG_TRACKER_TYPE = "tracker_type";
    public static final String DEFAULT_TRACKER_TYPE = "KCF"; // KCF or CSRT

    // ==================== OSNet Body Re-ID Model ====================
    public static final String OSNET_MODEL_FILE = "osnet_x0_25_msmt17.onnx";
    public static final int OSNET_INPUT_HEIGHT = 256;   // OSNet input: 256×128 (H×W)
    public static final int OSNET_INPUT_WIDTH = 128;
    public static final int OSNET_EMBEDDING_DIM = 512;  // OSNet x0.25 output dimensions

    // ==================== Body Lock (Facial-to-Spatial Handoff) ====================
    /** Expand face bbox downward by this factor to capture upper torso/shirt for CSRT. */
    public static final double BODY_LOCK_EXPANSION_RATIO = 2.0;
    /** Maximum frames a body lock can persist without face re-confirmation (60s at 15 FPS). */
    public static final int BODY_LOCK_MAX_FRAMES = 900;
    /** Frames after face loss to transition from face-weighted to body-only fusion. */
    public static final int BODY_LOCK_GRACE_FRAMES = 30;
    /** Minimum fused confidence to maintain a body lock. */
    public static final double BODY_LOCK_MIN_CONFIDENCE = 0.40;
    /** Consecutive low-confidence frames before releasing a body lock. */
    public static final int BODY_LOCK_LOW_CONF_FRAMES = 15;
    /** Re-verify OSNet embedding every N frames while face is lost. */
    public static final int BODY_LOCK_REVERIFY_INTERVAL = 15;
    /** Minimum OSNet cosine similarity to consider the same person. */
    public static final double OSNET_SIMILARITY_THRESHOLD = 0.50;

    // Body lock fusion weights: α = face weight, β = body weight
    public static final double FUSION_ALPHA_FACE_VISIBLE = 0.8;
    public static final double FUSION_BETA_FACE_VISIBLE = 0.2;
    public static final double FUSION_ALPHA_GRACE = 0.4;
    public static final double FUSION_BETA_GRACE = 0.6;
    public static final double FUSION_ALPHA_BODY_ONLY = 0.0;
    public static final double FUSION_BETA_BODY_ONLY = 1.0;

    /** Color for body-locked bounding boxes when face is lost (BGR: amber/orange). */
    public static final int[] COLOR_BODY_LOCK_BGR = {0, 165, 255};
}
