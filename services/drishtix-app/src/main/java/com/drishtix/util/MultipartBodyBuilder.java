package com.drishtix.util;

import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.net.http.HttpRequest;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.List;
import java.util.UUID;

/**
 * Builder for creating {@code multipart/form-data} request bodies compatible
 * with Java 11's {@link java.net.http.HttpClient}.
 * <p>
 * Java's built-in HttpClient does not support multipart bodies natively.
 * This utility constructs RFC 2046 compliant multipart bodies manually.
 * </p>
 * <p>
 * Usage:
 * <pre>{@code
 * MultipartBodyBuilder builder = new MultipartBodyBuilder()
 *     .addTextField("chat_id", "123456")
 *     .addFileField("photo", "snapshot.jpg", imageBytes, "image/jpeg");
 *
 * HttpRequest request = HttpRequest.newBuilder()
 *     .uri(URI.create("https://api.telegram.org/bot.../sendPhoto"))
 *     .header("Content-Type", builder.getContentType())
 *     .POST(builder.build())
 *     .build();
 * }</pre>
 * </p>
 */
public class MultipartBodyBuilder {

    private final String boundary;
    private final List<byte[]> parts;

    public MultipartBodyBuilder() {
        this.boundary = "----DrishtiX" + UUID.randomUUID().toString().replace("-", "");
        this.parts = new ArrayList<>();
    }

    /**
     * Adds a text field to the multipart body.
     *
     * @param name  the field name
     * @param value the text value
     * @return this builder for chaining
     */
    public MultipartBodyBuilder addTextField(String name, String value) {
        StringBuilder sb = new StringBuilder();
        sb.append("--").append(boundary).append("\r\n");
        sb.append("Content-Disposition: form-data; name=\"").append(name).append("\"\r\n");
        sb.append("\r\n");
        sb.append(value).append("\r\n");
        parts.add(sb.toString().getBytes(StandardCharsets.UTF_8));
        return this;
    }

    /**
     * Adds a file field to the multipart body from raw bytes.
     *
     * @param fieldName   the form field name (e.g., "file", "photo")
     * @param fileName    the file name to report (e.g., "snapshot.jpg")
     * @param fileBytes   the raw file content
     * @param contentType the MIME type (e.g., "image/jpeg")
     * @return this builder for chaining
     */
    public MultipartBodyBuilder addFileField(String fieldName, String fileName,
                                              byte[] fileBytes, String contentType) {
        ByteArrayOutputStream baos = new ByteArrayOutputStream();
        try {
            String header = "--" + boundary + "\r\n" +
                    "Content-Disposition: form-data; name=\"" + fieldName + "\"; filename=\"" + fileName + "\"\r\n" +
                    "Content-Type: " + contentType + "\r\n" +
                    "\r\n";
            baos.write(header.getBytes(StandardCharsets.UTF_8));
            baos.write(fileBytes);
            baos.write("\r\n".getBytes(StandardCharsets.UTF_8));
        } catch (IOException e) {
            throw new RuntimeException("Failed to build multipart file field", e);
        }
        parts.add(baos.toByteArray());
        return this;
    }

    /**
     * Adds a file field from a file path.
     *
     * @param fieldName   the form field name
     * @param filePath    the path to the file on disk
     * @param contentType the MIME type
     * @return this builder for chaining
     * @throws IOException if the file cannot be read
     */
    public MultipartBodyBuilder addFileField(String fieldName, Path filePath,
                                              String contentType) throws IOException {
        byte[] fileBytes = Files.readAllBytes(filePath);
        String fileName = filePath.getFileName().toString();
        return addFileField(fieldName, fileName, fileBytes, contentType);
    }

    /**
     * Returns the Content-Type header value including the boundary.
     * Must be set on the HttpRequest.
     */
    public String getContentType() {
        return "multipart/form-data; boundary=" + boundary;
    }

    /**
     * Builds the complete multipart body as an {@link HttpRequest.BodyPublisher}.
     */
    public HttpRequest.BodyPublisher build() {
        ByteArrayOutputStream baos = new ByteArrayOutputStream();
        try {
            for (byte[] part : parts) {
                baos.write(part);
            }
            // Final boundary
            String closing = "--" + boundary + "--\r\n";
            baos.write(closing.getBytes(StandardCharsets.UTF_8));
        } catch (IOException e) {
            throw new RuntimeException("Failed to build multipart body", e);
        }
        return HttpRequest.BodyPublishers.ofByteArray(baos.toByteArray());
    }
}
