package com.drishtix.controller;

import com.drishtix.service.ConfigurationService;
import com.drishtix.util.AppConstants;
import com.drishtix.dao.DatabaseManager;
import javafx.fxml.FXML;
import javafx.scene.control.*;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

/**
 * Controller for the application Settings view.
 * Allows operators to configure detection, alert, and system parameters.
 */
public class SettingsController {

    private static final Logger log = LoggerFactory.getLogger(SettingsController.class);

    @FXML private Slider thresholdSlider;
    @FXML private Label lblThreshold;
    @FXML private Spinner<Integer> cooldownSpinner;
    @FXML private ComboBox<String> detectionMethod;
    @FXML private Spinner<Integer> minFaceSize;
    @FXML private CheckBox autoStartCamera;
    @FXML private CheckBox audioEnabled;
    @FXML private Spinner<Integer> retentionDays;
    @FXML private Label lblDbStatus;
    @FXML private TextField officerEmailField;
    @FXML private TextField telegramTokenField;
    @FXML private TextField telegramChatIdField;
    @FXML private CheckBox telegramEnabled;
    @FXML private CheckBox officerDispatchEnabled;

    private final ConfigurationService configService = ConfigurationService.getInstance();

    @FXML
    public void initialize() {
        // Load current values
        if (thresholdSlider != null) {
            thresholdSlider.setValue(configService.getConfidenceThreshold());
            thresholdSlider.valueProperty().addListener((obs, old, val) -> {
                if (lblThreshold != null) lblThreshold.setText(String.format("%.0f", val.doubleValue()));
            });
        }

        if (cooldownSpinner != null) {
            cooldownSpinner.setValueFactory(new SpinnerValueFactory.IntegerSpinnerValueFactory(
                    5, 300, configService.getAlertCooldownSeconds()));
        }

        if (detectionMethod != null) {
            detectionMethod.getItems().addAll("HAAR", "DNN");
            detectionMethod.setValue(configService.getDetectionMethod());
        }

        if (minFaceSize != null) {
            minFaceSize.setValueFactory(new SpinnerValueFactory.IntegerSpinnerValueFactory(
                    30, 200, configService.getMinFaceSize()));
        }

        if (autoStartCamera != null) {
            autoStartCamera.setSelected(configService.isAutoStartCamera());
        }

        if (audioEnabled != null) {
            audioEnabled.setSelected(configService.isAudioEnabled());
        }

        if (retentionDays != null) {
            retentionDays.setValueFactory(new SpinnerValueFactory.IntegerSpinnerValueFactory(
                    7, 365, configService.getSnapshotRetentionDays()));
        }

        if (officerEmailField != null) officerEmailField.setText(configService.getOfficerEmail());
        if (telegramTokenField != null) telegramTokenField.setText(configService.getTelegramBotToken());
        if (telegramChatIdField != null) telegramChatIdField.setText(configService.getTelegramChatId());
        if (telegramEnabled != null) telegramEnabled.setSelected(configService.isTelegramEnabled());
        if (officerDispatchEnabled != null) officerDispatchEnabled.setSelected(configService.isOfficerDispatchEnabled());

        // Test DB connection
        testDbConnection();
    }

    @FXML
    public void handleSaveSettings() {
        if (thresholdSlider != null)
            configService.updateConfig(AppConstants.CFG_CONFIDENCE_THRESHOLD,
                    String.valueOf(thresholdSlider.getValue()));
        if (cooldownSpinner != null)
            configService.updateConfig(AppConstants.CFG_ALERT_COOLDOWN,
                    String.valueOf(cooldownSpinner.getValue()));
        if (detectionMethod != null)
            configService.updateConfig(AppConstants.CFG_DETECTION_METHOD,
                    detectionMethod.getValue());
        if (minFaceSize != null)
            configService.updateConfig(AppConstants.CFG_MIN_FACE_SIZE,
                    String.valueOf(minFaceSize.getValue()));
        if (autoStartCamera != null)
            configService.updateConfig(AppConstants.CFG_AUTO_START_CAMERA,
                    String.valueOf(autoStartCamera.isSelected()));
        if (audioEnabled != null)
            configService.updateConfig(AppConstants.CFG_AUDIO_ENABLED,
                    String.valueOf(audioEnabled.isSelected()));
        if (retentionDays != null)
            configService.updateConfig(AppConstants.CFG_SNAPSHOT_RETENTION,
                    String.valueOf(retentionDays.getValue()));
        if (officerEmailField != null)
            configService.updateConfig(AppConstants.CFG_OFFICER_EMAIL, officerEmailField.getText().trim());
        if (telegramTokenField != null)
            configService.updateConfig(AppConstants.CFG_TELEGRAM_BOT_TOKEN, telegramTokenField.getText().trim());
        if (telegramChatIdField != null)
            configService.updateConfig(AppConstants.CFG_TELEGRAM_CHAT_ID, telegramChatIdField.getText().trim());
        if (telegramEnabled != null)
            configService.updateConfig(AppConstants.CFG_TELEGRAM_ENABLED, String.valueOf(telegramEnabled.isSelected()));
        if (officerDispatchEnabled != null)
            configService.updateConfig(AppConstants.CFG_OFFICER_DISPATCH_ENABLED, String.valueOf(officerDispatchEnabled.isSelected()));

        configService.refresh();
        log.info("Settings saved and configuration refreshed");

        Alert alert = new Alert(Alert.AlertType.INFORMATION);
        alert.setTitle("DrishtiX Settings");
        alert.setContentText("Settings saved successfully.");
        alert.showAndWait();
    }

    private void testDbConnection() {
        boolean connected = DatabaseManager.getInstance().testConnection();
        if (lblDbStatus != null) {
            lblDbStatus.setText(connected ? "● Connected" : "○ Disconnected");
            lblDbStatus.setStyle(connected
                    ? "-fx-text-fill: #22C55E; -fx-font-weight: bold;"
                    : "-fx-text-fill: #EF4444; -fx-font-weight: bold;");
        }
    }

    @FXML
    public void handleClearData() {
        Alert confirm = new Alert(Alert.AlertType.CONFIRMATION);
        confirm.setTitle("Clear System Data");
        confirm.setHeaderText("Nuclear Reset Warning");
        confirm.setContentText("This will permanently delete ALL registered targets, photos, detection logs, and audit trails.\n\nAre you absolutely sure you want to proceed?");
        
        // Style the alert to look dangerous
        confirm.getDialogPane().setStyle("-fx-base: #fee2e2;");
        
        ButtonType result = confirm.showAndWait().orElse(ButtonType.CANCEL);
        if (result == ButtonType.OK) {
            try {
                DatabaseManager.getInstance().clearSystemData();
                log.info("Operator triggered system data clear via Settings UI.");
                
                Alert success = new Alert(Alert.AlertType.INFORMATION);
                success.setTitle("Data Cleared");
                success.setContentText("All system data has been wiped successfully.");
                success.showAndWait();
                
            } catch (Exception e) {
                log.error("Failed to clear system data", e);
                Alert error = new Alert(Alert.AlertType.ERROR);
                error.setTitle("Error");
                error.setContentText("Failed to clear system data: " + e.getMessage());
                error.showAndWait();
            }
        }
    }

    @FXML
    public void handleTestDispatch() {
        // Save fields first
        handleSaveSettings();

        // Trigger test messages
        com.drishtix.service.TelegramAlertService.getInstance().sendTestMessage();
        
        Alert alert = new Alert(Alert.AlertType.INFORMATION);
        alert.setTitle("Officer Dispatch Test");
        alert.setHeaderText("📲 Messaging Dispatch Test Triggered");
        alert.setContentText("Test notification payload dispatched to configured Officer Channels (Telegram / Email).\nCheck your configured officer inbox/chat!");
        alert.showAndWait();
    }
}
