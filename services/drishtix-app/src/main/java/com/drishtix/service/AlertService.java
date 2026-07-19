package com.drishtix.service;

import com.drishtix.model.TargetCategory;
import com.drishtix.util.AppConstants;
import com.drishtix.util.ThreadPools;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import javax.sound.sampled.*;
import java.io.BufferedInputStream;
import java.io.InputStream;
import java.time.Instant;
import java.util.EnumMap;
import java.util.Map;
import java.util.concurrent.CompletableFuture;
import java.util.concurrent.ConcurrentHashMap;

/**
 * Service handling audible alert playback and alert cooldown management.
 * <p>
 * Preloads WAV audio clips at startup for instant playback.
 * Uses the Audio Alert thread pool to avoid blocking the Video Inference pipeline.
 * Implements per-target cooldown to prevent alert fatigue.
 * </p>
 */
public class AlertService {

    private static final Logger log = LoggerFactory.getLogger(AlertService.class);
    private static volatile AlertService instance;

    /** Preloaded audio clips per category. */
    private final Map<TargetCategory, byte[]> audioData;

    /** Tracks the last alert time per target_id for cooldown enforcement. */
    private final ConcurrentHashMap<Integer, Instant> lastAlertTimes;

    /** Whether audio alerts are currently enabled (mute toggle). */
    private volatile boolean audioEnabled;

    private AlertService() {
        this.audioData = new EnumMap<>(TargetCategory.class);
        this.lastAlertTimes = new ConcurrentHashMap<>();
        this.audioEnabled = ConfigurationService.getInstance().isAudioEnabled();
        preloadAudio();
    }

    public static AlertService getInstance() {
        if (instance == null) {
            synchronized (AlertService.class) {
                if (instance == null) {
                    instance = new AlertService();
                }
            }
        }
        return instance;
    }

    /**
     * Triggers an alert for a detected target, respecting the cooldown window.
     * Plays the audio asynchronously on the Audio Alert thread pool.
     *
     * @param targetId the ID of the detected target
     * @param category the category (determines sound type)
     * @return true if the alert was triggered, false if suppressed by cooldown
     */
    public boolean triggerAlert(int targetId, TargetCategory category) {
        if (!shouldAlert(targetId)) {
            log.debug("Alert suppressed for target {} (cooldown active)", targetId);
            return false;
        }

        // Record alert time
        lastAlertTimes.put(targetId, Instant.now());

        // Play sound asynchronously on the audio thread pool
        if (audioEnabled) {
            CompletableFuture.runAsync(() -> playSound(category), ThreadPools.getAudioAlertPool())
                    .exceptionally(ex -> {
                        log.error("Audio playback failed for category: {}", category, ex);
                        return null;
                    });
        }

        log.info("ALERT TRIGGERED: targetId={}, category={}", targetId, category);
        return true;
    }

    /**
     * Checks whether an alert should fire for the given target,
     * based on the cooldown window.
     */
    public boolean shouldAlert(int targetId) {
        Instant lastAlert = lastAlertTimes.get(targetId);
        if (lastAlert == null) {
            return true;
        }

        int cooldownSeconds = ConfigurationService.getInstance().getAlertCooldownSeconds();
        return Instant.now().isAfter(lastAlert.plusSeconds(cooldownSeconds));
    }

    /**
     * Toggles the audio mute state.
     */
    public void toggleMute() {
        audioEnabled = !audioEnabled;
        log.info("Audio alerts {}", audioEnabled ? "ENABLED" : "MUTED");
    }

    public boolean isAudioEnabled() {
        return audioEnabled;
    }

    public void setAudioEnabled(boolean enabled) {
        this.audioEnabled = enabled;
    }

    /**
     * Clears the cooldown state for all targets.
     */
    public void resetCooldowns() {
        lastAlertTimes.clear();
        log.info("Alert cooldowns reset");
    }

    /**
     * Plays the alert sound for the given category.
     * This method runs on the Audio Alert thread pool.
     */
    private void playSound(TargetCategory category) {
        byte[] data = audioData.get(category);
        if (data == null) {
            log.warn("No audio data loaded for category: {}", category);
            return;
        }

        try {
            InputStream bais = new java.io.ByteArrayInputStream(data);
            BufferedInputStream bis = new BufferedInputStream(bais);
            AudioInputStream audioStream = AudioSystem.getAudioInputStream(bis);
            Clip clip = AudioSystem.getClip();
            clip.open(audioStream);

            clip.addLineListener(event -> {
                if (event.getType() == LineEvent.Type.STOP) {
                    clip.close();
                }
            });

            clip.start();
            log.debug("Playing alert sound for category: {}", category);

        } catch (Exception e) {
            log.error("Failed to play sound for category: {}", category, e);
        }
    }

    /**
     * Preloads WAV audio files into memory at startup for instant playback.
     */
    private void preloadAudio() {
        loadAudioData(TargetCategory.CRIMINAL, AppConstants.SOUND_CRIMINAL_ALARM);
        loadAudioData(TargetCategory.MISSING_PERSON, AppConstants.SOUND_MISSING_CHIME);
    }

    private void loadAudioData(TargetCategory category, String resourcePath) {
        try (InputStream is = getClass().getClassLoader().getResourceAsStream(resourcePath)) {
            if (is != null) {
                audioData.put(category, is.readAllBytes());
                log.info("Audio preloaded for {}: {}", category, resourcePath);
            } else {
                log.warn("Audio resource not found: {} — alerts for {} will be silent", resourcePath, category);
            }
        } catch (Exception e) {
            log.error("Failed to preload audio for {}", category, e);
        }
    }
}
