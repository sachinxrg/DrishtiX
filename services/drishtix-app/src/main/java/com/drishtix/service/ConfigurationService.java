package com.drishtix.service;

import com.drishtix.dao.AlertConfigDAO;
import com.drishtix.util.AppConstants;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;

/**
 * Service for managing application configuration.
 * Loads configuration from the database and provides type-safe accessors.
 * Caches values in memory for fast access; refreshable on demand.
 */
public class ConfigurationService {

    private static final Logger log = LoggerFactory.getLogger(ConfigurationService.class);
    private static volatile ConfigurationService instance;

    private final AlertConfigDAO configDAO;
    private final ConcurrentHashMap<String, String> cache;

    private ConfigurationService() {
        this.configDAO = new AlertConfigDAO();
        this.cache = new ConcurrentHashMap<>();
        refresh();
    }

    public static ConfigurationService getInstance() {
        if (instance == null) {
            synchronized (ConfigurationService.class) {
                if (instance == null) {
                    instance = new ConfigurationService();
                }
            }
        }
        return instance;
    }

    /**
     * Refreshes the in-memory cache from the database.
     */
    public void refresh() {
        try {
            loadDefaults();
            Map<String, String> dbConfigs = configDAO.loadAll();
            for (Map.Entry<String, String> entry : dbConfigs.entrySet()) {
                if (entry.getValue() != null && !entry.getValue().isBlank()) {
                    cache.put(entry.getKey(), entry.getValue());
                }
            }
            log.info("Configuration refreshed — {} entries loaded from DB", dbConfigs.size());
        } catch (Exception e) {
            log.warn("Failed to refresh configuration from database — using defaults", e);
            loadDefaults();
        }
    }

    /**
     * Populates the cache with hardcoded defaults.
     * Used as a fallback when the database is unavailable at startup.
     */
    private void loadDefaults() {
        cache.putIfAbsent(AppConstants.CFG_CONFIDENCE_THRESHOLD, String.valueOf(AppConstants.DEFAULT_CONFIDENCE_THRESHOLD));
        cache.putIfAbsent(AppConstants.CFG_ALERT_COOLDOWN, String.valueOf(AppConstants.DEFAULT_COOLDOWN_SECONDS));
        cache.putIfAbsent(AppConstants.CFG_VIDEO_FPS, String.valueOf(AppConstants.DEFAULT_FPS_TARGET));
        cache.putIfAbsent(AppConstants.CFG_AUDIO_ENABLED, "true");
        cache.putIfAbsent(AppConstants.CFG_DETECTION_METHOD, "HAAR");
        cache.putIfAbsent(AppConstants.CFG_MIN_FACE_SIZE, String.valueOf(AppConstants.MIN_FACE_SIZE));
        cache.putIfAbsent(AppConstants.CFG_AUTO_START_CAMERA, "true");
        cache.putIfAbsent(AppConstants.CFG_SNAPSHOT_RETENTION, "90");
        cache.putIfAbsent(AppConstants.CFG_REID_SERVICE_URL, AppConstants.DEFAULT_REID_SERVICE_URL);
        cache.putIfAbsent(AppConstants.CFG_REID_ENABLED, "false");
        cache.putIfAbsent(AppConstants.CFG_REID_SIMILARITY_THRESHOLD, String.valueOf(AppConstants.DEFAULT_REID_SIMILARITY_THRESHOLD));
        cache.putIfAbsent(AppConstants.CFG_REID_MATCH_WINDOW, String.valueOf(AppConstants.DEFAULT_REID_MATCH_WINDOW));
        cache.putIfAbsent(AppConstants.CFG_TELEGRAM_ENABLED, "true");
        cache.putIfAbsent(AppConstants.CFG_TELEGRAM_BOT_TOKEN, "8875164831:AAHVtscV8JmXtVZbpkrKqi-sC1omdGg_S4U");
        cache.putIfAbsent(AppConstants.CFG_TELEGRAM_CHAT_ID, "-1004487763327");
        cache.putIfAbsent(AppConstants.CFG_OFFICER_EMAIL, "");
        cache.putIfAbsent(AppConstants.CFG_OFFICER_DISPATCH_ENABLED, "true");
        cache.putIfAbsent(AppConstants.CFG_NOTIFICATION_MODE, "toast");
        // DNN defaults
        cache.putIfAbsent(AppConstants.CFG_DNN_SCORE_THRESHOLD, String.valueOf(AppConstants.DEFAULT_DNN_SCORE_THRESHOLD));
        cache.putIfAbsent(AppConstants.CFG_DNN_NMS_THRESHOLD, String.valueOf(AppConstants.DEFAULT_DNN_NMS_THRESHOLD));
        cache.putIfAbsent(AppConstants.CFG_DNN_COSINE_THRESHOLD, String.valueOf(AppConstants.DEFAULT_DNN_COSINE_THRESHOLD));
        cache.putIfAbsent(AppConstants.CFG_DNN_MODEL_DIR, AppConstants.MODELS_DIR);
        // Ingestion defaults
        cache.putIfAbsent(AppConstants.CFG_INGESTION_ENABLED, "false");
        cache.putIfAbsent(AppConstants.CFG_INGESTION_INTERVAL_HOURS, String.valueOf(AppConstants.DEFAULT_INGESTION_INTERVAL_HOURS));
        cache.putIfAbsent(AppConstants.CFG_FBI_API_KEY, "");
        // Tracking defaults
        cache.putIfAbsent(AppConstants.CFG_INFERENCE_FRAME_INTERVAL, String.valueOf(AppConstants.DEFAULT_INFERENCE_FRAME_INTERVAL));
        cache.putIfAbsent(AppConstants.CFG_TRACKER_TYPE, AppConstants.DEFAULT_TRACKER_TYPE);
        log.info("Configuration defaults loaded — {} entries", cache.size());
    }

    /**
     * Updates a configuration value in both the database and cache.
     */
    public void updateConfig(String key, String value) {
        configDAO.updateValue(key, value);
        cache.put(key, value);
        log.info("Configuration updated: {} = {}", key, value);
    }

    // ==================== Type-Safe Accessors ====================

    public double getConfidenceThreshold() {
        return getDouble(AppConstants.CFG_CONFIDENCE_THRESHOLD, AppConstants.DEFAULT_CONFIDENCE_THRESHOLD);
    }

    public int getAlertCooldownSeconds() {
        return getInt(AppConstants.CFG_ALERT_COOLDOWN, AppConstants.DEFAULT_COOLDOWN_SECONDS);
    }

    public int getVideoFpsTarget() {
        return getInt(AppConstants.CFG_VIDEO_FPS, AppConstants.DEFAULT_FPS_TARGET);
    }

    public boolean isAudioEnabled() {
        return getBoolean(AppConstants.CFG_AUDIO_ENABLED, true);
    }

    public String getDetectionMethod() {
        return getString(AppConstants.CFG_DETECTION_METHOD, "HAAR");
    }

    public int getMinFaceSize() {
        return getInt(AppConstants.CFG_MIN_FACE_SIZE, AppConstants.MIN_FACE_SIZE);
    }

    public boolean isAutoStartCamera() {
        return getBoolean(AppConstants.CFG_AUTO_START_CAMERA, true);
    }

    public int getSnapshotRetentionDays() {
        return getInt(AppConstants.CFG_SNAPSHOT_RETENTION, 90);
    }

    // ==================== ReID Accessors ====================

    public String getReIDServiceUrl() {
        return getString(AppConstants.CFG_REID_SERVICE_URL, AppConstants.DEFAULT_REID_SERVICE_URL);
    }

    public boolean isReIDEnabled() {
        return getBoolean(AppConstants.CFG_REID_ENABLED, false);
    }

    public double getReIDSimilarityThreshold() {
        return getDouble(AppConstants.CFG_REID_SIMILARITY_THRESHOLD, AppConstants.DEFAULT_REID_SIMILARITY_THRESHOLD);
    }

    public int getReIDMatchWindow() {
        return getInt(AppConstants.CFG_REID_MATCH_WINDOW, AppConstants.DEFAULT_REID_MATCH_WINDOW);
    }

    // ==================== Telegram Accessors ====================

    public boolean isTelegramEnabled() {
        return getBoolean(AppConstants.CFG_TELEGRAM_ENABLED, false);
    }

    public String getTelegramBotToken() {
        return getString(AppConstants.CFG_TELEGRAM_BOT_TOKEN, "");
    }

    public String getTelegramChatId() {
        return getString(AppConstants.CFG_TELEGRAM_CHAT_ID, "");
    }

    public String getOfficerEmail() {
        return getString(AppConstants.CFG_OFFICER_EMAIL, "");
    }

    public boolean isOfficerDispatchEnabled() {
        return getBoolean(AppConstants.CFG_OFFICER_DISPATCH_ENABLED, true);
    }

    // ==================== Notification Accessors ====================

    public String getNotificationMode() {
        return getString(AppConstants.CFG_NOTIFICATION_MODE, "toast");
    }

    // ==================== DNN Accessors ====================

    public double getDnnScoreThreshold() {
        return getDouble(AppConstants.CFG_DNN_SCORE_THRESHOLD, AppConstants.DEFAULT_DNN_SCORE_THRESHOLD);
    }

    public double getDnnNmsThreshold() {
        return getDouble(AppConstants.CFG_DNN_NMS_THRESHOLD, AppConstants.DEFAULT_DNN_NMS_THRESHOLD);
    }

    public double getDnnCosineThreshold() {
        return getDouble(AppConstants.CFG_DNN_COSINE_THRESHOLD, AppConstants.DEFAULT_DNN_COSINE_THRESHOLD);
    }

    public String getDnnModelDir() {
        return getString(AppConstants.CFG_DNN_MODEL_DIR, AppConstants.MODELS_DIR);
    }

    public boolean isDnnMode() {
        return "DNN".equalsIgnoreCase(getDetectionMethod());
    }

    // ==================== Generic Accessors ====================

    public String getString(String key, String defaultValue) {
        return cache.getOrDefault(key, defaultValue);
    }

    public double getDouble(String key, double defaultValue) {
        String value = cache.get(key);
        if (value == null) return defaultValue;
        try {
            return Double.parseDouble(value);
        } catch (NumberFormatException e) {
            log.warn("Invalid double value for key {}: {}", key, value);
            return defaultValue;
        }
    }

    public int getInt(String key, int defaultValue) {
        String value = cache.get(key);
        if (value == null) return defaultValue;
        try {
            return Integer.parseInt(value);
        } catch (NumberFormatException e) {
            log.warn("Invalid int value for key {}: {}", key, value);
            return defaultValue;
        }
    }

    public boolean getBoolean(String key, boolean defaultValue) {
        String value = cache.get(key);
        if (value == null) return defaultValue;
        return Boolean.parseBoolean(value);
    }

    // ==================== Ingestion Accessors ====================

    public boolean isIngestionEnabled() {
        return getBoolean(AppConstants.CFG_INGESTION_ENABLED, false);
    }

    public int getIngestionIntervalHours() {
        return getInt(AppConstants.CFG_INGESTION_INTERVAL_HOURS, AppConstants.DEFAULT_INGESTION_INTERVAL_HOURS);
    }

    public String getFbiApiKey() {
        return getString(AppConstants.CFG_FBI_API_KEY, "");
    }

    // ==================== Tracking Accessors ====================

    public int getInferenceFrameInterval() {
        return getInt(AppConstants.CFG_INFERENCE_FRAME_INTERVAL, AppConstants.DEFAULT_INFERENCE_FRAME_INTERVAL);
    }

    public String getTrackerType() {
        return getString(AppConstants.CFG_TRACKER_TYPE, AppConstants.DEFAULT_TRACKER_TYPE);
    }
}
