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
 * Headless web scraper for the public Indian CBI Wanted List.
 * <p>
 * Uses JSoup to parse the HTML page structure, extract target names,
 * case numbers, and image URLs. Downloads facial images to a local directory.
 * </p>
 * <p>
 * Anti-DDoS: Enforces a strict 2-second delay between page requests.
 * Uses a standard browser User-Agent to avoid being blocked.
 * </p>
 */
public class CbiWantedScraper {

    private static final Logger log = LoggerFactory.getLogger(CbiWantedScraper.class);

    private static final int MAX_PAGES = 3;
    private static final int JSOUP_TIMEOUT_MS = 30_000;

    private final HttpClient httpClient;
    private final String outputDir;

    public CbiWantedScraper() {
        this.httpClient = HttpClient.newBuilder()
                .connectTimeout(Duration.ofSeconds(30))
                .followRedirects(HttpClient.Redirect.NORMAL)
                .build();
        this.outputDir = AppConstants.INGESTION_CBI_DIR;
        new File(outputDir).mkdirs();
    }

    /**
     * Scrapes the CBI wanted persons page and returns parsed profiles.
     *
     * @return list of WantedProfile objects, or empty list on failure
     */
    public List<WantedProfile> scrapeWantedProfiles() {
        List<WantedProfile> profiles = new ArrayList<>();

        try {
            for (int page = 1; page <= MAX_PAGES; page++) {
                log.info("[CBI] Scraping page {}...", page);

                String url = AppConstants.CBI_WANTED_URL;
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

                // CBI uses various layouts — try multiple CSS selectors
                Elements personCards = doc.select(".wanted-person, .person-card, .views-row, table.views-table tbody tr");

                if (personCards.isEmpty()) {
                    // Fallback: try to find any structured list with images
                    personCards = doc.select("div.view-content .views-row, div.item-list li");
                }

                if (personCards.isEmpty()) {
                    log.info("[CBI] No person entries found on page {} — layout may have changed", page);
                    break;
                }

                int parsedOnPage = 0;
                for (Element card : personCards) {
                    try {
                        WantedProfile profile = parsePersonCard(card);
                        if (profile != null) {
                            profiles.add(profile);
                            parsedOnPage++;
                        }
                    } catch (Exception e) {
                        log.debug("[CBI] Skipping malformed entry: {}", e.getMessage());
                    }
                }

                log.info("[CBI] Page {} scraped: {} profiles parsed", page, parsedOnPage);

                // Anti-DDoS rate limiting
                if (page < MAX_PAGES) {
                    Thread.sleep(AppConstants.INGESTION_RATE_LIMIT_MS);
                }
            }

        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
            log.warn("[CBI] Scraping interrupted");
        } catch (Exception e) {
            log.error("[CBI] Failed to scrape wanted profiles", e);
        }

        log.info("[CBI] Scraping complete: {} profiles fetched", profiles.size());
        return Collections.unmodifiableList(profiles);
    }

    /**
     * Parses a single person card/row from the CBI HTML into a WantedProfile.
     */
    private WantedProfile parsePersonCard(Element card) {
        // Try to extract the name from headings, title fields, or td elements
        String name = extractText(card, "h3, h4, .field-name-title, .views-field-title, td:nth-child(2)");
        if (name == null || name.isBlank() || name.length() < 2) {
            return null;
        }

        // Extract case number
        String caseNumber = extractText(card, ".field-name-field-case-no, .views-field-field-case-no, td:nth-child(3)");
        if (caseNumber == null || caseNumber.isBlank()) {
            caseNumber = "CBI-" + name.hashCode();
        }

        // Extract description
        String description = extractText(card, ".field-name-body, .views-field-body, td:nth-child(4)");
        if (description == null) {
            description = "CBI Wanted Person";
        }
        if (description.length() > 500) {
            description = description.substring(0, 500) + "...";
        }

        // Extract image URL
        String imageUrl = extractImageUrl(card);
        if (imageUrl == null) {
            log.debug("[CBI] No image found for: {}", name);
            return null;
        }

        // Generate external ID
        String externalId = "CBI_" + Math.abs((name + caseNumber).hashCode());

        WantedProfile profile = new WantedProfile(
                WantedProfile.SourceAgency.CBI,
                externalId,
                name.trim(),
                caseNumber.trim(),
                description.trim(),
                imageUrl,
                TargetCategory.CRIMINAL
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
     * Extracts the image URL from a person card element.
     */
    private String extractImageUrl(Element card) {
        // Try img tags within the card
        Elements imgs = card.select("img");
        for (Element img : imgs) {
            String src = img.attr("abs:src");
            if (src != null && !src.isBlank() && !src.contains("placeholder") && !src.contains("icon")) {
                return src;
            }
            // Check data-src for lazy-loaded images
            String dataSrc = img.attr("abs:data-src");
            if (dataSrc != null && !dataSrc.isBlank()) {
                return dataSrc;
            }
        }

        // Try background-image in style attributes
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
     * Downloads an image to the local CBI ingestion directory.
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
            String filename = "cbi_" + externalId.replaceAll("[^a-zA-Z0-9_-]", "_") + ext;
            Path outputPath = Path.of(outputDir, filename);

            Files.copy(response.body(), outputPath, StandardCopyOption.REPLACE_EXISTING);
            log.debug("[CBI] Image downloaded: {}", outputPath);
            return outputPath.toString();

        } catch (Exception e) {
            log.debug("[CBI] Failed to download image for {}: {}", externalId, e.getMessage());
            return null;
        }
    }
}
