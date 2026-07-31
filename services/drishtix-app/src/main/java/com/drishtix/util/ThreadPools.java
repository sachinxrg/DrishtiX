package com.drishtix.util;

import com.drishtix.service.DnnFaceRecognitionService;
import org.bytedeco.opencv.opencv_core.Mat;
import static org.bytedeco.opencv.global.opencv_core.CV_8UC3;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.util.ArrayList;
import java.util.List;
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
    private static volatile ExecutorService recognitionInferencePool;
    private static volatile ScheduledExecutorService scheduledPool;
    private static volatile ScheduledExecutorService ingestionPool;

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
     * Returns the Background Ingestion thread pool (2 threads, scheduled).
     * Used for periodic web scraping and REST API polling (FBI, CBI, TrackChild).
     * Kept separate from the main scheduled pool to avoid contention.
     */
    public static ScheduledExecutorService getIngestionPool() {
        if (ingestionPool == null) {
            synchronized (ThreadPools.class) {
                if (ingestionPool == null) {
                    ingestionPool = Executors.newScheduledThreadPool(2, r -> {
                        Thread t = new Thread(r, "DrishtiX-Ingestion");
                        t.setDaemon(true);
                        t.setPriority(Thread.MIN_PRIORITY); // Low priority — don't steal CPU from inference
                        return t;
                    });
                    log.info("Ingestion thread pool initialized (2 threads, low priority)");
                }
            }
        }
        return ingestionPool;
    }

    /**
     * Returns the DNN Recognition Inference thread pool (4 threads).
     * Used for heavy DNN embedding extraction (SFace/ArcFace) to keep
     * the main capture loop responsive.
     */
    public static ExecutorService getRecognitionInferencePool() {
        if (recognitionInferencePool == null) {
            synchronized (ThreadPools.class) {
                if (recognitionInferencePool == null) {
                    recognitionInferencePool = Executors.newFixedThreadPool(4, r -> {
                        Thread t = new Thread(r, "DrishtiX-RecognitionInference");
                        t.setDaemon(true);
                        return t;
                    });
                    log.info("Recognition Inference thread pool initialized (4 threads)");
                }
            }
        }
        return recognitionInferencePool;
    }

    /**
     * Pre-warms the recognition pool by triggering ThreadLocal FaceRecognizerSF
     * initialization on all pool threads. Eliminates the ~200ms cold-start
     * penalty when the first face appears on camera.
     * <p>
     * Each pool thread creates a dummy 112x112 Mat and runs extractEmbedding()
     * to force the ThreadLocal SFace model to load.
     * </p>
     */
    public static void preWarmRecognitionPool() {
        ExecutorService pool = getRecognitionInferencePool();
        DnnFaceRecognitionService recogService = DnnFaceRecognitionService.getInstance();
        if (!recogService.isInitialized()) {
            log.warn("Cannot pre-warm recognition pool — DNN recognizer not initialized");
            return;
        }

        List<CompletableFuture<Void>> warmups = new ArrayList<>();
        for (int i = 0; i < 4; i++) {
            warmups.add(CompletableFuture.runAsync(() -> {
                Mat dummy = new Mat(112, 112, CV_8UC3);
                try {
                    recogService.extractEmbedding(dummy);
                } finally {
                    dummy.release();
                }
                log.debug("Recognition pool thread pre-warmed: {}", Thread.currentThread().getName());
            }, pool));
        }
        try {
            CompletableFuture.allOf(warmups.toArray(new CompletableFuture[0])).join();
            log.info("Recognition inference pool pre-warmed (4 threads ready)");
        } catch (Exception e) {
            log.warn("Recognition pool pre-warming failed (non-fatal)", e);
        }
    }

    /**
     * Gracefully shuts down all thread pools.
     * Called during application shutdown to release resources.
     */
    public static void shutdownAll() {
        log.info("Shutting down all DrishtiX thread pools...");
        shutdownPool("VideoInference", videoInferencePool);
        shutdownPool("AudioAlert", audioAlertPool);
        shutdownPool("RecognitionInference", recognitionInferencePool);
        shutdownPool("Scheduled", scheduledPool);
        shutdownPool("Ingestion", ingestionPool);
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
