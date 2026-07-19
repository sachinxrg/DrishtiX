package com.drishtix.service;

import com.drishtix.model.DetectionLog;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.io.BufferedWriter;
import java.io.FileWriter;
import java.io.IOException;
import java.time.LocalDate;
import java.time.format.DateTimeFormatter;
import java.util.List;

/**
 * Service for exporting detection logs to CSV format.
 */
public class ExportService {

    private static final Logger log = LoggerFactory.getLogger(ExportService.class);

    /**
     * Exports a list of detection logs to a CSV file.
     *
     * @param detections the detection logs to export
     * @param outputPath the file path for the CSV output
     * @throws IOException if writing fails
     */
    public void exportToCSV(List<DetectionLog> detections, String outputPath) throws IOException {
        try (BufferedWriter writer = new BufferedWriter(new FileWriter(outputPath))) {
            // CSV Header
            writer.write("Log ID,Target Name,Category,Case Number,Detection Time," +
                    "Confidence Score,Confidence %,Camera,Location,Snapshot Path");
            writer.newLine();

            DateTimeFormatter dtf = DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm:ss");

            for (DetectionLog dl : detections) {
                writer.write(String.format("%d,\"%s\",%s,\"%s\",%s,%.2f,%s,\"%s\",\"%s\",\"%s\"",
                        dl.getLogId(),
                        escapeCsv(dl.getTargetName()),
                        dl.getTargetCategory() != null ? dl.getTargetCategory().getDbValue() : "",
                        escapeCsv(dl.getCaseNumber()),
                        dl.getDetectionTimestamp().format(dtf),
                        dl.getMatchConfidenceScore(),
                        dl.getConfidenceDisplay(),
                        escapeCsv(dl.getCameraName()),
                        escapeCsv(dl.getLocationTag()),
                        escapeCsv(dl.getSnapshotPath())));
                writer.newLine();
            }

            log.info("Exported {} detection logs to: {}", detections.size(), outputPath);
        }
    }

    /**
     * Generates a default export filename with the current date.
     */
    public String generateExportFilename() {
        String date = LocalDate.now().format(DateTimeFormatter.ofPattern("yyyy-MM-dd"));
        return "DrishtiX_DetectionLogs_" + date + ".csv";
    }

    private String escapeCsv(String value) {
        if (value == null) return "";
        return value.replace("\"", "\"\"");
    }
}
