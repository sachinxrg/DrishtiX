package com.drishtix.util;

import javafx.scene.image.Image;
import javafx.scene.image.PixelWriter;
import javafx.scene.image.WritableImage;
import org.bytedeco.opencv.opencv_core.Mat;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;



import static org.bytedeco.opencv.global.opencv_imgproc.*;

/**
 * Utility class for converting between OpenCV Mat and JavaFX Image.
 * Used to display processed OpenCV frames in JavaFX ImageView components.
 */
public final class FxImageConverter {

    private static final Logger log = LoggerFactory.getLogger(FxImageConverter.class);

    private FxImageConverter() {
        // Utility class — no instantiation
    }

    /**
     * Converts an OpenCV Mat (BGR or grayscale) to a JavaFX WritableImage.
     * <p>
     * This method handles both BGR 3-channel and grayscale 1-channel Mats.
     * The Mat is first converted to BGRA (4-channel) format for JavaFX compatibility.
     * </p>
     *
     * @param mat the OpenCV Mat to convert (must not be null or empty)
     * @return a JavaFX WritableImage, or null if conversion fails
     */
    public static Image matToImage(Mat mat) {
        if (mat == null || mat.empty()) {
            log.warn("Cannot convert null or empty Mat to Image");
            return null;
        }

        try (AutoCloseableMat bgraMat = new AutoCloseableMat()) {
            int channels = mat.channels();

            // Convert to BGRA for JavaFX compatibility
            if (channels == 1) {
                cvtColor(mat, bgraMat.get(), COLOR_GRAY2BGRA);
            } else if (channels == 3) {
                cvtColor(mat, bgraMat.get(), COLOR_BGR2BGRA);
            } else if (channels == 4) {
                mat.copyTo(bgraMat.get());
            } else {
                log.error("Unsupported number of channels: {}", channels);
                return null;
            }

            int width = bgraMat.get().cols();
            int height = bgraMat.get().rows();

            // Create byte buffer from Mat data
            byte[] pixels = new byte[width * height * 4];
            bgraMat.get().data().get(pixels);

            // Create JavaFX WritableImage and copy pixel data
            WritableImage writableImage = new WritableImage(width, height);
            PixelWriter pixelWriter = writableImage.getPixelWriter();

            // Convert from BGRA to the JavaFX pixel format (BGRA pre-multiplied)
            pixelWriter.setPixels(0, 0, width, height,
                    javafx.scene.image.PixelFormat.getByteBgraPreInstance(),
                    pixels, 0, width * 4);

            return writableImage;

        } catch (Exception e) {
            log.error("Failed to convert Mat to JavaFX Image", e);
            return null;
        }
    }

    /**
     * Creates a placeholder image of the specified dimensions with a solid color.
     *
     * @param width  image width in pixels
     * @param height image height in pixels
     * @return a solid dark image for use as a camera-off placeholder
     */
    public static Image createPlaceholder(int width, int height) {
        WritableImage image = new WritableImage(width, height);
        PixelWriter writer = image.getPixelWriter();
        for (int y = 0; y < height; y++) {
            for (int x = 0; x < width; x++) {
                writer.setArgb(x, y, 0xFF0A0E1A); // DrishtiX deep navy background
            }
        }
        return image;
    }
}
