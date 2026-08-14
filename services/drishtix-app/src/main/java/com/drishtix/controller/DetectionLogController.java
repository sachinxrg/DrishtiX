package com.drishtix.controller;

import com.drishtix.model.DetectionLog;
import com.drishtix.model.TargetCategory;
import com.drishtix.service.DetectionLogService;
import com.drishtix.service.ExportService;
import javafx.application.Platform;
import javafx.collections.FXCollections;
import javafx.collections.ObservableList;
import javafx.fxml.FXML;
import javafx.geometry.Pos;
import javafx.scene.control.*;
import javafx.scene.control.cell.PropertyValueFactory;
import javafx.scene.image.Image;
import javafx.scene.image.ImageView;
import javafx.scene.layout.HBox;
import javafx.scene.layout.VBox;
import javafx.scene.shape.Rectangle;
import javafx.stage.FileChooser;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.io.File;
import java.time.LocalDate;
import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;
import java.util.ArrayList;
import java.util.List;
import java.util.concurrent.CompletableFuture;

/**
 * Controller for the Detection Logs (History) view.
 * <p>
 * Redesigned with:
 * - Full Bento Grid layout (Neumorphism × Glassmorphism)
 * - Quick Stats glassmorphic bar with live counts
 * - Serial number column
 * - Custom CellFactories for formatted timestamps, confidence percentages, and category badges
 * - Click-to-view Glassmorphic detail panel with 2×3 micro-card grid
 * </p>
 */
public class DetectionLogController {

    private static final Logger log = LoggerFactory.getLogger(DetectionLogController.class);

    // ==================== Table ====================
    @FXML private TableView<DetectionLog> logTable;
    @FXML private TableColumn<DetectionLog, Long> colSerial;
    @FXML private TableColumn<DetectionLog, LocalDateTime> colTimestamp;
    @FXML private TableColumn<DetectionLog, String> colTargetName;
    @FXML private TableColumn<DetectionLog, TargetCategory> colCategory;
    @FXML private TableColumn<DetectionLog, String> colCaseNum;
    @FXML private TableColumn<DetectionLog, Double> colConfidence;
    @FXML private TableColumn<DetectionLog, String> colCamera;

    // ==================== Toolbar ====================
    @FXML private DatePicker dateFrom;
    @FXML private DatePicker dateTo;
    @FXML private ComboBox<String> categoryFilter;
    @FXML private Label recordCountLabel;

    // ==================== Quick Stats ====================
    @FXML private Label statTotal;
    @FXML private Label statCriminals;
    @FXML private Label statMissing;

    // ==================== Bento Detail Panel ====================
    @FXML private VBox emptyStatePanel;
    @FXML private VBox detailsPanel;
    @FXML private ImageView snapshotPreview;
    @FXML private Label lblDetailName;
    @FXML private Label lblDetailCategory;
    @FXML private Label lblDetailConfidence;
    @FXML private Label lblDetailTime;
    @FXML private Label lblDetailCamera;
    @FXML private Label lblDetailFir;

    // ==================== Services ====================
    private final DetectionLogService logService = DetectionLogService.getInstance();
    private final ExportService exportService = new ExportService();
    private final ObservableList<DetectionLog> logList = FXCollections.observableArrayList();

    private final DateTimeFormatter timeFormatter = DateTimeFormatter.ofPattern("dd/MM/yyyy HH:mm:ss");

    // ==================== Initialization ====================

    @FXML
    public void initialize() {
        setupTableColumns();
        setupFilters();
        setupSelectionListener();

        if (logTable != null) {
            logTable.setItems(logList);
        }

        handleFilter();
    }

    // ==================== Table Column Setup ====================

    private void setupTableColumns() {

        // --- Serial Number (Stable index) ---
        if (colSerial != null) {
            colSerial.setCellValueFactory(new PropertyValueFactory<>("logId"));
            colSerial.setCellFactory(column -> new TableCell<DetectionLog, Long>() {
                @Override
                protected void updateItem(Long item, boolean empty) {
                    super.updateItem(item, empty);
                    if (empty || getTableRow() == null || getTableRow().getItem() == null) {
                        setText(null);
                        setGraphic(null);
                    } else {
                        setText(String.valueOf(getIndex() + 1));
                        setStyle("-fx-alignment: CENTER; -fx-font-weight: bold; -fx-text-fill: #94A3B8;");
                    }
                }
            });
        }

        // --- Target Name (Bold) ---
        if (colTargetName != null) {
            colTargetName.setCellValueFactory(new PropertyValueFactory<>("targetName"));
            colTargetName.setCellFactory(column -> new TableCell<DetectionLog, String>() {
                @Override
                protected void updateItem(String item, boolean empty) {
                    super.updateItem(item, empty);
                    if (empty || item == null) {
                        setText(null);
                    } else {
                        setText(item);
                        setStyle("-fx-font-weight: bold; -fx-text-fill: #1E293B;");
                    }
                }
            });
        }

        // --- Camera Name (Centered, muted) ---
        if (colCamera != null) {
            colCamera.setCellValueFactory(new PropertyValueFactory<>("cameraName"));
            colCamera.setCellFactory(column -> new TableCell<DetectionLog, String>() {
                @Override
                protected void updateItem(String item, boolean empty) {
                    super.updateItem(item, empty);
                    if (empty || item == null) {
                        setText(null);
                    } else {
                        setText(item);
                        setStyle("-fx-text-fill: #64748B; -fx-alignment: CENTER;");
                    }
                }
            });
        }

        // --- FIR Number (Centered) ---
        if (colCaseNum != null) {
            colCaseNum.setCellValueFactory(new PropertyValueFactory<>("caseNumber"));
            colCaseNum.setCellFactory(column -> new TableCell<DetectionLog, String>() {
                @Override
                protected void updateItem(String item, boolean empty) {
                    super.updateItem(item, empty);
                    if (empty || item == null) {
                        setText(null);
                    } else {
                        setText(item);
                        setStyle("-fx-alignment: CENTER;");
                    }
                }
            });
        }

        // --- Formatted Timestamp (dd/MM/yyyy HH:mm:ss, centered) ---
        if (colTimestamp != null) {
            colTimestamp.setCellValueFactory(new PropertyValueFactory<>("detectionTimestamp"));
            colTimestamp.setCellFactory(column -> new TableCell<DetectionLog, LocalDateTime>() {
                @Override
                protected void updateItem(LocalDateTime date, boolean empty) {
                    super.updateItem(date, empty);
                    if (empty || date == null) {
                        setText(null);
                    } else {
                        setText(timeFormatter.format(date));
                        setStyle("-fx-text-fill: #64748B; -fx-font-size: 12; -fx-alignment: CENTER;");
                    }
                }
            });
        }

        // --- Color-Coded Confidence Percentage ---
        if (colConfidence != null) {
            colConfidence.setCellValueFactory(new PropertyValueFactory<>("matchConfidenceScore"));
            colConfidence.setCellFactory(column -> new TableCell<DetectionLog, Double>() {
                @Override
                protected void updateItem(Double conf, boolean empty) {
                    super.updateItem(conf, empty);
                    if (empty || conf == null) {
                        setText(null);
                        setGraphic(null);
                    } else {
                        double percentage = conf;
                        if (conf <= 1.0) percentage = conf * 100.0;

                        setText(String.format("%.1f%%", percentage));

                        String color;
                        if (percentage >= 90.0) color = "#10B981";
                        else if (percentage >= 80.0) color = "#F59E0B";
                        else color = "#EF4444";

                        setStyle("-fx-font-weight: bold; -fx-alignment: CENTER; -fx-text-fill: " + color + ";");
                    }
                }
            });
        }

        // --- Category Badges (Colored Pills) ---
        if (colCategory != null) {
            colCategory.setCellValueFactory(new PropertyValueFactory<>("targetCategory"));
            colCategory.setCellFactory(column -> new TableCell<DetectionLog, TargetCategory>() {
                @Override
                protected void updateItem(TargetCategory cat, boolean empty) {
                    super.updateItem(cat, empty);
                    setText(null);
                    if (empty || cat == null) {
                        setGraphic(null);
                    } else {
                        Label badge = new Label();
                        if (cat == TargetCategory.CRIMINAL) {
                            badge.setText("🔴 Criminal");
                            badge.getStyleClass().add("category-badge-criminal");
                        } else {
                            badge.setText("🔵 Missing Person");
                            badge.getStyleClass().add("category-badge-missing");
                        }
                        badge.getStyleClass().add("category-badge");
                        HBox container = new HBox(badge);
                        container.setAlignment(Pos.CENTER);
                        setGraphic(container);
                    }
                }
            });
        }
    }

    // ==================== Filter Setup ====================

    private void setupFilters() {
        if (categoryFilter != null) {
            categoryFilter.getItems().addAll("All", "CRIMINAL", "MISSING_PERSON");
            categoryFilter.setValue("All");
        }
        if (dateFrom != null) dateFrom.setValue(LocalDate.now().minusDays(7));
        if (dateTo != null) dateTo.setValue(LocalDate.now());
    }

    // ==================== Selection Listener ====================

    private void setupSelectionListener() {
        if (logTable != null) {
            logTable.getSelectionModel().selectedItemProperty().addListener((obs, old, sel) -> {
                updateBentoDetailsPanel(sel);
            });
        }

        // Initial state: show empty, hide details
        updateBentoDetailsPanel(null);

        // Clip snapshot corners for a rounded neumorphic look
        if (snapshotPreview != null) {
            Rectangle clip = new Rectangle(260, 210);
            clip.setArcWidth(20);
            clip.setArcHeight(20);
            snapshotPreview.setClip(clip);
        }
    }

    // ==================== Bento Detail Panel ====================

    /**
     * Toggles visibility of the Bento Details vs Empty State based on selection.
     * Populates all 6 micro-cards when a detection is selected.
     */
    private void updateBentoDetailsPanel(DetectionLog selected) {
        if (selected == null) {
            if (emptyStatePanel != null) emptyStatePanel.setVisible(true);
            if (detailsPanel != null) detailsPanel.setVisible(false);
            if (snapshotPreview != null) snapshotPreview.setImage(null);
            return;
        }

        // Show Details, Hide Empty State
        if (emptyStatePanel != null) emptyStatePanel.setVisible(false);
        if (detailsPanel != null) detailsPanel.setVisible(true);

        // --- Snapshot Image ---
        if (snapshotPreview != null) {
            String path = selected.getSnapshotPath();
            if (path != null && !path.isBlank()) {
                try {
                    File file = new File(path);
                    if (file.exists()) {
                        snapshotPreview.setImage(new Image(file.toURI().toString(), 260, 210, true, true));
                    } else {
                        snapshotPreview.setImage(null);
                    }
                } catch (Exception e) {
                    log.warn("Failed to load snapshot: {}", path, e);
                    snapshotPreview.setImage(null);
                }
            } else {
                snapshotPreview.setImage(null);
            }
        }

        // --- Micro-Card: Target Name ---
        if (lblDetailName != null) {
            lblDetailName.setText(selected.getTargetName() != null ? selected.getTargetName() : "Unknown");
        }

        // --- Micro-Card: Category Badge ---
        if (lblDetailCategory != null && selected.getTargetCategory() != null) {
            lblDetailCategory.getStyleClass().removeAll("category-badge-criminal", "category-badge-missing", "category-badge");
            if (selected.getTargetCategory() == TargetCategory.CRIMINAL) {
                lblDetailCategory.setText("🔴 Criminal");
                lblDetailCategory.getStyleClass().addAll("category-badge", "category-badge-criminal");
            } else {
                lblDetailCategory.setText("🔵 Missing");
                lblDetailCategory.getStyleClass().addAll("category-badge", "category-badge-missing");
            }
        }

        // --- Micro-Card: Confidence ---
        if (lblDetailConfidence != null) {
            double c = selected.getMatchConfidenceScore();
            if (c <= 1.0) c = c * 100.0;
            lblDetailConfidence.setText(String.format("%.1f%%", c));
            if (c >= 90.0) lblDetailConfidence.setStyle("-fx-text-fill: #10B981; -fx-font-weight: bold; -fx-font-size: 14;");
            else if (c >= 80.0) lblDetailConfidence.setStyle("-fx-text-fill: #F59E0B; -fx-font-weight: bold; -fx-font-size: 14;");
            else lblDetailConfidence.setStyle("-fx-text-fill: #EF4444; -fx-font-weight: bold; -fx-font-size: 14;");
        }

        // --- Micro-Card: Detection Time ---
        if (lblDetailTime != null && selected.getDetectionTimestamp() != null) {
            lblDetailTime.setText(timeFormatter.format(selected.getDetectionTimestamp()));
        }

        // --- Micro-Card: Camera ---
        if (lblDetailCamera != null) {
            lblDetailCamera.setText(selected.getCameraName() != null ? selected.getCameraName() : "N/A");
        }

        // --- Micro-Card: FIR Number ---
        if (lblDetailFir != null) {
            lblDetailFir.setText(selected.getCaseNumber() != null ? selected.getCaseNumber() : "N/A");
        }
    }

    // ==================== Quick Stats ====================

    /**
     * Updates the Quick Stats bar with counts from the current logList.
     */
    private void updateQuickStats() {
        if (statTotal == null || statCriminals == null || statMissing == null) return;

        int total = logList.size();
        long criminals = logList.stream()
                .filter(l -> l.getTargetCategory() == TargetCategory.CRIMINAL)
                .count();
        long missing = logList.stream()
                .filter(l -> l.getTargetCategory() == TargetCategory.MISSING_PERSON)
                .count();

        statTotal.setText(String.valueOf(total));
        statCriminals.setText(String.valueOf(criminals));
        statMissing.setText(String.valueOf(missing));
    }

    // ==================== Action Handlers ====================

    @FXML
    public void handleFilter() {
        LocalDate from = dateFrom != null ? dateFrom.getValue() : LocalDate.now().minusDays(7);
        LocalDate to = dateTo != null ? dateTo.getValue() : LocalDate.now();
        String catVal = categoryFilter != null ? categoryFilter.getValue() : "All";
        TargetCategory catFilter = "All".equals(catVal) ? null : TargetCategory.fromDbValue(catVal);

        List<DetectionLog> results = logService.getDetectionsByDateRange(from, to, catFilter);
        Platform.runLater(() -> {
            logList.setAll(results);
            if (recordCountLabel != null) {
                recordCountLabel.setText(String.format("Showing %d detection logs", results.size()));
            }
            updateQuickStats();
        });
    }

    @FXML
    public void handleExportCSV() {
        FileChooser fc = new FileChooser();
        fc.setTitle("Export Detection Logs");
        fc.getExtensionFilters().add(new FileChooser.ExtensionFilter("CSV", "*.csv"));
        fc.setInitialFileName(exportService.generateExportFilename());

        javafx.stage.Window owner = null;
        if (logTable != null && logTable.getScene() != null) {
            owner = logTable.getScene().getWindow();
        }

        File file = fc.showSaveDialog(owner);

        if (file != null) {
            String filePath = file.getAbsolutePath();
            int recordCount = logList.size();
            List<DetectionLog> exportSnapshot = new ArrayList<>(logList);

            CompletableFuture.runAsync(() -> {
                try {
                    exportService.exportToCSV(exportSnapshot, filePath);
                    Platform.runLater(() -> {
                        Alert alert = new Alert(Alert.AlertType.INFORMATION);
                        alert.setTitle("Export Complete");
                        alert.setContentText("Exported " + recordCount + " records to:\n" + filePath);
                        alert.showAndWait();
                    });
                } catch (Exception e) {
                    log.error("CSV export failed", e);
                    Platform.runLater(() -> {
                        Alert alert = new Alert(Alert.AlertType.ERROR);
                        alert.setTitle("Export Failed");
                        alert.setContentText("CSV export failed: " + e.getMessage());
                        alert.showAndWait();
                    });
                }
            });
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
                "  Timestamp: " + (selected.getDetectionTimestamp() != null ? timeFormatter.format(selected.getDetectionTimestamp()) : "N/A") + "\n" +
                "  Confidence: " + String.format("%.1f%%", selected.getMatchConfidenceScore()) + "\n\n" +
                "The associated snapshot file will also be deleted.\n" +
                "This action cannot be undone.");
        confirm.getButtonTypes().setAll(ButtonType.OK, ButtonType.CANCEL);

        confirm.showAndWait().ifPresent(btn -> {
            if (btn == ButtonType.OK) {
                try {
                    logService.deleteLog(selected.getLogId());
                    handleFilter();
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
