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
