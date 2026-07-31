// =============================================================
// DrishtiX: Advanced Facial Recognition & Alert System
// MongoDB Initialization Script
// Run: mongosh drishtix_db drishtix_init.js
// =============================================================

print("=== DrishtiX MongoDB Initialization ===");

// -----------------------------------------------------------
// Create indexes for the targets collection
// -----------------------------------------------------------
db.targets.createIndex({ "category": 1 });
db.targets.createIndex({ "is_active": 1 });
db.targets.createIndex({ "case_number": 1 }, { unique: true });
db.targets.createIndex({ "recognizer_label": 1 }, { unique: true });
db.targets.createIndex({ "full_name": "text", "description": "text" });
print("✓ targets indexes created");

// -----------------------------------------------------------
// Create indexes for the target_images collection
// -----------------------------------------------------------
db.target_images.createIndex({ "target_id": 1 });
print("✓ target_images indexes created");

// -----------------------------------------------------------
// Create indexes for the camera_sources collection
// -----------------------------------------------------------
db.camera_sources.createIndex({ "is_active": 1 });
print("✓ camera_sources indexes created");

// -----------------------------------------------------------
// Create indexes for the detection_logs collection
// -----------------------------------------------------------
db.detection_logs.createIndex({ "target_id": 1 });
db.detection_logs.createIndex({ "detection_timestamp": -1 });
db.detection_logs.createIndex({ "camera_id": 1 });
db.detection_logs.createIndex({ "match_confidence_score": 1 });
print("✓ detection_logs indexes created");

// -----------------------------------------------------------
// Create indexes for the alert_config collection
// -----------------------------------------------------------
db.alert_config.createIndex({ "config_key": 1 }, { unique: true });
print("✓ alert_config indexes created");

// -----------------------------------------------------------
// Create indexes for the audit_log collection
// -----------------------------------------------------------
db.audit_log.createIndex({ "action_type": 1 });
db.audit_log.createIndex({ "performed_at": -1 });
print("✓ audit_log indexes created");

// -----------------------------------------------------------
// Seed: Default camera source
// -----------------------------------------------------------
if (db.camera_sources.countDocuments({ "camera_name": "Default Webcam" }) === 0) {
    db.counters.updateOne(
        { _id: "camera_sources" },
        { $setOnInsert: { seq: 1 } },
        { upsert: true }
    );
    db.camera_sources.insertOne({
        _id: 1,
        camera_name: "Default Webcam",
        source_uri: "0",
        is_active: true,
        created_at: new Date()
    });
    print("✓ Default webcam camera source seeded");
} else {
    print("✓ Default webcam already exists, skipping");
}

// -----------------------------------------------------------
// Seed: Default configuration entries
// -----------------------------------------------------------
const configs = [
    { config_key: "confidence_threshold", config_value: "80.0", description: "LBPH distance threshold; values below this are considered a match" },
    { config_key: "alert_cooldown_seconds", config_value: "30", description: "Seconds to wait before re-alerting for the same target" },
    { config_key: "video_fps_target", config_value: "15", description: "Target frames per second for the video feed" },
    { config_key: "snapshot_retention_days", config_value: "90", description: "Number of days to retain detection snapshots" },
    { config_key: "audio_enabled", config_value: "true", description: "Whether alert sounds are enabled" },
    { config_key: "face_detection_method", config_value: "HAAR", description: "HAAR or DNN face detection algorithm" },
    { config_key: "min_face_size", config_value: "80", description: "Minimum face size in pixels for detection" },
    { config_key: "max_targets", config_value: "10000", description: "Maximum number of targets supported" },
    { config_key: "auto_start_camera", config_value: "true", description: "Auto-start laptop camera on app launch" }
];

configs.forEach(cfg => {
    db.alert_config.updateOne(
        { config_key: cfg.config_key },
        { $setOnInsert: cfg },
        { upsert: true }
    );
});
print("✓ Default configuration entries seeded (" + configs.length + " entries)");

// -----------------------------------------------------------
// Initialize counters for auto-increment IDs
// -----------------------------------------------------------
const counterDefaults = [
    { _id: "targets", seq: 0 },
    { _id: "target_images", seq: 0 },
    { _id: "detection_logs", seq: 0 },
    { _id: "audit_log", seq: 0 }
];
counterDefaults.forEach(c => {
    db.counters.updateOne(
        { _id: c._id },
        { $setOnInsert: { seq: c.seq } },
        { upsert: true }
    );
});
print("✓ Counter sequences initialized");

print("\n=== DrishtiX MongoDB initialization complete ===");
print("Collections: targets, target_images, camera_sources, detection_logs, alert_config, audit_log, counters");

// =============================================================
// DrishtiX v2.0: ReID & Push Engine Schema Updates
// Incremental — appended without modifying existing schema above
// =============================================================

print("\n=== DrishtiX v2.0 Schema Updates ===");

// -----------------------------------------------------------
// Create indexes for the person_embeddings collection (ReID)
// -----------------------------------------------------------
db.person_embeddings.createIndex({ "camera_id": 1 });
db.person_embeddings.createIndex({ "timestamp": -1 });
db.person_embeddings.createIndex({ "target_id": 1 });
print("✓ person_embeddings indexes created");

// -----------------------------------------------------------
// Initialize counter for person_embeddings auto-increment IDs
// -----------------------------------------------------------
db.counters.updateOne(
    { _id: "person_embeddings" },
    { $setOnInsert: { seq: 0 } },
    { upsert: true }
);
print("✓ person_embeddings counter initialized");

// -----------------------------------------------------------
// Seed: New configuration entries for ReID and Telegram
// -----------------------------------------------------------
const v2Configs = [
    { config_key: "reid_service_url", config_value: "http://localhost:8100", description: "URL of the Python ReID microservice" },
    { config_key: "reid_enabled", config_value: "false", description: "Enable/disable Person Re-Identification" },
    { config_key: "reid_similarity_threshold", config_value: "0.85", description: "Cosine similarity threshold for ReID match (0.0 to 1.0)" },
    { config_key: "reid_match_window", config_value: "100", description: "Number of recent embeddings to compare against" },
    { config_key: "telegram_enabled", config_value: "false", description: "Enable/disable Telegram alerts" },
    { config_key: "telegram_bot_token", config_value: "", description: "Telegram Bot API token (from @BotFather)" },
    { config_key: "telegram_chat_id", config_value: "", description: "Telegram chat/group ID for alerts" },
    { config_key: "notification_mode", config_value: "toast", description: "Desktop notification mode: toast (ControlsFX) or popup (blocking overlay)" }
];

v2Configs.forEach(cfg => {
    db.alert_config.updateOne(
        { config_key: cfg.config_key },
        { $setOnInsert: cfg },
        { upsert: true }
    );
});
print("✓ v2.0 configuration entries seeded (" + v2Configs.length + " entries)");

print("\n=== DrishtiX v2.0 schema updates complete ===");
print("New collections: person_embeddings");
print("New config keys: reid_service_url, reid_enabled, reid_similarity_threshold, reid_match_window, telegram_enabled, telegram_bot_token, telegram_chat_id, notification_mode");
