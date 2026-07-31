package com.drishtix.util;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import javax.sound.sampled.*;
import java.io.*;

/**
 * Utility to generate simple alert WAV sounds at startup
 * if the sound resource files don't exist on the classpath.
 * <p>
 * Generates:
 * - alarm_criminal.wav: A two-tone siren (800Hz / 600Hz alternating)
 * - chime_missing.wav: A gentle two-note chime (523Hz / 659Hz)
 * </p>
 */
public final class SoundGenerator {

    private static final Logger log = LoggerFactory.getLogger(SoundGenerator.class);
    private static final float SAMPLE_RATE = 44100f;

    private SoundGenerator() {
    }

    /**
     * Ensures that the alert sound WAV files exist in the resources/sounds directory.
     * If they don't exist, generates them programmatically.
     */
    public static void ensureSoundFilesExist() {
        String soundsDir = "src/main/resources/sounds";
        File dir = new File(soundsDir);
        
        // Check if we're in a dev environment with source access
        if (!dir.exists()) {
            // In production, sounds are in the classpath. Check classpath instead.
            if (SoundGenerator.class.getClassLoader().getResource("sounds/alarm_criminal.wav") != null) {
                log.debug("Sound files found on classpath");
                return;
            }
            dir.mkdirs();
        }

        File criminalFile = new File(dir, "alarm_criminal.wav");
        File missingFile = new File(dir, "chime_missing.wav");

        if (!criminalFile.exists()) {
            generateSiren(criminalFile, 1.5);
            log.info("Generated alarm_criminal.wav");
        }

        if (!missingFile.exists()) {
            generateChime(missingFile, 0.8);
            log.info("Generated chime_missing.wav");
        }
    }

    /**
     * Generates a two-tone siren WAV file.
     */
    private static void generateSiren(File outputFile, double durationSeconds) {
        int numSamples = (int) (SAMPLE_RATE * durationSeconds);
        byte[] data = new byte[numSamples * 2]; // 16-bit mono

        double freq1 = 800.0;
        double freq2 = 600.0;
        double switchInterval = 0.15; // Switch tones every 150ms

        for (int i = 0; i < numSamples; i++) {
            double time = i / (double) SAMPLE_RATE;
            double freq = (int) (time / switchInterval) % 2 == 0 ? freq1 : freq2;
            double angle = 2.0 * Math.PI * freq * time;

            // Apply envelope (fade in/out)
            double envelope = 1.0;
            double fadeTime = 0.05;
            if (time < fadeTime) envelope = time / fadeTime;
            if (time > durationSeconds - fadeTime) envelope = (durationSeconds - time) / fadeTime;

            short sample = (short) (Short.MAX_VALUE * 0.7 * envelope * Math.sin(angle));
            data[i * 2] = (byte) (sample & 0xFF);
            data[i * 2 + 1] = (byte) ((sample >> 8) & 0xFF);
        }

        writeWav(outputFile, data);
    }

    /**
     * Generates a gentle two-note chime WAV file.
     */
    private static void generateChime(File outputFile, double durationSeconds) {
        int numSamples = (int) (SAMPLE_RATE * durationSeconds);
        byte[] data = new byte[numSamples * 2]; // 16-bit mono

        double freq1 = 523.25; // C5
        double freq2 = 659.25; // E5
        double halfDuration = durationSeconds / 2;

        for (int i = 0; i < numSamples; i++) {
            double time = i / (double) SAMPLE_RATE;
            double freq = time < halfDuration ? freq1 : freq2;
            double angle = 2.0 * Math.PI * freq * time;

            // Exponential decay envelope
            double noteTime = time < halfDuration ? time : time - halfDuration;
            double envelope = Math.exp(-noteTime * 4.0);

            short sample = (short) (Short.MAX_VALUE * 0.5 * envelope * Math.sin(angle));
            data[i * 2] = (byte) (sample & 0xFF);
            data[i * 2 + 1] = (byte) ((sample >> 8) & 0xFF);
        }

        writeWav(outputFile, data);
    }

    /**
     * Writes PCM data as a WAV file.
     */
    private static void writeWav(File file, byte[] pcmData) {
        try {
            AudioFormat format = new AudioFormat(SAMPLE_RATE, 16, 1, true, false);
            ByteArrayInputStream bais = new ByteArrayInputStream(pcmData);
            AudioInputStream ais = new AudioInputStream(bais, format, pcmData.length / 2);
            AudioSystem.write(ais, AudioFileFormat.Type.WAVE, file);
        } catch (IOException e) {
            log.error("Failed to write WAV file: {}", file.getAbsolutePath(), e);
        }
    }
}
