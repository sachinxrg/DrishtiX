package com.drishtix.service.ingestion;

import com.drishtix.dao.TargetDAO;
import com.drishtix.dao.TargetImageDAO;
import com.drishtix.model.TargetImage;
import com.drishtix.model.TargetRegistry;
import com.drishtix.model.WantedProfile;
import com.drishtix.service.ConfigurationService;
import com.drishtix.service.DnnFaceDetectionService;
import com.drishtix.service.DnnFaceRecognitionService;
import com.drishtix.service.FaceProcessingService;
import com.drishtix.model.FaceDetection;
import com.drishtix.util.AppConstants;
import com.drishtix.util.ThreadPools;
import org.bytedeco.opencv.opencv_core.Mat;
import org.bytedeco.opencv.opencv_core.Size;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.io.File;
import java.util.*;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.ScheduledExecutorService;
import java.util.concurrent.ScheduledFuture;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicBoolean;

import static org.bytedeco.opencv.global.opencv_imgcodecs.imread;
import static org.bytedeco.opencv.global.opencv_imgproc.resize;

/**
 * Background Ingestion Engine — the master orchestrator for scheduled data sync.
 * <p>
 * Coordinates all three scrapers (FBI API, CBI HTML, TrackChild HTML) on a
 * configurable schedule (default: every 6 hours). For each downloaded profile:
 * <ol>
 *   <li>Deduplicates against known external IDs</li>
 *   <li>Runs YuNet face detection to validate the image contains a face</li>
 *   <li>Extracts SFace 128-dim embedding</li>
 *   <li>Registers as a new target in MongoDB (target_registry + target_images)</li>
 *   <li>Injects the embedding into the live in-memory gallery for immediate recognition</li>
 * </ol>
 * </p>
 * <p>
 * Thread safety: All database writes and gallery injections are serialized through
 * the existing DAO layer and ReentrantReadWriteLock in DnnFaceRecognitionService.
 * The ingestion pool threads are daemon threads with MIN_PRIORITY to avoid
 * stealing CPU from the real-time inference pipeline.
 * </p>
 */
public class BackgroundIngestionEngine {

    private static final Logger log = LoggerFactory.getLogger(BackgroundIngestionEngine.class);
    private static volatile BackgroundIngestionEngine instance;

    private final FbiWantedApiClient fbiClient;
    private final CbiWantedScraper cbiScraper;
    private final TrackChildScraper trackChildScraper;

    private final TargetDAO targetDAO;
    private final TargetImageDAO targetImageDAO;

    /** Set of external IDs already processed — prevents duplicate registration */
    private final Set<String> processedExternalIds = ConcurrentHashMap.newKeySet();

    private final AtomicBoolean running = new AtomicBoolean(false);
    private ScheduledFuture<?> scheduledTask;

    private BackgroundIngestionEngine() {
        this.fbiClient = new FbiWantedApiClient();
        this.cbiScraper = new CbiWantedScraper();
        this.trackChildScraper = new TrackChildScraper();
        this.targetDAO = new TargetDAO();
        this.targetImageDAO = new TargetImageDAO();

        ensureDirectories();
        loadProcessedIds();
    }

    public static BackgroundIngestionEngine getInstance() {
        if (instance == null) {
            synchronized (BackgroundIngestionEngine.class) {
                if (instance == null) {
                    instance = new BackgroundIngestionEngine();
                }
            }
        }
        return instance;
    }

    /**
     * Starts the scheduled ingestion cycle.
     * <p>
     * Runs an initial sync after a 60-second startup delay (to let the UI and
     * camera initialize first), then repeats every N hours as configured.
     * </p>
     */
    public void start() {
        if (!ConfigurationService.getInstance().isIngestionEnabled()) {
            log.info("[Ingestion] Background ingestion is DISABLED via configuration");
            return;
        }

        if (running.getAndSet(true)) {
            log.warn("[Ingestion] Engine already running");
            return;
        }

        int intervalHours = ConfigurationService.getInstance().getIngestionIntervalHours();
        ScheduledExecutorService pool = ThreadPools.getIngestionPool();

        // Initial delay of 60 seconds — let the UI and camera threads stabilize first
        scheduledTask = pool.scheduleAtFixedRate(
                this::runIngestionCycle,
                60,                          // initial delay (seconds)
                intervalHours * 3600L,       // period (seconds)
                TimeUnit.SECONDS
        );

        log.info("[Ingestion] Background ingestion engine STARTED — interval: {} hours, initial delay: 60s",
                intervalHours);
    }

    /**
     * Stops the scheduled ingestion cycle.
     */
    public void stop() {
        running.set(false);
        if (scheduledTask != null && !scheduledTask.isCancelled()) {
            scheduledTask.cancel(false); // Don't interrupt if currently running
            log.info("[Ingestion] Background ingestion engine STOPPED");
        }
    }

    /**
     * Returns true if the ingestion engine is currently running.
     */
    public boolean isRunning() {
        return running.get();
    }

    /**
     * Executes one full ingestion cycle across all three data sources.
     * <p>
     * This method is called by the scheduled executor and must be exception-safe
     * (a thrown exception would cancel the scheduled future).
     * </p>
     */
    private void runIngestionCycle() {
        log.info("[Ingestion] === Starting ingestion cycle ===");
        long startTime = System.currentTimeMillis();
        int totalIngested = 0;

        try {
            // ========== FBI Wanted API ==========
            try {
                List<WantedProfile> fbiProfiles = fbiClient.fetchWantedProfiles();
                int fbiIngested = processProfiles(fbiProfiles);
                totalIngested += fbiIngested;
                log.info("[Ingestion] FBI: {}/{} profiles ingested (new/total)", fbiIngested, fbiProfiles.size());
            } catch (Exception e) {
                log.error("[Ingestion] FBI ingestion failed", e);
            }

            // Rate limit between source switches
            Thread.sleep(AppConstants.INGESTION_RATE_LIMIT_MS);

            // ========== CBI Wanted List ==========
            try {
                List<WantedProfile> cbiProfiles = cbiScraper.scrapeWantedProfiles();
                int cbiIngested = processProfiles(cbiProfiles);
                totalIngested += cbiIngested;
                log.info("[Ingestion] CBI: {}/{} profiles ingested (new/total)", cbiIngested, cbiProfiles.size());
            } catch (Exception e) {
                log.error("[Ingestion] CBI ingestion failed", e);
            }

            // Rate limit between source switches
            Thread.sleep(AppConstants.INGESTION_RATE_LIMIT_MS);

            // ========== TrackChild Missing Children ==========
            try {
                List<WantedProfile> tcProfiles = trackChildScraper.scrapeMissingChildren();
                int tcIngested = processProfiles(tcProfiles);
                totalIngested += tcIngested;
                log.info("[Ingestion] TrackChild: {}/{} profiles ingested (new/total)", tcIngested, tcProfiles.size());
            } catch (Exception e) {
                log.error("[Ingestion] TrackChild ingestion failed", e);
            }

        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
            log.warn("[Ingestion] Ingestion cycle interrupted");
        } catch (Exception e) {
            log.error("[Ingestion] Unexpected error during ingestion cycle", e);
        }

        long elapsed = System.currentTimeMillis() - startTime;
        log.info("[Ingestion] === Cycle complete: {} profiles ingested in {}s ===",
                totalIngested, elapsed / 1000);
    }

    /**
     * Processes a batch of scraped profiles: deduplicates, validates faces,
     * extracts embeddings, registers targets, and injects into the live gallery.
     *
     * @return number of successfully ingested new profiles
     */
    private int processProfiles(List<WantedProfile> profiles) {
        int ingested = 0;

        for (WantedProfile profile : profiles) {
            try {
                // Skip if already processed
                if (profile.getExternalId() == null || processedExternalIds.contains(profile.getExternalId())) {
                    continue;
                }

                // Skip if no local image was downloaded
                if (profile.getLocalImagePath() == null || !new File(profile.getLocalImagePath()).exists()) {
                    continue;
                }

                // Validate face exists in the image
                float[] embedding = validateAndExtractEmbedding(profile.getLocalImagePath());
                if (embedding == null) {
                    log.debug("[Ingestion] No face detected in image for: {}", profile.getFullName());
                    continue;
                }

                // Register as a new target
                int targetId = registerTarget(profile);
                if (targetId <= 0) {
                    continue;
                }

                // Inject embedding into the live gallery for immediate recognition
                DnnFaceRecognitionService dnnService = DnnFaceRecognitionService.getInstance();
                if (dnnService.isInitialized()) {
                    dnnService.injectEmbedding(targetId, embedding);
                    log.info("[Ingestion] Embedding injected for target {}: {} (source: {})",
                            targetId, profile.getFullName(), profile.getSourceAgency());
                }

                // Mark as processed
                processedExternalIds.add(profile.getExternalId());
                ingested++;

            } catch (Exception e) {
                log.warn("[Ingestion] Failed to process profile {}: {}",
                        profile.getFullName(), e.getMessage());
            }
        }

        return ingested;
    }

    /**
     * Validates that the image contains a detectable face, then extracts
     * the SFace 128-dimensional embedding.
     *
     * @param imagePath path to the downloaded face image
     * @return the embedding float array, or null if no face found
     */
    private float[] validateAndExtractEmbedding(String imagePath) {
        DnnFaceDetectionService detector = DnnFaceDetectionService.getInstance();
        DnnFaceRecognitionService recognizer = DnnFaceRecognitionService.getInstance();

        if (!detector.isInitialized() || !recognizer.isInitialized()) {
            log.warn("[Ingestion] DNN services not initialized — skipping embedding extraction");
            return null;
        }

        Mat img = imread(imagePath);
        if (img.empty()) {
            img.release();
            return null;
        }

        try {
            // Detect faces
            List<FaceDetection> faces = detector.detectFaces(img);
            if (faces.isEmpty()) {
                return null;
            }

            // Use the first (largest/most confident) face
            FaceDetection bestFace = faces.get(0);

            // Align face to 112×112 for SFace
            Mat alignedFace = FaceProcessingService.getInstance().alignFaceForDnn(img, bestFace);
            if (alignedFace == null) {
                return null;
            }

            try {
                return recognizer.extractEmbedding(alignedFace);
            } finally {
                alignedFace.release();
            }

        } finally {
            img.release();
        }
    }

    /**
     * Registers a scraped profile as a new target in the database.
     *
     * @return the generated target ID, or -1 on failure
     */
    private int registerTarget(WantedProfile profile) {
        try {
            int recognizerLabel = targetDAO.getNextRecognizerLabel();

            TargetRegistry target = new TargetRegistry(
                    profile.getFullName(),
                    profile.getCategory(),
                    profile.getCaseNumber(),
                    profile.getDescription() + " [Source: " + profile.getSourceAgency() + "]",
                    profile.getLocalImagePath(),
                    recognizerLabel
            );

            int targetId = targetDAO.insert(target);

            // Also create a target_images entry
            TargetImage image = new TargetImage(
                    targetId,
                    profile.getLocalImagePath(),
                    profile.getLocalImagePath(), // Use same as template for scraped images
                    1
            );
            targetImageDAO.insert(image);

            log.info("[Ingestion] Target registered: id={}, name={}, source={}, category={}",
                    targetId, profile.getFullName(), profile.getSourceAgency(), profile.getCategory());

            return targetId;

        } catch (Exception e) {
            log.error("[Ingestion] Failed to register target: {}", profile.getFullName(), e);
            return -1;
        }
    }

    /**
     * Loads previously processed external IDs from existing targets in the database.
     * Looks for the [Source: XXX] pattern in the description field.
     */
    private void loadProcessedIds() {
        try {
            List<TargetRegistry> allTargets = targetDAO.findAll();
            for (TargetRegistry target : allTargets) {
                String desc = target.getDescription();
                if (desc != null && desc.contains("[Source:")) {
                    // Extract a synthetic external ID from existing scraped targets
                    String syntheticId = target.getFullName() + "_" + target.getCaseNumber();
                    processedExternalIds.add(String.valueOf(Math.abs(syntheticId.hashCode())));
                }
            }
            log.info("[Ingestion] Loaded {} previously processed external IDs", processedExternalIds.size());
        } catch (Exception e) {
            log.warn("[Ingestion] Failed to load processed IDs from database", e);
        }
    }

    /**
     * Ensures all ingestion directories exist.
     */
    private void ensureDirectories() {
        new File(AppConstants.INGESTION_DIR).mkdirs();
        new File(AppConstants.INGESTION_FBI_DIR).mkdirs();
        new File(AppConstants.INGESTION_CBI_DIR).mkdirs();
        new File(AppConstants.INGESTION_TRACKCHILD_DIR).mkdirs();
    }
}
