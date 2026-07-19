package com.drishtix.model;

import java.time.LocalDateTime;

/**
 * Entity representing a configuration entry in the alert_config table.
 * Used for runtime-configurable parameters like confidence threshold, cooldown, etc.
 */
public class AlertConfig {

    private int configId;
    private String configKey;
    private String configValue;
    private String description;
    private LocalDateTime updatedAt;

    public AlertConfig() {
    }

    public AlertConfig(String configKey, String configValue) {
        this.configKey = configKey;
        this.configValue = configValue;
    }

    public int getConfigId() {
        return configId;
    }

    public void setConfigId(int configId) {
        this.configId = configId;
    }

    public String getConfigKey() {
        return configKey;
    }

    public void setConfigKey(String configKey) {
        this.configKey = configKey;
    }

    public String getConfigValue() {
        return configValue;
    }

    public void setConfigValue(String configValue) {
        this.configValue = configValue;
    }

    public String getDescription() {
        return description;
    }

    public void setDescription(String description) {
        this.description = description;
    }

    public LocalDateTime getUpdatedAt() {
        return updatedAt;
    }

    public void setUpdatedAt(LocalDateTime updatedAt) {
        this.updatedAt = updatedAt;
    }

    /**
     * Returns the value parsed as a double.
     */
    public double getValueAsDouble() {
        return Double.parseDouble(configValue);
    }

    /**
     * Returns the value parsed as an integer.
     */
    public int getValueAsInt() {
        return Integer.parseInt(configValue);
    }

    /**
     * Returns the value parsed as a boolean.
     */
    public boolean getValueAsBoolean() {
        return Boolean.parseBoolean(configValue);
    }

    @Override
    public String toString() {
        return "AlertConfig{" + configKey + "=" + configValue + '}';
    }
}
