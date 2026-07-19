package com.drishtix.util;

import org.bytedeco.opencv.opencv_core.Mat;

/**
 * Wrapper around OpenCV Mat that implements AutoCloseable for safe
 * resource management via try-with-resources.
 * <p>
 * OpenCV Mat objects hold native memory that is not tracked by the JVM garbage collector.
 * This wrapper ensures that {@link Mat#release()} is called deterministically.
 * </p>
 *
 * <pre>{@code
 * try (AutoCloseableMat mat = new AutoCloseableMat(someOpenCvOperation())) {
 *     // Use mat.get() safely
 * } // mat.release() is called automatically
 * }</pre>
 */
public class AutoCloseableMat implements AutoCloseable {

    private final Mat mat;

    /**
     * Wraps an existing Mat for automatic resource management.
     *
     * @param mat the OpenCV Mat to manage (may be null)
     */
    public AutoCloseableMat(Mat mat) {
        this.mat = mat;
    }

    /**
     * Creates a new empty Mat wrapped for auto-close.
     */
    public AutoCloseableMat() {
        this.mat = new Mat();
    }

    /**
     * Returns the underlying Mat.
     *
     * @return the wrapped Mat instance
     */
    public Mat get() {
        return mat;
    }

    /**
     * Returns true if the underlying Mat is not null and not empty.
     */
    public boolean isValid() {
        return mat != null && !mat.empty();
    }

    /**
     * Releases the native memory held by the Mat.
     */
    @Override
    public void close() {
        if (mat != null) {
            mat.release();
        }
    }
}
