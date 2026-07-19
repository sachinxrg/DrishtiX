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
            Map<String, String> dbConfigs = configDAO.loadAll();
            cache.clear();
            cache.putAll(dbConfigs);
            log.info("Configuration refreshed — {} entries loaded", cache.size());
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
}
