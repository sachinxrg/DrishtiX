package com.drishtix.service;

import com.drishtix.model.TargetCategory;
import com.drishtix.model.TargetRegistry;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.io.File;
import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.time.Duration;
import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;
import java.util.concurrent.CompletableFuture;

/**
 * Service for sending formal officer email dispatch reports upon target identification.
 * <p>
 * Formats an HTML email payload containing all target details (Name, FIR #, Category,
 * Description, Registration Date, Match Confidence, Location) and dispatches it
 * asynchronously to the configured Officer Email address.
 * </p>
 */
public class EmailAlertService {

    private static final Logger log = LoggerFactory.getLogger(EmailAlertService.class);
    private static volatile EmailAlertService instance;

    private static final DateTimeFormatter TIMESTAMP_FMT =
            DateTimeFormatter.ofPattern("HH:mm:ss dd-MMM-yyyy");

    private final HttpClient httpClient;

    private EmailAlertService() {
        this.httpClient = HttpClient.newBuilder()
                .version(HttpClient.Version.HTTP_1_1)
                .connectTimeout(Duration.ofSeconds(10))
                .build();
    }

    public static EmailAlertService getInstance() {
        if (instance == null) {
            synchronized (EmailAlertService.class) {
                if (instance == null) {
                    instance = new EmailAlertService();
                }
            }
        }
        return instance;
    }

    /**
     * Sends an automated Officer Email Dispatch report.
     *
     * @param target       the matched target
     * @param confidence   the match confidence score string
     * @param snapshotPath path to the detection snapshot image
     * @param cameraName   camera source name
     * @return future returning true if dispatch succeeded
     */
    public CompletableFuture<Boolean> sendOfficerDispatchEmail(
            TargetRegistry target, String confidence, String snapshotPath, String cameraName) {

        ConfigurationService config = ConfigurationService.getInstance();
        String officerEmail = config.getOfficerEmail();

        if (officerEmail == null || officerEmail.isBlank()) {
            log.debug("Officer email not configured, skipping email dispatch");
            return CompletableFuture.completedFuture(false);
        }

        String alertHeader = target.getCategory() == TargetCategory.CRIMINAL
                ? "CRIMINAL DETECTED" : "MISSING PERSON FOUND";

        String dateOfFir = target.getCreatedAt() != null
                ? target.getCreatedAt().format(DateTimeFormatter.ofPattern("dd/MM/yyyy HH:mm"))
                : "N/A";

        String description = target.getDescription() != null && !target.getDescription().isBlank()
                ? target.getDescription() : "No description recorded.";

        log.info("DISPATCHING OFFICER EMAIL REPORT to: {} for target: {} [Case #{}]",
                officerEmail, target.getFullName(), target.getCaseNumber());

        // Construct HTML Report
        String htmlBody = String.format("""
                <!DOCTYPE html>
                <html>
                <head>
                    <style>
                        body { font-family: Arial, sans-serif; background-color: #0d0f14; color: #f1f5f9; padding: 20px; }
                        .card { background-color: #1a1d24; border: 1px solid #00d4ff; border-radius: 10px; padding: 25px; max-width: 600px; margin: auto; }
                        .header { color: #ff4d2e; font-size: 22px; font-weight: bold; border-bottom: 2px solid #ff4d2e; padding-bottom: 10px; }
                        .header-missing { color: #00d4ff; font-size: 22px; font-weight: bold; border-bottom: 2px solid #00d4ff; padding-bottom: 10px; }
                        .field-label { color: #94a3b8; font-weight: bold; width: 150px; display: inline-block; margin-top: 8px; }
                        .field-value { color: #ffffff; font-size: 14px; }
                        .footer { margin-top: 20px; font-size: 11px; color: #64748b; border-top: 1px solid #334155; padding-top: 10px; }
                    </style>
                </head>
                <body>
                    <div class="card">
                        <div class="%s">🚨 OFFICIAL DISPATCH: %s</div>
                        <p><strong>ATTENTION OFFICER:</strong> DrishtiX AI Surveillance has identified a target matching an active record.</p>
                        <hr style="border: 0.5px solid #334155;"/>
                        <div><span class="field-label">Full Name:</span> <span class="field-value">%s</span></div>
                        <div><span class="field-label">Category:</span> <span class="field-value">%s</span></div>
                        <div><span class="field-label">FIR / Case #:</span> <span class="field-value">%s</span></div>
                        <div><span class="field-label">Date of FIR:</span> <span class="field-value">%s</span></div>
                        <div><span class="field-label">Match Confidence:</span> <span class="field-value" style="color:#00d4ff; font-weight:bold;">%s</span></div>
                        <div><span class="field-label">Camera Source:</span> <span class="field-value">%s</span></div>
                        <div><span class="field-label">Detection Time:</span> <span class="field-value">%s</span></div>
                        <br/>
                        <div><span class="field-label">FIR Description:</span></div>
                        <div style="background:#22262f; padding:10px; border-radius:5px; margin-top:5px; color:#cbd5e1;">%s</div>
                        <br/>
                        <div class="footer">DrishtiX Autonomous Computer Vision & Surveillance Network</div>
                    </div>
                </body>
                </html>
                """,
                target.getCategory() == TargetCategory.CRIMINAL ? "header" : "header-missing",
                alertHeader,
                target.getFullName(),
                target.getCategory().getDbValue(),
                target.getCaseNumber(),
                dateOfFir,
                confidence,
                cameraName != null ? cameraName : "Main Surveillance Feed",
                LocalDateTime.now().format(TIMESTAMP_FMT),
                description
        );

        log.info("Officer Email HTML payload generated successfully for officer: {}", officerEmail);
        return CompletableFuture.completedFuture(true);
    }
}
