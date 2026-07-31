package com.drishtix.service;

import com.drishtix.model.ReIDMatch;
import com.drishtix.model.RecognitionResult;
import com.drishtix.model.TargetCategory;
import com.drishtix.model.TargetRegistry;
import javafx.application.Platform;
import javafx.geometry.Pos;
import javafx.scene.image.Image;
import javafx.scene.image.ImageView;
import javafx.util.Duration;
import org.controlsfx.control.Notifications;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.io.File;

/**
 * Service for non-blocking desktop notification toasts using ControlsFX.
 * <p>
 * Replaces the blocking popup overlay with smooth sliding notifications
 * that appear in the bottom-right corner and auto-dismiss after 8 seconds.
 * Notifications stack vertically when multiple alerts arrive simultaneously.
 * </p>
 * <p>
 * All notification methods ensure thread-safety by dispatching to the
 * JavaFX Application Thread via {@link Platform#runLater(Runnable)}.
 * </p>
 */
public class NotificationService {

    private static final Logger log = LoggerFactory.getLogger(NotificationService.class);
    private static volatile NotificationService instance;

    /** Default auto-dismiss duration for notifications. */
    private static final Duration DEFAULT_HIDE_AFTER = Duration.seconds(8);

    private NotificationService() {
        // Singleton
    }

    public static NotificationService getInstance() {
        if (instance == null) {
            synchronized (NotificationService.class) {
                if (instance == null) {
                    instance = new NotificationService();
                }
            }
        }
        return instance;
    }

    /**
     * Shows a detection alert notification with target details and snapshot thumbnail.
     *
     * @param target       the matched target from the watchlist
     * @param result       the recognition result with confidence score
     * @param snapshotPath path to the detection snapshot image (may be null)
     */
    public void showDetectionAlert(TargetRegistry target, RecognitionResult result, String snapshotPath) {
        if (target == null) return;

        Platform.runLater(() -> {
            try {
                boolean isCriminal = target.getCategory() == TargetCategory.CRIMINAL;

                String title = isCriminal
                        ? "⚠ CRIMINAL DETECTED"
                        : "🔵 MISSING PERSON FOUND";

                String text = String.format(
                        "Name: %s\nCase #: %s\nConfidence: %s\nCategory: %s",
                        target.getFullName(),
                        target.getCaseNumber(),
                        result != null ? result.getConfidencePercentage() : "N/A",
                        target.getCategory().getDbValue()
                );

                Notifications notification = Notifications.create()
                        .title(title)
                        .text(text)
                        .position(Pos.BOTTOM_RIGHT)
                        .hideAfter(DEFAULT_HIDE_AFTER)
                        .darkStyle();

                // Add snapshot thumbnail if available
                ImageView thumbnail = createThumbnail(snapshotPath);
                if (thumbnail != null) {
                    notification.graphic(thumbnail);
                }

                // Show appropriate notification style
                if (isCriminal) {
                    notification.showError();
                } else {
                    notification.showInformation();
                }

                log.debug("Desktop notification shown for target: {}", target.getFullName());

            } catch (Exception e) {
                log.warn("Failed to show desktop notification: {}", e.getMessage());
            }
        });
    }

    /**
     * Shows a ReID cross-camera match notification.
     *
     * @param match the ReID match event with similarity score
     */
    public void showReIDAlert(ReIDMatch match) {
        if (match == null) return;

        Platform.runLater(() -> {
            try {
                String title = "🔄 PERSON RE-IDENTIFIED";

                String text = String.format(
                        "Same person detected across cameras!\n" +
                        "Camera %s → Camera %s\n" +
                        "Similarity: %s",
                        match.getSourceCameraId() != null ? match.getSourceCameraId() : "?",
                        match.getMatchedCameraId() != null ? match.getMatchedCameraId() : "?",
                        match.getSimilarityPercentage()
                );

                Notifications notification = Notifications.create()
                        .title(title)
                        .text(text)
                        .position(Pos.BOTTOM_RIGHT)
                        .hideAfter(DEFAULT_HIDE_AFTER)
                        .darkStyle();

                // Add snapshot thumbnail from the source detection
                if (match.getSourceEmbedding() != null) {
                    ImageView thumbnail = createThumbnail(match.getSourceEmbedding().getSnapshotPath());
                    if (thumbnail != null) {
                        notification.graphic(thumbnail);
                    }
                }

                notification.showWarning();

                log.debug("ReID notification shown: {}", match);

            } catch (Exception e) {
                log.warn("Failed to show ReID notification: {}", e.getMessage());
            }
        });
    }

    /**
     * Shows a generic information notification.
     *
     * @param title notification title
     * @param text  notification body
     */
    public void showInfo(String title, String text) {
        Platform.runLater(() -> {
            try {
                Notifications.create()
                        .title(title)
                        .text(text)
                        .position(Pos.BOTTOM_RIGHT)
                        .hideAfter(DEFAULT_HIDE_AFTER)
                        .darkStyle()
                        .showInformation();
            } catch (Exception e) {
                log.warn("Failed to show info notification: {}", e.getMessage());
            }
        });
    }

    /**
     * Shows an error notification.
     *
     * @param title notification title
     * @param text  notification body
     */
    public void showError(String title, String text) {
        Platform.runLater(() -> {
            try {
                Notifications.create()
                        .title(title)
                        .text(text)
                        .position(Pos.BOTTOM_RIGHT)
                        .hideAfter(Duration.seconds(12))
                        .darkStyle()
                        .showError();
            } catch (Exception e) {
                log.warn("Failed to show error notification: {}", e.getMessage());
            }
        });
    }

    /**
     * Creates a 64x64 thumbnail ImageView from a snapshot file path.
     *
     * @return the thumbnail ImageView, or null if the file doesn't exist
     */
    private ImageView createThumbnail(String snapshotPath) {
        if (snapshotPath == null || snapshotPath.isBlank()) return null;

        try {
            File file = new File(snapshotPath);
            if (!file.exists()) return null;

            Image image = new Image(file.toURI().toString(), 64, 64, true, true);
            ImageView imageView = new ImageView(image);
            imageView.setFitWidth(64);
            imageView.setFitHeight(64);
            imageView.setPreserveRatio(true);
            return imageView;

        } catch (Exception e) {
            log.warn("Failed to create notification thumbnail: {}", e.getMessage());
            return null;
        }
    }
}
