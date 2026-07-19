package com.drishtix.exception;

/**
 * Thrown when a database operation fails in the DAO layer.
 * Wraps underlying SQLExceptions with domain-specific context.
 */
public class DatabaseException extends RuntimeException {

    public DatabaseException(String message) {
        super(message);
    }

    public DatabaseException(String message, Throwable cause) {
        super(message, cause);
    }
}
