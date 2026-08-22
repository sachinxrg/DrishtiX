package com.drishtix.controller;

import com.drishtix.model.*;
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
import java.util.concurrent.CompletableFuture;

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

        handleRefresh();
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

        CompletableFuture.supplyAsync(() -> {
            try {
                return analyticsService.generateSnapshot(from, to);
            } catch (Exception e) {
                log.error("Failed to generate analytics snapshot", e);
                return null;
            }
        }).thenAccept(snapshot -> {
            Platform.runLater(() -> {
                if (snapshot == null) {
                    if (lblStatus != null) lblStatus.setText("⚠️ Failed to load analytics");
                    return;
                }

                // 1. Populate KPI Stat Cards
                if (lblTotalDetections != null) {
                    lblTotalDetections.setText(String.valueOf(snapshot.getTotalDetections()));
                }
                if (lblUniqueTargets != null) {
                    lblUniqueTargets.setText(String.valueOf(snapshot.getUniqueTargetsDetected()));
                }
                if (lblAvgConfidence != null) {
                    lblAvgConfidence.setText(snapshot.getAvgConfidenceDisplay());
                }
                if (lblPeakHour != null) {
                    lblPeakHour.setText(snapshot.getPeakHourDisplay());
                }

                // 2. Populate Hourly BarChart
                if (hourlyBarChart != null) {
                    hourlyBarChart.getData().clear();
                    XYChart.Series<String, Number> hourlySeries = new XYChart.Series<>();
                    hourlySeries.setName("Activity");
                    for (HourlyDetectionCount h : snapshot.getHourlyDistribution()) {
                        hourlySeries.getData().add(new XYChart.Data<>(h.getHourLabel(), h.getCount()));
                    }
                    hourlyBarChart.getData().add(hourlySeries);
                }

                // 3. Populate Daily Trend LineChart
                if (dailyLineChart != null) {
                    dailyLineChart.getData().clear();
                    XYChart.Series<String, Number> dailySeries = new XYChart.Series<>();
                    dailySeries.setName("Daily Detections");
                    for (DailyDetectionCount d : snapshot.getDailyTrend()) {
                        dailySeries.getData().add(new XYChart.Data<>(d.getDateLabel(), d.getCount()));
                    }
                    dailyLineChart.getData().add(dailySeries);
                }

                // 4. Populate Category PieChart
                if (categoryPieChart != null) {
                    categoryPieChart.getData().clear();
                    long crimCount = snapshot.getCategoryBreakdown().getOrDefault(TargetCategory.CRIMINAL, 0L);
                    long missCount = snapshot.getCategoryBreakdown().getOrDefault(TargetCategory.MISSING_PERSON, 0L);

                    if (crimCount > 0 || missCount > 0) {
                        PieChart.Data sliceCrim = new PieChart.Data(String.format("🔴 Criminal (%d)", crimCount), crimCount);
                        PieChart.Data sliceMiss = new PieChart.Data(String.format("🔵 Missing (%d)", missCount), missCount);
                        categoryPieChart.getData().addAll(sliceCrim, sliceMiss);
                    }
                }

                // 5. Populate Top-N Targets Table
                topTargetsList.setAll(snapshot.getTopTargets());

                // 6. Update Status
                if (lblStatus != null) {
                    lblStatus.setText(String.format("Updated: %d events across %d targets",
                            snapshot.getTotalDetections(), snapshot.getUniqueTargetsDetected()));
                }
            });
        });
    }
}
