package com.drishtix.controller;

import javafx.fxml.FXML;
import javafx.fxml.FXMLLoader;
import javafx.scene.Node;
import javafx.scene.control.Label;
import javafx.scene.layout.BorderPane;
import javafx.scene.layout.StackPane;
import javafx.scene.layout.VBox;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.io.IOException;
import java.util.HashMap;
import java.util.Map;

/**
 * Main controller managing the sidebar navigation and content area switching.
 * Orchestrates view transitions and maintains a cache of loaded views.
 */
public class MainController {

    private static final Logger log = LoggerFactory.getLogger(MainController.class);

    @FXML private BorderPane rootPane;
    @FXML private StackPane contentArea;
    @FXML private VBox navDashboard;
    @FXML private VBox navRegistry;
    @FXML private VBox navScanner;
    @FXML private VBox navLogs;
    @FXML private VBox navAnalytics;
    @FXML private VBox navSettings;
    @FXML private Label statusCamera;
    @FXML private Label statusDb;
    @FXML private Label statusFps;
    @FXML private Label statusTargets;

    private final Map<String, Node> viewCache = new HashMap<>();
    private final Map<String, Object> controllerCache = new HashMap<>();

    @FXML
    public void initialize() {
        log.info("MainController initializing...");

        // Set up navigation click handlers
        navDashboard.setOnMouseClicked(e -> switchView("dashboard"));
        navRegistry.setOnMouseClicked(e -> switchView("registry"));
        navScanner.setOnMouseClicked(e -> switchView("scanner"));
        navLogs.setOnMouseClicked(e -> switchView("logs"));
        navAnalytics.setOnMouseClicked(e -> switchView("analytics"));
        navSettings.setOnMouseClicked(e -> switchView("settings"));

        // Load dashboard as the default hero view
        switchView("dashboard");
    }

    /**
     * Switches the content area to the specified view.
     */
    public void switchView(String viewName) {
        try {
            Node view = viewCache.get(viewName);
            if (view == null) {
                String fxmlPath = getFxmlPath(viewName);
                FXMLLoader loader = new FXMLLoader(getClass().getResource(fxmlPath));
                view = loader.load();
                viewCache.put(viewName, view);
                controllerCache.put(viewName, loader.getController());
                log.info("View loaded and cached: {}", viewName);
            }

            contentArea.getChildren().setAll(view);
            updateActiveNavStyle(viewName);

        } catch (IOException e) {
            log.error("Failed to load view: {}", viewName, e);
        }
    }

    /**
     * Returns the controller for a cached view.
     */
    @SuppressWarnings("unchecked")
    public <T> T getController(String viewName) {
        return (T) controllerCache.get(viewName);
    }

    /**
     * Updates the status bar indicators.
     */
    public void updateStatusBar(boolean cameraActive, boolean dbConnected, int fps, int targetCount) {
        if (statusCamera != null) {
            statusCamera.setText(cameraActive ? "● Camera: Active" : "○ Camera: Inactive");
            statusCamera.setStyle(cameraActive ? "-fx-text-fill: #22C55E;" : "-fx-text-fill: #EF4444;");
        }
        if (statusDb != null) {
            statusDb.setText(dbConnected ? "● DB: Connected" : "○ DB: Disconnected");
            statusDb.setStyle(dbConnected ? "-fx-text-fill: #22C55E;" : "-fx-text-fill: #EF4444;");
        }
        if (statusFps != null) {
            statusFps.setText("FPS: " + fps);
        }
        if (statusTargets != null) {
            statusTargets.setText("Targets: " + targetCount);
        }
    }

    private String getFxmlPath(String viewName) {
        return switch (viewName) {
            case "dashboard" -> "/fxml/dashboard_view.fxml";
            case "registry" -> "/fxml/registry_view.fxml";
            case "scanner" -> "/fxml/image_scan_view.fxml";
            case "logs" -> "/fxml/detection_log_view.fxml";
            case "analytics" -> "/fxml/analytics_view.fxml";
            case "settings" -> "/fxml/settings_view.fxml";
            default -> throw new IllegalArgumentException("Unknown view: " + viewName);
        };
    }

    private void updateActiveNavStyle(String viewName) {
        // Reset all nav items
        navDashboard.getStyleClass().remove("nav-active");
        navRegistry.getStyleClass().remove("nav-active");
        navScanner.getStyleClass().remove("nav-active");
        navLogs.getStyleClass().remove("nav-active");
        navAnalytics.getStyleClass().remove("nav-active");
        navSettings.getStyleClass().remove("nav-active");

        // Set active
        VBox target = switch (viewName) {
            case "dashboard" -> navDashboard;
            case "registry" -> navRegistry;
            case "scanner" -> navScanner;
            case "logs" -> navLogs;
            case "analytics" -> navAnalytics;
            case "settings" -> navSettings;
            default -> navDashboard;
        };
        target.getStyleClass().add("nav-active");
    }
}
