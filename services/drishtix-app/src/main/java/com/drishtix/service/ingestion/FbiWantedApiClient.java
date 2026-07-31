package com.drishtix.service.ingestion;

import com.drishtix.model.TargetCategory;
import com.drishtix.model.WantedProfile;
import com.drishtix.util.AppConstants;
import org.json.JSONArray;
import org.json.JSONObject;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.io.File;
import java.io.InputStream;
import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardCopyOption;
import java.time.Duration;
import java.util.ArrayList;
import java.util.Collections;
import java.util.List;

/**
 * REST API client for the free FBI Wanted API (api.fbi.gov).
 * <p>
 * Polls the paginated JSON endpoint, extracts metadata (name, case number,
 * description, image URLs), and downloads facial images to a local directory.
 * </p>
 * <p>
 * Anti-DDoS: Enforces a strict 2-second delay between paginated API requests
 * to prevent IP blacklisting. Uses a single HttpClient instance with
 * connection pooling and 30-second timeouts.
 * </p>
 */
public class FbiWantedApiClient {

    private static final Logger log = LoggerFactory.getLogger(FbiWantedApiClient.class);

    private static final int MAX_PAGES = 5;        // Limit pages to avoid excessive downloads
    private static final int PAGE_SIZE = 20;       // FBI API default page size

    private final HttpClient httpClient;
    private final String outputDir;

    public FbiWantedApiClient() {
        this.httpClient = HttpClient.newBuilder()
                .connectTimeout(Duration.ofSeconds(30))
                .followRedirects(HttpClient.Redirect.NORMAL)
                .build();
        this.outputDir = AppConstants.INGESTION_FBI_DIR;
        new File(outputDir).mkdirs();
    }

    /**
     * Polls the FBI Wanted API and returns a list of parsed profiles.
     * Downloads facial images to data/ingestion/fbi/.
     *
     * @return list of WantedProfile objects, or empty list on failure
     */
    public List<WantedProfile> fetchWantedProfiles() {
        List<WantedProfile> profiles = new ArrayList<>();

        try {
            for (int page = 1; page <= MAX_PAGES; page++) {
                log.info("[FBI] Fetching page {} of {}...", page, MAX_PAGES);

                String url = AppConstants.FBI_API_BASE_URL + "?page=" + page + "&pageSize=" + PAGE_SIZE;

                HttpRequest request = HttpRequest.newBuilder()
                        .uri(URI.create(url))
                        .header("Accept", "application/json")
                        .header("User-Agent", "DrishtiX/4.0 (Edge AI Facial Recognition System)")
                        .timeout(Duration.ofSeconds(30))
                        .GET()
                        .build();

                HttpResponse<String> response = httpClient.send(request, HttpResponse.BodyHandlers.ofString());

                if (response.statusCode() != 200) {
                    log.warn("[FBI] API returned status {} for page {}", response.statusCode(), page);
                    break;
                }

                JSONObject json = new JSONObject(response.body());
                JSONArray items = json.optJSONArray("items");

                if (items == null || items.isEmpty()) {
                    log.info("[FBI] No more items on page {}, stopping pagination", page);
                    break;
                }

                for (int i = 0; i < items.length(); i++) {
                    try {
                        JSONObject item = items.getJSONObject(i);
                        WantedProfile profile = parseItem(item);
                        if (profile != null) {
                            profiles.add(profile);
                        }
                    } catch (Exception e) {
                        log.debug("[FBI] Skipping malformed item at index {}: {}", i, e.getMessage());
                    }
                }

                log.info("[FBI] Page {} parsed: {} items, {} total profiles", page, items.length(), profiles.size());

                // Anti-DDoS rate limiting — mandatory 2-second delay between requests
                if (page < MAX_PAGES) {
                    Thread.sleep(AppConstants.INGESTION_RATE_LIMIT_MS);
                }
            }

        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
            log.warn("[FBI] Ingestion interrupted");
        } catch (Exception e) {
            log.error("[FBI] Failed to fetch wanted profiles", e);
        }

        log.info("[FBI] Ingestion complete: {} profiles fetched", profiles.size());
        return Collections.unmodifiableList(profiles);
    }

    /**
     * Parses a single FBI Wanted API JSON item into a WantedProfile.
     */
    private WantedProfile parseItem(JSONObject item) {
        String uid = item.optString("uid", null);
        String title = item.optString("title", null);

        if (uid == null || title == null || title.isBlank()) {
            return null;
        }

        // Extract image URL — FBI API uses "images" array with "original" field
        String imageUrl = extractImageUrl(item);
        if (imageUrl == null) {
            log.debug("[FBI] No image URL for UID: {}", uid);
            return null;
        }

        // Extract metadata
        String caseNumber = item.optString("caution", "FBI-" + uid);
        if (caseNumber.length() > 50) {
            caseNumber = "FBI-" + uid; // Use UID as case number if caution text is too long
        }

        String description = item.optString("description", "");
        if (description.length() > 500) {
            description = description.substring(0, 500) + "...";
        }

        // Determine category from FBI subject classification
        String subjects = item.optString("subjects", "").toLowerCase();
        TargetCategory category = subjects.contains("missing")
                ? TargetCategory.MISSING_PERSON
                : TargetCategory.CRIMINAL;

        WantedProfile profile = new WantedProfile(
                WantedProfile.SourceAgency.FBI,
                uid,
                title,
                caseNumber,
                description,
                imageUrl,
                category
        );

        // Download the image
        String localPath = downloadImage(imageUrl, uid);
        if (localPath != null) {
            profile.setLocalImagePath(localPath);
        }

        return profile;
    }

    /**
     * Extracts the best available image URL from an FBI item's "images" array.
     */
    private String extractImageUrl(JSONObject item) {
        JSONArray images = item.optJSONArray("images");
        if (images == null || images.isEmpty()) {
            return null;
        }

        // Prefer the "original" field, fall back to "thumb" or "large"
        for (int i = 0; i < images.length(); i++) {
            JSONObject imgObj = images.getJSONObject(i);
            String original = imgObj.optString("original", null);
            if (original != null && !original.isBlank()) {
                return original;
            }
            String large = imgObj.optString("large", null);
            if (large != null && !large.isBlank()) {
                return large;
            }
            String thumb = imgObj.optString("thumb", null);
            if (thumb != null && !thumb.isBlank()) {
                return thumb;
            }
        }

        return null;
    }

    /**
     * Downloads an image from a URL to the local FBI ingestion directory.
     *
     * @return local file path on success, or null on failure
     */
    private String downloadImage(String imageUrl, String uid) {
        try {
            HttpRequest request = HttpRequest.newBuilder()
                    .uri(URI.create(imageUrl))
                    .header("User-Agent", "DrishtiX/4.0")
                    .timeout(Duration.ofSeconds(30))
                    .GET()
                    .build();

            HttpResponse<InputStream> response = httpClient.send(request, HttpResponse.BodyHandlers.ofInputStream());

            if (response.statusCode() != 200) {
                log.debug("[FBI] Image download failed for {}: status {}", uid, response.statusCode());
                return null;
            }

            // Determine file extension from URL or default to .jpg
            String ext = imageUrl.contains(".png") ? ".png" : ".jpg";
            String filename = "fbi_" + uid.replaceAll("[^a-zA-Z0-9_-]", "_") + ext;
            Path outputPath = Path.of(outputDir, filename);

            Files.copy(response.body(), outputPath, StandardCopyOption.REPLACE_EXISTING);
            log.debug("[FBI] Image downloaded: {}", outputPath);

            return outputPath.toString();

        } catch (Exception e) {
            log.debug("[FBI] Failed to download image for {}: {}", uid, e.getMessage());
            return null;
        }
    }
}
