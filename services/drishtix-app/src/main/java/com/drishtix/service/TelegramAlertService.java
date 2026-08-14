package com.drishtix.service;

import com.drishtix.model.TargetCategory;
import com.drishtix.model.TargetRegistry;
import com.drishtix.util.MultipartBodyBuilder;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.io.File;
import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Duration;
import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;
import java.util.concurrent.CompletableFuture;

import javax.net.ssl.SSLContext;
import javax.net.ssl.TrustManager;
import javax.net.ssl.X509TrustManager;
import java.security.SecureRandom;
import java.security.cert.X509Certificate;

/**
 * Service for sending alert notifications to Telegram via the Bot API.
 * <p>
 * Uses Java 11's {@link HttpClient} to send photo messages containing
 * the detection snapshot and formatted details (target name, category,
 * camera location, confidence score, timestamp).
 * </p>
 * <p>
 * All Telegram calls are fully asynchronous and fire-and-forget.
 * If the Telegram API is unreachable or misconfigured, the service
 * logs a warning and continues without affecting the main application.
 * </p>
 */
public class TelegramAlertService {

    private static final Logger log = LoggerFactory.getLogger(TelegramAlertService.class);
    private static volatile TelegramAlertService instance;

    private static final String TELEGRAM_API_BASE = "https://api.telegram.org/bot";
    private static final DateTimeFormatter TIMESTAMP_FMT =
            DateTimeFormatter.ofPattern("HH:mm:ss dd-MMM-yyyy");

    private final HttpClient httpClient;

    private TelegramAlertService() {
        this.httpClient = HttpClient.newBuilder()
                .version(HttpClient.Version.HTTP_1_1)
                .connectTimeout(Duration.ofSeconds(10))
                .build();
    }

    public static TelegramAlertService getInstance() {
        if (instance == null) {
            synchronized (TelegramAlertService.class) {
                if (instance == null) {
                    instance = new TelegramAlertService();
                }
            }
        }
        return instance;
    }

    /**
     * Sends a detection alert photo message to Telegram.
     * <p>
     * The message includes the detection snapshot as a photo and a caption
     * with all relevant detection details.
     * </p>
     *
     * @param target       the matched target
     * @param confidence   the match confidence percentage string
     * @param snapshotPath path to the detection snapshot image
     * @param cameraName   the camera name/location
     * @param locationTag  the location tag (may be null)
     * @return a future containing true on success, false on failure
     */
    public CompletableFuture<Boolean> sendDetectionAlert(
            TargetRegistry target, String confidence,
            String snapshotPath, String cameraName, String locationTag) {

        ConfigurationService config = ConfigurationService.getInstance();

        if (!config.isTelegramEnabled()) {
            log.debug("Telegram alerts disabled, skipping");
            return CompletableFuture.completedFuture(false);
        }

        String botToken = config.getTelegramBotToken();
        String chatId = config.getTelegramChatId();

        if (botToken == null || botToken.isBlank() || chatId == null || chatId.isBlank()) {
            log.warn("Telegram bot token or chat ID not configured");
            return CompletableFuture.completedFuture(false);
        }

        // Build the caption
        String emoji = target.getCategory() == TargetCategory.CRIMINAL ? "🚨" : "🔵";
        String alertType = target.getCategory() == TargetCategory.CRIMINAL
                ? "CRIMINAL DETECTED" : "MISSING PERSON FOUND";

        StringBuilder caption = new StringBuilder();
        caption.append(emoji).append(" <b>OFFICER DISPATCH: ").append(alertType).append("</b> ").append(emoji).append("\n\n");
        caption.append("👤 <b>Name:</b> ").append(escapeHtml(target.getFullName())).append("\n");
        caption.append("📋 <b>Category:</b> ").append(escapeHtml(target.getCategory().getDbValue())).append("\n");
        caption.append("🔢 <b>FIR / Case #:</b> ").append(escapeHtml(target.getCaseNumber())).append("\n");
        if (target.getDescription() != null && !target.getDescription().isBlank()) {
            caption.append("📜 <b>FIR Description:</b> ").append(escapeHtml(target.getDescription())).append("\n");
        }
        if (target.getCreatedAt() != null) {
            DateTimeFormatter dateFmt = DateTimeFormatter.ofPattern("dd/MM/yyyy HH:mm");
            caption.append("📅 <b>Date of FIR:</b> ").append(target.getCreatedAt().format(dateFmt)).append("\n");
        }
        caption.append("📊 <b>Match Confidence:</b> ").append(escapeHtml(confidence)).append("\n");
        if (cameraName != null && !cameraName.isBlank()) {
            caption.append("📷 <b>Camera Source:</b> ").append(escapeHtml(cameraName)).append("\n");
        }
        if (locationTag != null && !locationTag.isBlank()) {
            caption.append("📍 <b>Location:</b> ").append(escapeHtml(locationTag)).append("\n");
        }
        caption.append("🕐 <b>Detection Time:</b> ").append(LocalDateTime.now().format(TIMESTAMP_FMT)).append("\n");
        caption.append("\n🔒 <i>DrishtiX Automated Officer Dispatch System</i>");

        // Send photo if snapshot exists, otherwise send text message
        if (snapshotPath != null && new File(snapshotPath).exists()) {
            return sendPhotoMessage(botToken, chatId, snapshotPath, caption.toString());
        } else {
            return sendTextMessage(botToken, chatId, caption.toString());
        }
    }

    /**
     * Sends a ReID cross-camera match alert to Telegram.
     */
    public CompletableFuture<Boolean> sendReIDAlert(
            String snapshotPath, int sourceCameraId, int matchedCameraId, double similarity) {

        ConfigurationService config = ConfigurationService.getInstance();

        if (!config.isTelegramEnabled()) {
            return CompletableFuture.completedFuture(false);
        }

        String botToken = config.getTelegramBotToken();
        String chatId = config.getTelegramChatId();

        if (botToken == null || botToken.isBlank() || chatId == null || chatId.isBlank()) {
            return CompletableFuture.completedFuture(false);
        }

        String caption = String.format(
                "🔄 PERSON RE-IDENTIFIED\n\n" +
                "Same person detected across cameras!\n" +
                "📷 Camera %d → Camera %d\n" +
                "📊 Similarity: %.1f%%\n" +
                "🕐 Time: %s\n\n" +
                "🔒 DrishtiX ReID System",
                sourceCameraId, matchedCameraId,
                similarity * 100,
                LocalDateTime.now().format(TIMESTAMP_FMT)
        );

        if (snapshotPath != null && new File(snapshotPath).exists()) {
            return sendPhotoMessage(botToken, chatId, snapshotPath, caption);
        } else {
            return sendTextMessage(botToken, chatId, caption);
        }
    }

    /**
     * Sends a test message to verify the Telegram bot configuration.
     *
     * @return a future containing true if the message was sent successfully
     */
    public CompletableFuture<Boolean> sendTestMessage() {
        ConfigurationService config = ConfigurationService.getInstance();
        String botToken = config.getTelegramBotToken();
        String chatId = config.getTelegramChatId();

        if (botToken == null || botToken.isBlank() || chatId == null || chatId.isBlank()) {
            log.warn("Telegram test: bot token or chat ID not configured");
            return CompletableFuture.completedFuture(false);
        }

        String message = "✅ DrishtiX Telegram Alert System\n\n" +
                "Connection test successful!\n" +
                "Time: " + LocalDateTime.now().format(TIMESTAMP_FMT) + "\n\n" +
                "You will receive detection alerts on this chat.";

        return sendTextMessage(botToken, chatId, message);
    }

    // ==================== Private HTTP Methods ====================

    /**
     * Sends a photo message via the Telegram Bot API using multipart/form-data.
     */
    private CompletableFuture<Boolean> sendPhotoMessage(
            String botToken, String chatId, String photoPath, String caption) {

        try {
            String url = TELEGRAM_API_BASE + botToken + "/sendPhoto";

            Path filePath = Path.of(photoPath);
            byte[] photoBytes = Files.readAllBytes(filePath);

            // Determine content type
            String contentType = photoPath.toLowerCase().endsWith(".png")
                    ? "image/png" : "image/jpeg";

            MultipartBodyBuilder builder = new MultipartBodyBuilder()
                    .addTextField("chat_id", chatId)
                    .addTextField("caption", caption)
                    .addTextField("parse_mode", "HTML")
                    .addFileField("photo", filePath.getFileName().toString(),
                            photoBytes, contentType);

            HttpRequest request = HttpRequest.newBuilder()
                    .uri(URI.create(url))
                    .header("Content-Type", builder.getContentType())
                    .timeout(Duration.ofSeconds(15))
                    .POST(builder.build())
                    .build();

            return httpClient.sendAsync(request, HttpResponse.BodyHandlers.ofString())
                    .thenApply(response -> {
                        if (response.statusCode() == 200) {
                            log.info("Telegram photo alert sent successfully to chat: {}", chatId);
                            return true;
                        } else {
                            String body = response.body();
                            log.warn("Telegram API returned HTTP {}: {}", response.statusCode(), body);
                            if (body != null && body.contains("migrate_to_chat_id")) {
                                try {
                                    org.json.JSONObject obj = new org.json.JSONObject(body);
                                    if (obj.has("parameters")) {
                                        long newChatId = obj.getJSONObject("parameters").optLong("migrate_to_chat_id");
                                        if (newChatId != 0) {
                                            String newChatIdStr = String.valueOf(newChatId);
                                            log.info("Telegram group migrated! Updating chat ID to: {}", newChatIdStr);
                                            ConfigurationService.getInstance().updateConfig(
                                                    com.drishtix.util.AppConstants.CFG_TELEGRAM_CHAT_ID, newChatIdStr);
                                        }
                                    }
                                } catch (Exception ex) {
                                    log.warn("Could not parse migrate_to_chat_id", ex);
                                }
                            }
                            return false;
                        }
                    })
                    .exceptionally(ex -> {
                        log.warn("Telegram photo send failed: {}", ex.getMessage());
                        return false;
                    });

        } catch (Exception e) {
            log.error("Failed to build Telegram photo request: {}", e.getMessage());
            return CompletableFuture.completedFuture(false);
        }
    }

    /**
     * Sends a text message via the Telegram Bot API.
     * Used as fallback when no snapshot image is available.
     */
    private CompletableFuture<Boolean> sendTextMessage(
            String botToken, String chatId, String text) {

        try {
            String url = TELEGRAM_API_BASE + botToken + "/sendMessage";

            MultipartBodyBuilder builder = new MultipartBodyBuilder()
                    .addTextField("chat_id", chatId)
                    .addTextField("text", text)
                    .addTextField("parse_mode", "HTML");

            HttpRequest request = HttpRequest.newBuilder()
                    .uri(URI.create(url))
                    .header("Content-Type", builder.getContentType())
                    .timeout(Duration.ofSeconds(10))
                    .POST(builder.build())
                    .build();

            return httpClient.sendAsync(request, HttpResponse.BodyHandlers.ofString())
                    .thenApply(response -> {
                        if (response.statusCode() == 200) {
                            log.info("Telegram text alert sent to chat: {}", chatId);
                            return true;
                        } else {
                            log.warn("Telegram API returned HTTP {}: {}",
                                    response.statusCode(), response.body());
                            return false;
                        }
                    })
                    .exceptionally(ex -> {
                        log.warn("Telegram text send failed: {}", ex.getMessage());
                        return false;
                    });

        } catch (Exception e) {
            log.error("Failed to build Telegram text request: {}", e.getMessage());
            return CompletableFuture.completedFuture(false);
        }
    }

    /**
     * Escapes characters for Telegram's HTML parse_mode.
     * Telegram requires <, > and & to be escaped.
     */
    private String escapeHtml(String text) {
        if (text == null) return "";
        return text.replace("&", "&amp;")
                   .replace("<", "&lt;")
                   .replace(">", "&gt;");
    }
}
