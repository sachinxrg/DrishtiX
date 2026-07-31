package com.drishtix.service.ingestion;

import com.drishtix.model.TargetCategory;
import com.drishtix.model.WantedProfile;
import com.drishtix.util.AppConstants;
import org.jsoup.Jsoup;
import org.jsoup.nodes.Document;
import org.jsoup.nodes.Element;
import org.jsoup.select.Elements;
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
 * Headless web scraper for the Indian TrackChild.gov.in missing children portal.
 * <p>
 * Parses the public photograph gallery of missing children, extracting names,
 * case references, and facial images. All extracted profiles are categorized
 * as MISSING_PERSON.
 * </p>
 * <p>
 * Anti-DDoS: Enforces a strict 2-second delay between page requests.
 * Uses a standard browser User-Agent to avoid being blocked.
 * </p>
 */
public class TrackChildScraper {

    private static final Logger log = LoggerFactory.getLogger(TrackChildScraper.class);

    private static final int MAX_PAGES = 3;
    private static final int JSOUP_TIMEOUT_MS = 30_000;

    private final HttpClient httpClient;
    private final String outputDir;

    public TrackChildScraper() {
        this.httpClient = HttpClient.newBuilder()
                .connectTimeout(Duration.ofSeconds(30))
                .followRedirects(HttpClient.Redirect.NORMAL)
                .build();
        this.outputDir = AppConstants.INGESTION_TRACKCHILD_DIR;
        new File(outputDir).mkdirs();
    }

    /**
     * Scrapes the TrackChild missing children portal and returns parsed profiles.
     *
     * @return list of WantedProfile objects (all MISSING_PERSON), or empty list on failure
     */
    public List<WantedProfile> scrapeMissingChildren() {
        List<WantedProfile> profiles = new ArrayList<>();

        try {
            for (int page = 1; page <= MAX_PAGES; page++) {
                log.info("[TrackChild] Scraping page {}...", page);

                String url = AppConstants.TRACKCHILD_URL;
                if (page > 1) {
                    url += "?page=" + page;
                }

                Document doc = Jsoup.connect(url)
                        .userAgent("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 " +
                                "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
                        .timeout(JSOUP_TIMEOUT_MS)
                        .referrer("https://www.google.com")
                        .header("Accept-Language", "en-US,en;q=0.9")
                        .get();

                // TrackChild uses a photo gallery layout — try multiple selectors
                Elements childCards = doc.select(
                        ".child-photo, .gallery-item, .missing-child, " +
                        "table.table tbody tr, div.col-md-3, div.col-sm-4, div.card"
                );

                if (childCards.isEmpty()) {
                    // Broader fallback: any element with an image and adjacent text
                    childCards = doc.select("div[class*=child], div[class*=missing], li[class*=item]");
                }

                if (childCards.isEmpty()) {
                    log.info("[TrackChild] No child entries found on page {} — layout may have changed", page);
                    break;
                }

                int parsedOnPage = 0;
                for (Element card : childCards) {
                    try {
                        WantedProfile profile = parseChildCard(card);
                        if (profile != null) {
                            profiles.add(profile);
                            parsedOnPage++;
                        }
                    } catch (Exception e) {
                        log.debug("[TrackChild] Skipping malformed entry: {}", e.getMessage());
                    }
                }

                log.info("[TrackChild] Page {} scraped: {} profiles parsed", page, parsedOnPage);

                // Anti-DDoS rate limiting
                if (page < MAX_PAGES) {
                    Thread.sleep(AppConstants.INGESTION_RATE_LIMIT_MS);
                }
            }

        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
            log.warn("[TrackChild] Scraping interrupted");
        } catch (Exception e) {
            log.error("[TrackChild] Failed to scrape missing children profiles", e);
        }

        log.info("[TrackChild] Scraping complete: {} profiles fetched", profiles.size());
        return Collections.unmodifiableList(profiles);
    }

    /**
     * Parses a single child card from the TrackChild HTML into a WantedProfile.
     */
    private WantedProfile parseChildCard(Element card) {
        // Extract child name from various possible elements
        String name = extractText(card,
                "h4, h5, .child-name, .name, .card-title, td:nth-child(2), strong, b, span.name");
        if (name == null || name.isBlank() || name.length() < 2) {
            return null;
        }

        // Clean up name — remove "Name:" prefix if present
        name = name.replaceFirst("(?i)^(name|child name)\\s*[:;-]\\s*", "").trim();
        if (name.isBlank()) return null;

        // Extract case reference / FIR number
        String caseRef = extractText(card,
                ".case-number, .fir, .case-ref, td:nth-child(3), span[class*=case], span[class*=fir]");
        if (caseRef == null || caseRef.isBlank()) {
            caseRef = "TC-" + Math.abs(name.hashCode());
        }
        caseRef = caseRef.replaceFirst("(?i)^(case|fir|ref)\\s*[:;-]\\s*", "").trim();

        // Extract description (age, location, etc.)
        String description = extractText(card,
                ".description, .details, .child-details, td:nth-child(4), p, .card-text");
        if (description == null) {
            description = "Missing child reported via TrackChild.gov.in";
        }
        if (description.length() > 500) {
            description = description.substring(0, 500) + "...";
        }

        // Extract image URL
        String imageUrl = extractImageUrl(card);
        if (imageUrl == null) {
            log.debug("[TrackChild] No image found for: {}", name);
            return null;
        }

        // Generate external ID
        String externalId = "TC_" + Math.abs((name + caseRef).hashCode());

        WantedProfile profile = new WantedProfile(
                WantedProfile.SourceAgency.TRACKCHILD,
                externalId,
                name,
                caseRef,
                description,
                imageUrl,
                TargetCategory.MISSING_PERSON  // Always MISSING_PERSON for TrackChild
        );

        // Download image
        String localPath = downloadImage(imageUrl, externalId);
        if (localPath != null) {
            profile.setLocalImagePath(localPath);
        }

        return profile;
    }

    /**
     * Extracts text content from the first matching CSS selector.
     */
    private String extractText(Element parent, String selectors) {
        for (String selector : selectors.split(",")) {
            Elements found = parent.select(selector.trim());
            if (!found.isEmpty()) {
                String text = found.first().text().trim();
                if (!text.isBlank()) {
                    return text;
                }
            }
        }
        return null;
    }

    /**
     * Extracts the image URL from a child card element.
     */
    private String extractImageUrl(Element card) {
        Elements imgs = card.select("img");
        for (Element img : imgs) {
            String src = img.attr("abs:src");
            if (src != null && !src.isBlank() && !src.contains("placeholder")
                    && !src.contains("icon") && !src.contains("logo")) {
                return src;
            }
            String dataSrc = img.attr("abs:data-src");
            if (dataSrc != null && !dataSrc.isBlank()) {
                return dataSrc;
            }
        }

        // Try background-image CSS
        Elements styledElements = card.select("[style*=background-image]");
        for (Element el : styledElements) {
            String style = el.attr("style");
            int urlStart = style.indexOf("url(");
            if (urlStart >= 0) {
                int urlEnd = style.indexOf(")", urlStart + 4);
                if (urlEnd > urlStart) {
                    String bgUrl = style.substring(urlStart + 4, urlEnd)
                            .replace("'", "").replace("\"", "").trim();
                    if (!bgUrl.isBlank()) {
                        return bgUrl;
                    }
                }
            }
        }

        return null;
    }

    /**
     * Downloads an image to the local TrackChild ingestion directory.
     */
    private String downloadImage(String imageUrl, String externalId) {
        try {
            HttpRequest request = HttpRequest.newBuilder()
                    .uri(URI.create(imageUrl))
                    .header("User-Agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64)")
                    .timeout(Duration.ofSeconds(30))
                    .GET()
                    .build();

            HttpResponse<InputStream> response = httpClient.send(request, HttpResponse.BodyHandlers.ofInputStream());

            if (response.statusCode() != 200) {
                return null;
            }

            String ext = imageUrl.contains(".png") ? ".png" : ".jpg";
            String filename = "tc_" + externalId.replaceAll("[^a-zA-Z0-9_-]", "_") + ext;
            Path outputPath = Path.of(outputDir, filename);

            Files.copy(response.body(), outputPath, StandardCopyOption.REPLACE_EXISTING);
            log.debug("[TrackChild] Image downloaded: {}", outputPath);
            return outputPath.toString();

        } catch (Exception e) {
            log.debug("[TrackChild] Failed to download image for {}: {}", externalId, e.getMessage());
            return null;
        }
    }
}
