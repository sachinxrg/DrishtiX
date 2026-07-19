package com.drishtix.util;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.util.concurrent.*;

/**
 * Centralized thread pool factory for the DrishtiX three-pool architecture.
 * <p>
 * Thread Pool 1: JavaFX Application Thread (managed by JavaFX runtime — not created here)
 * Thread Pool 2: Video Inference Pool — frame capture, face detection, and recognition
 * Thread Pool 3: Audio Alert Pool — sound playback to avoid blocking video processing
 * </p>
 */
public final class ThreadPools {

    private static final Logger log = LoggerFactory.getLogger(ThreadPools.class);

    private static volatile ExecutorService videoInferencePool;
    private static volatile ExecutorService audioAlertPool;
    private static volatile ScheduledExecutorService scheduledPool;

    private ThreadPools() {
        // Utility class — no instantiation
    }

    /**
     * Returns the Video Inference thread pool (2 threads).
     * Used for camera frame capture, face detection, and recognition.
     */
    public static ExecutorService getVideoInferencePool() {
        if (videoInferencePool == null) {
            synchronized (ThreadPools.class) {
                if (videoInferencePool == null) {
                    videoInferencePool = Executors.newFixedThreadPool(2, r -> {
                        Thread t = new Thread(r, "DrishtiX-VideoInference");
                        t.setDaemon(true);
                        return t;
                    });
                    log.info("Video Inference thread pool initialized (2 threads)");
                }
            }
        }
        return videoInferencePool;
    }

    /**
     * Returns the Audio Alert thread pool (single thread).
     * Used for asynchronous sound playback.
     */
    public static ExecutorService getAudioAlertPool() {
        if (audioAlertPool == null) {
            synchronized (ThreadPools.class) {
                if (audioAlertPool == null) {
                    audioAlertPool = Executors.newSingleThreadExecutor(r -> {
                        Thread t = new Thread(r, "DrishtiX-AudioAlert");
                        t.setDaemon(true);
                        return t;
                    });
                    log.info("Audio Alert thread pool initialized (1 thread)");
                }
            }
        }
        return audioAlertPool;
    }

    /**
     * Returns a shared scheduled executor for periodic tasks (e.g., snapshot cleanup).
     */
    public static ScheduledExecutorService getScheduledPool() {
        if (scheduledPool == null) {
            synchronized (ThreadPools.class) {
                if (scheduledPool == null) {
                    scheduledPool = Executors.newScheduledThreadPool(1, r -> {
                        Thread t = new Thread(r, "DrishtiX-Scheduled");
                        t.setDaemon(true);
                        return t;
                    });
                    log.info("Scheduled thread pool initialized (1 thread)");
                }
            }
        }
        return scheduledPool;
    }

    /**
     * Gracefully shuts down all thread pools.
     * Called during application shutdown to release resources.
     */
    public static void shutdownAll() {
        log.info("Shutting down all DrishtiX thread pools...");
        shutdownPool("VideoInference", videoInferencePool);
        shutdownPool("AudioAlert", audioAlertPool);
        shutdownPool("Scheduled", scheduledPool);
        log.info("All thread pools shut down successfully");
    }

    private static void shutdownPool(String name, ExecutorService pool) {
        if (pool != null && !pool.isShutdown()) {
            pool.shutdown();
            try {
                if (!pool.awaitTermination(3, TimeUnit.SECONDS)) {
                    log.warn("{} pool did not terminate gracefully, forcing shutdown", name);
                    pool.shutdownNow();
                }
            } catch (InterruptedException e) {
                log.error("{} pool shutdown interrupted", name, e);
                pool.shutdownNow();
                Thread.currentThread().interrupt();
            }
        }
    }
}
