package com.drishtix.exception;

/**
 * Thrown when no face can be detected in an uploaded image.
 * Prevents registration of targets without a valid face template.
 */
public class FaceNotFoundException extends RuntimeException {

    public FaceNotFoundException(String message) {
        super(message);
    }

    public FaceNotFoundException(String message, Throwable cause) {
        super(message, cause);
    }
}
