package com.drishtix.model;

/**
 * Enumeration representing the category of a watchlist target.
 * Determines alert severity, bounding box color, and sound type.
 */
public enum TargetCategory {

    /**
     * Criminal target — triggers RED bounding box + high-priority siren alarm.
     */
    CRIMINAL("CRIMINAL", "#FF4D2E", "alarm_criminal.wav"),

    /**
     * Missing person — triggers BLUE (cyan) bounding box + notification chime.
     */
    MISSING_PERSON("MISSING_PERSON", "#00D4FF", "chime_missing.wav");

    private final String dbValue;
    private final String boxColor;
    private final String soundFile;

    TargetCategory(String dbValue, String boxColor, String soundFile) {
        this.dbValue = dbValue;
        this.boxColor = boxColor;
        this.soundFile = soundFile;
    }

    public String getDbValue() {
        return dbValue;
    }

    /**
     * Returns the hex color code for the bounding box overlay.
     */
    public String getBoxColor() {
        return boxColor;
    }

    /**
     * Returns the sound file name to play on alert.
     */
    public String getSoundFile() {
        return soundFile;
    }

    /**
     * Parses a database string value into the corresponding enum constant.
     *
     * @param value the database string (e.g., "CRIMINAL" or "MISSING_PERSON")
     * @return the matching TargetCategory
     * @throws IllegalArgumentException if the value does not match any category
     */
    public static TargetCategory fromDbValue(String value) {
        for (TargetCategory cat : values()) {
            if (cat.dbValue.equalsIgnoreCase(value)) {
                return cat;
            }
        }
        throw new IllegalArgumentException("Unknown target category: " + value);
    }
}
