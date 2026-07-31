package com.drishtix.controller;

import com.drishtix.model.DetectionLog;
import com.drishtix.model.TargetCategory;
import com.drishtix.service.DetectionLogService;
import com.drishtix.service.ExportService;
import javafx.application.Platform;
import javafx.collections.FXCollections;
import javafx.collections.ObservableList;
import javafx.fxml.FXML;
import javafx.scene.control.*;
import javafx.scene.control.cell.PropertyValueFactory;
import javafx.scene.image.Image;
import javafx.scene.image.ImageView;
import javafx.stage.FileChooser;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.io.File;
import java.time.LocalDate;
import java.time.LocalDateTime;
import java.util.List;

/**
 * Controller for the Detection Logs view.
 * Provides filterable log table with snapshot preview and CSV export.
 */
public class DetectionLogController {

    private static final Logger log = LoggerFactory.getLogger(DetectionLogController.class);

    @FXML private TableView<DetectionLog> logTable;
    @FXML private TableColumn<DetectionLog, LocalDateTime> colTimestamp;
    @FXML private TableColumn<DetectionLog, String> colTargetName;
    @FXML private TableColumn<DetectionLog, TargetCategory> colCategory;
    @FXML private TableColumn<DetectionLog, String> colCaseNum;
    @FXML private TableColumn<DetectionLog, Double> colConfidence;
    @FXML private TableColumn<DetectionLog, String> colCamera;
    @FXML private DatePicker dateFrom;
    @FXML private DatePicker dateTo;
    @FXML private ComboBox<String> categoryFilter;
    @FXML private ImageView snapshotPreview;

    private final DetectionLogService logService = DetectionLogService.getInstance();
    private final ExportService exportService = new ExportService();
    private final ObservableList<DetectionLog> logList = FXCollections.observableArrayList();

    @FXML
    public void initialize() {
        if (colTimestamp != null) colTimestamp.setCellValueFactory(new PropertyValueFactory<>("detectionTimestamp"));
        if (colTargetName != null) colTargetName.setCellValueFactory(new PropertyValueFactory<>("targetName"));
        if (colCategory != null) colCategory.setCellValueFactory(new PropertyValueFactory<>("targetCategory"));
        if (colCaseNum != null) colCaseNum.setCellValueFactory(new PropertyValueFactory<>("caseNumber"));
        if (colConfidence != null) colConfidence.setCellValueFactory(new PropertyValueFactory<>("matchConfidenceScore"));
        if (colCamera != null) colCamera.setCellValueFactory(new PropertyValueFactory<>("cameraName"));

        if (categoryFilter != null) {
            categoryFilter.getItems().addAll("All", "CRIMINAL", "MISSING_PERSON");
            categoryFilter.setValue("All");
        }

        if (dateFrom != null) dateFrom.setValue(LocalDate.now().minusDays(7));
        if (dateTo != null) dateTo.setValue(LocalDate.now());

        if (logTable != null) {
            logTable.setItems(logList);
            logTable.getSelectionModel().selectedItemProperty().addListener((obs, old, sel) -> {
                if (sel != null && sel.getSnapshotPath() != null && snapshotPreview != null) {
                    try {
                        File snapFile = new File(sel.getSnapshotPath());
                        if (snapFile.exists()) {
                            snapshotPreview.setImage(new Image(snapFile.toURI().toString(), 300, 300, true, true));
                        }
                    } catch (Exception e) {
                        log.warn("Could not load snapshot", e);
                    }
                }
            });
        }

        handleFilter();
    }

    @FXML
    public void handleFilter() {
        LocalDate from = dateFrom != null ? dateFrom.getValue() : LocalDate.now().minusDays(7);
        LocalDate to = dateTo != null ? dateTo.getValue() : LocalDate.now();
        String catVal = categoryFilter != null ? categoryFilter.getValue() : "All";
        TargetCategory catFilter = "All".equals(catVal) ? null : TargetCategory.fromDbValue(catVal);

        List<DetectionLog> results = logService.getDetectionsByDateRange(from, to, catFilter);
        Platform.runLater(() -> logList.setAll(results));
    }

    @FXML
    public void handleExportCSV() {
        FileChooser fc = new FileChooser();
        fc.setTitle("Export Detection Logs");
        fc.getExtensionFilters().add(new FileChooser.ExtensionFilter("CSV", "*.csv"));
        fc.setInitialFileName(exportService.generateExportFilename());
        File file = fc.showSaveDialog(logTable.getScene().getWindow());

        if (file != null) {
            try {
                exportService.exportToCSV(logList, file.getAbsolutePath());
                Alert alert = new Alert(Alert.AlertType.INFORMATION);
                alert.setTitle("Export Complete");
                alert.setContentText("Exported " + logList.size() + " records to:\n" + file.getAbsolutePath());
                alert.showAndWait();
            } catch (Exception e) {
                log.error("CSV export failed", e);
            }
        }
    }

    @FXML
    public void handleDeleteLog() {
        DetectionLog selected = logTable.getSelectionModel().getSelectedItem();
        if (selected == null) {
            Platform.runLater(() -> {
                Alert info = new Alert(Alert.AlertType.INFORMATION);
                info.setTitle("DrishtiX");
                info.setContentText("Please select a log entry to delete.");
                info.showAndWait();
            });
            return;
        }

        Alert confirm = new Alert(Alert.AlertType.CONFIRMATION);
        confirm.setTitle("Delete Detection Log");
        confirm.setHeaderText("🗑️ Delete Log Entry");
        confirm.setContentText(
                "Delete this detection log entry?\n\n" +
                "  Target: " + (selected.getTargetName() != null ? selected.getTargetName() : "ID " + selected.getTargetId()) + "\n" +
                "  Timestamp: " + selected.getDetectionTimestamp() + "\n" +
                "  Confidence: " + String.format("%.2f", selected.getMatchConfidenceScore()) + "\n\n" +
                "The associated snapshot file will also be deleted.\n" +
                "This action cannot be undone.");
        confirm.getButtonTypes().setAll(ButtonType.OK, ButtonType.CANCEL);

        confirm.showAndWait().ifPresent(btn -> {
            if (btn == ButtonType.OK) {
                try {
                    logService.deleteLog(selected.getLogId());
                    handleFilter(); // Refresh the table
                    Platform.runLater(() -> {
                        Alert success = new Alert(Alert.AlertType.INFORMATION);
                        success.setTitle("DrishtiX");
                        success.setContentText("Detection log entry deleted successfully.");
                        success.showAndWait();
                    });
                } catch (Exception e) {
                    log.error("Failed to delete detection log: {}", selected.getLogId(), e);
                    Platform.runLater(() -> {
                        Alert error = new Alert(Alert.AlertType.ERROR);
                        error.setTitle("Delete Failed");
                        error.setContentText("Failed to delete log entry: " + e.getMessage());
                        error.showAndWait();
                    });
                }
            }
        });
    }
}
