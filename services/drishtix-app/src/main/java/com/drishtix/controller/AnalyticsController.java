package com.drishtix.controller;

import com.drishtix.model.TargetCategory;
import com.drishtix.model.TargetDetectionSummary;
import com.drishtix.service.DetectionAnalyticsService;
import javafx.application.Platform;
import javafx.collections.FXCollections;
import javafx.collections.ObservableList;
import javafx.fxml.FXML;
import javafx.geometry.Pos;
import javafx.scene.chart.*;
import javafx.scene.control.*;
import javafx.scene.control.cell.PropertyValueFactory;
import javafx.scene.layout.HBox;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.time.LocalDate;
import java.time.format.DateTimeFormatter;

/**
 * Controller for the Analytics Dashboard view.
 * Visualizes historical detection trends, category distributions, hourly heatmaps,
 * and top detected targets using JavaFX charts and Bento cards.
 */
public class AnalyticsController {

    private static final Logger log = LoggerFactory.getLogger(AnalyticsController.class);
    private static final DateTimeFormatter DATE_FMT = DateTimeFormatter.ofPattern("dd MMM yyyy");

    // ==================== Header & Filters ====================
    @FXML private Label lblDateRangeSubtitle;
    @FXML private Label lblStatus;
    @FXML private DatePicker dateFrom;
    @FXML private DatePicker dateTo;

    // ==================== KPI Stat Card Labels ====================
    @FXML private Label lblTotalDetections;
    @FXML private Label lblUniqueTargets;
    @FXML private Label lblAvgConfidence;
    @FXML private Label lblPeakHour;

    // ==================== Charts ====================
    @FXML private BarChart<String, Number> hourlyBarChart;
    @FXML private CategoryAxis hourAxis;
    @FXML private NumberAxis hourCountAxis;

    @FXML private LineChart<String, Number> dailyLineChart;
    @FXML private CategoryAxis dateAxis;
    @FXML private NumberAxis dailyCountAxis;

    @FXML private PieChart categoryPieChart;

    // ==================== Top Targets Table ====================
    @FXML private TableView<TargetDetectionSummary> topTargetsTable;
    @FXML private TableColumn<TargetDetectionSummary, Integer> colRank;
    @FXML private TableColumn<TargetDetectionSummary, String> colTargetName;
    @FXML private TableColumn<TargetDetectionSummary, TargetCategory> colCategory;
    @FXML private TableColumn<TargetDetectionSummary, Long> colTotalDetections;
    @FXML private TableColumn<TargetDetectionSummary, String> colAvgConfidence;
    @FXML private TableColumn<TargetDetectionSummary, String> colLastSeen;

    // ==================== State & Services ====================
    private final DetectionAnalyticsService analyticsService = DetectionAnalyticsService.getInstance();
    private final ObservableList<TargetDetectionSummary> topTargetsList = FXCollections.observableArrayList();

    @FXML
    public void initialize() {
        setupTableColumns();
        setupDefaultDates();

        if (topTargetsTable != null) {
            topTargetsTable.setItems(topTargetsList);
        }

        log.info("AnalyticsController initialized successfully");
    }

    private void setupTableColumns() {
        if (colRank != null) {
            colRank.setCellFactory(column -> new TableCell<>() {
                @Override
                protected void updateItem(Integer item, boolean empty) {
                    super.updateItem(item, empty);
                    if (empty || getTableRow() == null || getTableRow().getItem() == null) {
                        setText(null);
                    } else {
                        setText(String.valueOf(getIndex() + 1));
                        setStyle("-fx-alignment: CENTER; -fx-font-weight: bold; -fx-text-fill: #94A3B8;");
                    }
                }
            });
        }

        if (colTargetName != null) {
            colTargetName.setCellValueFactory(new PropertyValueFactory<>("targetName"));
            colTargetName.setCellFactory(column -> new TableCell<>() {
                @Override
                protected void updateItem(String name, boolean empty) {
                    super.updateItem(name, empty);
                    if (empty || name == null) {
                        setText(null);
                    } else {
                        setText(name);
                        setStyle("-fx-font-weight: bold; -fx-text-fill: #E2E8F0;");
                    }
                }
            });
        }

        if (colCategory != null) {
            colCategory.setCellValueFactory(new PropertyValueFactory<>("category"));
            colCategory.setCellFactory(column -> new TableCell<>() {
                @Override
                protected void updateItem(TargetCategory cat, boolean empty) {
                    super.updateItem(cat, empty);
                    setText(null);
                    if (empty || cat == null) {
                        setGraphic(null);
                    } else {
                        Label badge = new Label(cat == TargetCategory.CRIMINAL ? "🔴 Criminal" : "🔵 Missing");
                        badge.getStyleClass().add("category-badge");
                        badge.getStyleClass().add(cat == TargetCategory.CRIMINAL ? "category-badge-criminal" : "category-badge-missing");
                        HBox container = new HBox(badge);
                        container.setAlignment(Pos.CENTER);
                        setGraphic(container);
                    }
                }
            });
        }

        if (colTotalDetections != null) {
            colTotalDetections.setCellValueFactory(new PropertyValueFactory<>("totalDetections"));
            colTotalDetections.setCellFactory(column -> new TableCell<>() {
                @Override
                protected void updateItem(Long count, boolean empty) {
                    super.updateItem(count, empty);
                    if (empty || count == null) {
                        setText(null);
                    } else {
                        setText(String.valueOf(count));
                        setStyle("-fx-alignment: CENTER; -fx-font-weight: bold; -fx-text-fill: #38BDF8;");
                    }
                }
            });
        }

        if (colAvgConfidence != null) {
            colAvgConfidence.setCellValueFactory(new PropertyValueFactory<>("avgConfidenceDisplay"));
            colAvgConfidence.setStyle("-fx-alignment: CENTER; -fx-text-fill: #10B981; -fx-font-weight: bold;");
        }

        if (colLastSeen != null) {
            colLastSeen.setCellValueFactory(new PropertyValueFactory<>("lastSeenDisplay"));
            colLastSeen.setStyle("-fx-alignment: CENTER; -fx-text-fill: #94A3B8;");
        }
    }

    private void setupDefaultDates() {
        if (dateFrom != null) dateFrom.setValue(LocalDate.now().minusDays(7));
        if (dateTo != null) dateTo.setValue(LocalDate.now());
    }

    // ==================== Presets & Handlers ====================

    @FXML
    public void handlePreset7Days() {
        if (dateFrom != null) dateFrom.setValue(LocalDate.now().minusDays(7));
        if (dateTo != null) dateTo.setValue(LocalDate.now());
        handleRefresh();
    }

    @FXML
    public void handlePreset30Days() {
        if (dateFrom != null) dateFrom.setValue(LocalDate.now().minusDays(30));
        if (dateTo != null) dateTo.setValue(LocalDate.now());
        handleRefresh();
    }

    @FXML
    public void handlePresetAllTime() {
        if (dateFrom != null) dateFrom.setValue(LocalDate.now().minusYears(1));
        if (dateTo != null) dateTo.setValue(LocalDate.now());
        handleRefresh();
    }

    @FXML
    public void handleRefresh() {
        LocalDate from = dateFrom != null ? dateFrom.getValue() : LocalDate.now().minusDays(7);
        LocalDate to = dateTo != null ? dateTo.getValue() : LocalDate.now();

        if (lblDateRangeSubtitle != null) {
            lblDateRangeSubtitle.setText(String.format("Showing analytics from %s to %s",
                    from.format(DATE_FMT), to.format(DATE_FMT)));
        }

        if (lblStatus != null) {
            lblStatus.setText("Querying analytics data...");
        }

        log.debug("handleRefresh triggered for range: {} to {}", from, to);
    }
}
