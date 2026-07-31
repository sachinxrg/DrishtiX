package com.drishtix.service;

import com.drishtix.util.MultipartBodyBuilder;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.time.Duration;
import java.util.concurrent.CompletableFuture;

/**
 * Service for communicating with the Python ReID microservice.
 * <p>
 * Sends person crop images to the FastAPI service and retrieves
 * 512-dimensional feature embeddings for cross-camera re-identification.
 * </p>
 * <p>
 * Uses Java 11's {@link HttpClient} for async HTTP communication.
 * Gracefully degrades if the Python service is unavailable — logs a
 * warning and returns null without crashing the application.
 * </p>
 */
public class ReIDService {

    private static final Logger log = LoggerFactory.getLogger(ReIDService.class);
    private static volatile ReIDService instance;

    private final HttpClient httpClient;

    private ReIDService() {
        this.httpClient = HttpClient.newBuilder()
                .version(HttpClient.Version.HTTP_1_1)
                .connectTimeout(Duration.ofSeconds(10))
                .build();
    }

    public static ReIDService getInstance() {
        if (instance == null) {
            synchronized (ReIDService.class) {
                if (instance == null) {
                    instance = new ReIDService();
                }
            }
        }
        return instance;
    }

    /**
     * Extracts a feature embedding from a person crop image.
     * <p>
     * Sends the image bytes to the Python ReID service asynchronously
     * and returns the 512-dimensional embedding vector.
     * </p>
     *
     * @param imageBytes JPEG or PNG encoded image of a person
     * @param fileName   file name hint for the upload (e.g., "person_crop.jpg")
     * @return a future containing the embedding array, or null on failure
     */
    public CompletableFuture<double[]> extractEmbedding(byte[] imageBytes, String fileName) {
        if (!ConfigurationService.getInstance().isReIDEnabled()) {
            return CompletableFuture.completedFuture(null);
        }

        if (imageBytes == null || imageBytes.length == 0) {
            log.warn("ReID: Empty image bytes provided, skipping extraction");
            return CompletableFuture.completedFuture(null);
        }

        String baseUrl = ConfigurationService.getInstance().getReIDServiceUrl();
        String extractUrl = baseUrl + "/extract";

        try {
            MultipartBodyBuilder builder = new MultipartBodyBuilder()
                    .addFileField("file", fileName, imageBytes, "image/jpeg");

            HttpRequest request = HttpRequest.newBuilder()
                    .uri(URI.create(extractUrl))
                    .header("Content-Type", builder.getContentType())
                    .timeout(Duration.ofSeconds(15))
                    .POST(builder.build())
                    .build();

            return httpClient.sendAsync(request, HttpResponse.BodyHandlers.ofString())
                    .thenApply(response -> {
                        if (response.statusCode() == 200) {
                            return parseEmbeddingResponse(response.body());
                        } else {
                            log.warn("ReID service returned HTTP {}: {}",
                                    response.statusCode(), response.body());
                            return null;
                        }
                    })
                    .exceptionally(ex -> {
                        log.warn("ReID service unavailable: {} — continuing without ReID",
                                ex.getMessage());
                        return null;
                    });

        } catch (Exception e) {
            log.warn("Failed to build ReID request: {}", e.getMessage());
            return CompletableFuture.completedFuture(null);
        }
    }

    /**
     * Checks if the Python ReID service is healthy and reachable.
     *
     * @return a future containing true if healthy, false otherwise
     */
    public CompletableFuture<Boolean> checkHealth() {
        String baseUrl = ConfigurationService.getInstance().getReIDServiceUrl();
        String healthUrl = baseUrl + "/health";

        try {
            HttpRequest request = HttpRequest.newBuilder()
                    .uri(URI.create(healthUrl))
                    .timeout(Duration.ofSeconds(5))
                    .GET()
                    .build();

            return httpClient.sendAsync(request, HttpResponse.BodyHandlers.ofString())
                    .thenApply(response -> {
                        boolean healthy = response.statusCode() == 200;
                        if (healthy) {
                            log.info("ReID service healthy: {}", response.body());
                        } else {
                            log.warn("ReID service unhealthy: HTTP {}", response.statusCode());
                        }
                        return healthy;
                    })
                    .exceptionally(ex -> {
                        log.warn("ReID service unreachable: {}", ex.getMessage());
                        return false;
                    });

        } catch (Exception e) {
            log.warn("Failed to check ReID health: {}", e.getMessage());
            return CompletableFuture.completedFuture(false);
        }
    }

    /**
     * Parses the JSON response from the ReID service to extract the embedding array.
     * Uses simple string parsing to avoid adding a JSON library dependency.
     * <p>
     * Expected format: {@code {"embedding": [0.123, -0.456, ...], "dimensions": 512}}
     * </p>
     */
    private double[] parseEmbeddingResponse(String json) {
        try {
            // Extract the embedding array from the JSON response
            int embeddingStart = json.indexOf("\"embedding\"");
            if (embeddingStart == -1) {
                log.warn("ReID response missing 'embedding' field: {}", json);
                return null;
            }

            int arrayStart = json.indexOf('[', embeddingStart);
            int arrayEnd = json.indexOf(']', arrayStart);
            if (arrayStart == -1 || arrayEnd == -1) {
                log.warn("ReID response has malformed embedding array");
                return null;
            }

            String arrayContent = json.substring(arrayStart + 1, arrayEnd).trim();
            if (arrayContent.isEmpty()) {
                log.warn("ReID response has empty embedding array");
                return null;
            }

            String[] values = arrayContent.split(",");
            double[] embedding = new double[values.length];
            for (int i = 0; i < values.length; i++) {
                embedding[i] = Double.parseDouble(values[i].trim());
            }

            log.debug("ReID embedding parsed: {} dimensions", embedding.length);
            return embedding;

        } catch (Exception e) {
            log.error("Failed to parse ReID embedding response", e);
            return null;
        }
    }
}
