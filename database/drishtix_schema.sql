-- =============================================================
-- DrishtiX: Advanced Facial Recognition & Alert System
-- Database Initialization Script — MySQL 8.0+
-- =============================================================

CREATE DATABASE IF NOT EXISTS drishtix_db
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

USE drishtix_db;

-- -----------------------------------------------------------
-- Table 1: target_registry — Core watchlist entries
-- -----------------------------------------------------------
CREATE TABLE IF NOT EXISTS target_registry (
    target_id        INT             AUTO_INCREMENT PRIMARY KEY,
    full_name        VARCHAR(150)    NOT NULL,
    category         ENUM('CRIMINAL', 'MISSING_PERSON') NOT NULL,
    case_number      VARCHAR(50)     NOT NULL UNIQUE,
    description      TEXT            DEFAULT NULL,
    profile_image_path VARCHAR(500)  NOT NULL COMMENT 'Path to the primary uploaded photo',
    is_active        BOOLEAN         NOT NULL DEFAULT TRUE,
    recognizer_label INT             NOT NULL UNIQUE COMMENT 'Unique integer label for LBPH recognizer',
    created_at       TIMESTAMP       NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at       TIMESTAMP       NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    INDEX idx_category (category),
    INDEX idx_is_active (is_active),
    INDEX idx_case_number (case_number),
    FULLTEXT INDEX ft_name_desc (full_name, description)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- -----------------------------------------------------------
-- Table 2: target_images — Multiple photos per target
-- -----------------------------------------------------------
CREATE TABLE IF NOT EXISTS target_images (
    image_id         INT             AUTO_INCREMENT PRIMARY KEY,
    target_id        INT             NOT NULL,
    image_path       VARCHAR(500)    NOT NULL COMMENT 'Path to the original uploaded image',
    template_path    VARCHAR(500)    DEFAULT NULL COMMENT 'Path to the preprocessed grayscale face ROI',
    image_order      INT             NOT NULL DEFAULT 1 CHECK (image_order BETWEEN 1 AND 5),
    uploaded_at      TIMESTAMP       NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT fk_target_images_target
        FOREIGN KEY (target_id) REFERENCES target_registry(target_id)
        ON DELETE CASCADE ON UPDATE CASCADE,
    
    INDEX idx_target_id (target_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- -----------------------------------------------------------
-- Table 3: camera_sources — Registered camera feeds
-- -----------------------------------------------------------
CREATE TABLE IF NOT EXISTS camera_sources (
    camera_id        INT             AUTO_INCREMENT PRIMARY KEY,
    camera_name      VARCHAR(100)    NOT NULL,
    source_uri       VARCHAR(500)    NOT NULL COMMENT 'Device index (0,1,...) or RTSP URL',
    is_active        BOOLEAN         NOT NULL DEFAULT TRUE,
    created_at       TIMESTAMP       NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_camera_active (is_active)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

INSERT INTO camera_sources (camera_name, source_uri) VALUES ('Default Webcam', '0')
    ON DUPLICATE KEY UPDATE camera_name = camera_name;

-- -----------------------------------------------------------
-- Table 4: detection_logs — Historical sighting records
-- -----------------------------------------------------------
CREATE TABLE IF NOT EXISTS detection_logs (
    log_id               BIGINT          AUTO_INCREMENT PRIMARY KEY,
    target_id            INT             NOT NULL,
    detection_timestamp  TIMESTAMP       NOT NULL DEFAULT CURRENT_TIMESTAMP,
    match_confidence_score DOUBLE        NOT NULL COMMENT 'LBPH distance; lower = better match',
    snapshot_path        VARCHAR(500)    DEFAULT NULL COMMENT 'Path to the annotated frame snapshot',
    camera_id            INT             DEFAULT NULL,
    location_tag         VARCHAR(100)    DEFAULT NULL,
    created_at           TIMESTAMP       NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT fk_detection_target
        FOREIGN KEY (target_id) REFERENCES target_registry(target_id)
        ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_detection_camera
        FOREIGN KEY (camera_id) REFERENCES camera_sources(camera_id)
        ON DELETE SET NULL ON UPDATE CASCADE,
    
    INDEX idx_detection_target (target_id),
    INDEX idx_detection_timestamp (detection_timestamp),
    INDEX idx_detection_camera (camera_id),
    INDEX idx_confidence (match_confidence_score)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- -----------------------------------------------------------
-- Table 5: alert_config — Application configuration store
-- -----------------------------------------------------------
CREATE TABLE IF NOT EXISTS alert_config (
    config_id        INT             AUTO_INCREMENT PRIMARY KEY,
    config_key       VARCHAR(50)     NOT NULL UNIQUE,
    config_value     VARCHAR(500)    NOT NULL,
    description      TEXT            DEFAULT NULL,
    updated_at       TIMESTAMP       NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

INSERT INTO alert_config (config_key, config_value, description) VALUES
    ('confidence_threshold', '80.0', 'LBPH distance threshold; values below this are considered a match'),
    ('alert_cooldown_seconds', '30', 'Seconds to wait before re-alerting for the same target'),
    ('video_fps_target', '15', 'Target frames per second for the video feed'),
    ('snapshot_retention_days', '90', 'Number of days to retain detection snapshots'),
    ('audio_enabled', 'true', 'Whether alert sounds are enabled'),
    ('face_detection_method', 'HAAR', 'HAAR or DNN face detection algorithm'),
    ('min_face_size', '80', 'Minimum face size in pixels for detection'),
    ('max_targets', '10000', 'Maximum number of targets supported'),
    ('auto_start_camera', 'true', 'Auto-start laptop camera on app launch')
ON DUPLICATE KEY UPDATE config_value = VALUES(config_value);

-- -----------------------------------------------------------
-- Table 6: audit_log — Administrative action tracking
-- -----------------------------------------------------------
CREATE TABLE IF NOT EXISTS audit_log (
    audit_id         BIGINT          AUTO_INCREMENT PRIMARY KEY,
    action_type      VARCHAR(100)    NOT NULL COMMENT 'e.g., TARGET_ADDED, TARGET_DEACTIVATED, ALERT_ACKNOWLEDGED',
    target_id        INT             DEFAULT NULL,
    performed_by     VARCHAR(100)    NOT NULL DEFAULT 'SYSTEM',
    details          TEXT            DEFAULT NULL COMMENT 'JSON-serialized action details',
    performed_at     TIMESTAMP       NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT fk_audit_target
        FOREIGN KEY (target_id) REFERENCES target_registry(target_id)
        ON DELETE SET NULL ON UPDATE CASCADE,
    
    INDEX idx_audit_action (action_type),
    INDEX idx_audit_timestamp (performed_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- -----------------------------------------------------------
-- Views for commonly used queries
-- -----------------------------------------------------------
CREATE OR REPLACE VIEW v_active_targets AS
SELECT 
    tr.target_id,
    tr.full_name,
    tr.category,
    tr.case_number,
    tr.description,
    tr.profile_image_path,
    tr.recognizer_label,
    tr.created_at,
    COUNT(ti.image_id) AS photo_count
FROM target_registry tr
LEFT JOIN target_images ti ON tr.target_id = ti.target_id
WHERE tr.is_active = TRUE
GROUP BY tr.target_id;

CREATE OR REPLACE VIEW v_recent_detections AS
SELECT 
    dl.log_id,
    dl.detection_timestamp,
    dl.match_confidence_score,
    dl.snapshot_path,
    tr.full_name,
    tr.category,
    tr.case_number,
    cs.camera_name,
    dl.location_tag
FROM detection_logs dl
JOIN target_registry tr ON dl.target_id = tr.target_id
LEFT JOIN camera_sources cs ON dl.camera_id = cs.camera_id
ORDER BY dl.detection_timestamp DESC;

CREATE OR REPLACE VIEW v_detection_stats AS
SELECT 
    tr.target_id,
    tr.full_name,
    tr.category,
    COUNT(dl.log_id) AS total_detections,
    MIN(dl.detection_timestamp) AS first_seen,
    MAX(dl.detection_timestamp) AS last_seen,
    AVG(dl.match_confidence_score) AS avg_confidence
FROM target_registry tr
LEFT JOIN detection_logs dl ON tr.target_id = dl.target_id
WHERE tr.is_active = TRUE
GROUP BY tr.target_id;
