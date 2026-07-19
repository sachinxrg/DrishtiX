package com.drishtix.exception;

/**
 * Thrown when the face recognition engine encounters an error.
 * May occur during training, prediction, or model I/O operations.
 */
public class RecognitionException extends RuntimeException {

    public RecognitionException(String message) {
        super(message);
    }

    public RecognitionException(String message, Throwable cause) {
        super(message, cause);
    }
}
