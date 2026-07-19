package com.drishtix;

import com.drishtix.dao.DatabaseManager;
import com.drishtix.util.AppConstants;
import com.drishtix.util.SoundGenerator;
import com.drishtix.util.ThreadPools;
import javafx.application.Application;
import javafx.application.Platform;
import javafx.fxml.FXMLLoader;
import javafx.scene.Parent;
import javafx.scene.Scene;
import javafx.scene.image.Image;
import javafx.stage.Stage;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.io.InputStream;

/**
 * Main entry point for the DrishtiX Application.
 * <p>
 * Initializes JavaFX runtime, loads the main FXML view,
 * and sets up graceful shutdown hooks for thread pools and database connections.
 * </p>
 */
public class DrishtiXApp extends Application {

    private static final Logger log = LoggerFactory.getLogger(DrishtiXApp.class);

    @Override
    public void start(Stage primaryStage) {
        try {
            log.info("Starting {} v{}", AppConstants.APP_NAME, AppConstants.APP_VERSION);

            // Generate alert sounds if not present
            SoundGenerator.ensureSoundFilesExist();

            // Load the main FXML
            FXMLLoader loader = new FXMLLoader(getClass().getResource("/fxml/main_view.fxml"));
            Parent root = loader.load();

            // Create the scene
            Scene scene = new Scene(root, 1280, 800);

            // Load CSS
            String cssPath = getClass().getResource("/css/drishtix-dark.css").toExternalForm();
            scene.getStylesheets().add(cssPath);

            // Configure the stage
            primaryStage.setTitle(AppConstants.APP_NAME + " — " + AppConstants.APP_TAGLINE);
            primaryStage.setScene(scene);
            primaryStage.setMinWidth(1024);
            primaryStage.setMinHeight(700);

            // Set application icon
            try {
                InputStream iconStream = getClass().getResourceAsStream("/icons/logo.png");
                if (iconStream != null) {
                    primaryStage.getIcons().add(new Image(iconStream));
                }
            } catch (Exception e) {
                log.warn("Could not load application icon", e);
            }

            // Graceful shutdown
            primaryStage.setOnCloseRequest(event -> {
                log.info("Application shutdown initiated...");
                shutdown();
                Platform.exit();
            });

            primaryStage.show();
            log.info("{} started successfully — window: {}x{}", AppConstants.APP_NAME, 1280, 800);

        } catch (Exception e) {
            log.error("FATAL: Failed to start {}", AppConstants.APP_NAME, e);
            Platform.exit();
        }
    }

    /**
     * Graceful shutdown — releases all resources.
     */
    private void shutdown() {
        log.info("Shutting down {}...", AppConstants.APP_NAME);

        // Shutdown thread pools
        ThreadPools.shutdownAll();

        // Close database connections
        try {
            DatabaseManager.getInstance().shutdown();
        } catch (Exception e) {
            log.error("Error shutting down database", e);
        }

        log.info("{} shutdown complete", AppConstants.APP_NAME);
    }

    /**
     * Application entry point.
     */
    public static void main(String[] args) {
        log.info("Launching {} v{}", AppConstants.APP_NAME, AppConstants.APP_VERSION);
        launch(args);
    }
}
