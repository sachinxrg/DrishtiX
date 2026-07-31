package com.drishtix.util;

import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Nested;
import org.junit.jupiter.api.Test;

import java.net.http.HttpRequest;
import java.nio.charset.StandardCharsets;

import static org.junit.jupiter.api.Assertions.*;

/**
 * Unit tests for {@link MultipartBodyBuilder} — verifies RFC 2046 compliant
 * multipart/form-data body construction for Java 11 HttpClient.
 */
class MultipartBodyBuilderTest {

    @Nested
    @DisplayName("Content-Type Header")
    class ContentTypeTests {

        @Test
        @DisplayName("Content-Type starts with 'multipart/form-data; boundary='")
        void contentType_hasCorrectPrefix() {
            MultipartBodyBuilder builder = new MultipartBodyBuilder();
            String ct = builder.getContentType();
            assertTrue(ct.startsWith("multipart/form-data; boundary="),
                    "Content-Type must start with 'multipart/form-data; boundary=', got: " + ct);
        }

        @Test
        @DisplayName("Boundary starts with '----DrishtiX'")
        void boundary_hasProjectPrefix() {
            MultipartBodyBuilder builder = new MultipartBodyBuilder();
            String ct = builder.getContentType();
            String boundary = ct.replace("multipart/form-data; boundary=", "");
            assertTrue(boundary.startsWith("----DrishtiX"),
                    "Boundary should start with '----DrishtiX', got: " + boundary);
        }

        @Test
        @DisplayName("Each builder instance gets a unique boundary")
        void boundary_isUnique() {
            MultipartBodyBuilder a = new MultipartBodyBuilder();
            MultipartBodyBuilder b = new MultipartBodyBuilder();
            assertNotEquals(a.getContentType(), b.getContentType(),
                    "Two builder instances should produce different boundaries");
        }
    }

    @Nested
    @DisplayName("Text Fields")
    class TextFieldTests {

        @Test
        @DisplayName("Text field appears in built body with correct headers")
        void textField_presentInBody() {
            MultipartBodyBuilder builder = new MultipartBodyBuilder();
            builder.addTextField("chat_id", "123456");

            byte[] body = buildToBytes(builder);
            String bodyStr = new String(body, StandardCharsets.UTF_8);

            assertTrue(bodyStr.contains("Content-Disposition: form-data; name=\"chat_id\""),
                    "Body must contain Content-Disposition for chat_id");
            assertTrue(bodyStr.contains("123456"),
                    "Body must contain the field value");
        }

        @Test
        @DisplayName("Multiple text fields are all present")
        void multipleTextFields_allPresent() {
            MultipartBodyBuilder builder = new MultipartBodyBuilder();
            builder.addTextField("key1", "value1")
                   .addTextField("key2", "value2");

            byte[] body = buildToBytes(builder);
            String bodyStr = new String(body, StandardCharsets.UTF_8);

            assertTrue(bodyStr.contains("name=\"key1\""));
            assertTrue(bodyStr.contains("value1"));
            assertTrue(bodyStr.contains("name=\"key2\""));
            assertTrue(bodyStr.contains("value2"));
        }

        @Test
        @DisplayName("Fluent chaining returns same builder instance")
        void addTextField_returnsSameInstance() {
            MultipartBodyBuilder builder = new MultipartBodyBuilder();
            MultipartBodyBuilder returned = builder.addTextField("k", "v");
            assertSame(builder, returned);
        }
    }

    @Nested
    @DisplayName("File Fields")
    class FileFieldTests {

        @Test
        @DisplayName("File field includes filename and content-type in headers")
        void fileField_hasCorrectHeaders() {
            MultipartBodyBuilder builder = new MultipartBodyBuilder();
            byte[] fakeImage = {(byte) 0xFF, (byte) 0xD8, (byte) 0xFF}; // JPEG magic bytes
            builder.addFileField("photo", "snapshot.jpg", fakeImage, "image/jpeg");

            byte[] body = buildToBytes(builder);
            String bodyStr = new String(body, StandardCharsets.UTF_8);

            assertTrue(bodyStr.contains("name=\"photo\""),
                    "Body must contain field name 'photo'");
            assertTrue(bodyStr.contains("filename=\"snapshot.jpg\""),
                    "Body must contain the filename");
            assertTrue(bodyStr.contains("Content-Type: image/jpeg"),
                    "Body must contain the content type");
        }

        @Test
        @DisplayName("File bytes are embedded in the body")
        void fileField_bytesPresent() {
            byte[] payload = "HELLO_FILE_DATA".getBytes(StandardCharsets.UTF_8);
            MultipartBodyBuilder builder = new MultipartBodyBuilder();
            builder.addFileField("file", "test.txt", payload, "text/plain");

            byte[] body = buildToBytes(builder);
            String bodyStr = new String(body, StandardCharsets.UTF_8);

            assertTrue(bodyStr.contains("HELLO_FILE_DATA"),
                    "Body must contain the file payload");
        }

        @Test
        @DisplayName("Fluent chaining returns same builder instance")
        void addFileField_returnsSameInstance() {
            MultipartBodyBuilder builder = new MultipartBodyBuilder();
            MultipartBodyBuilder returned = builder.addFileField("f", "f.txt",
                    new byte[]{1}, "text/plain");
            assertSame(builder, returned);
        }
    }

    @Nested
    @DisplayName("Full Body Structure")
    class BodyStructureTests {

        @Test
        @DisplayName("Body ends with closing boundary '--boundary--'")
        void body_endsWithClosingBoundary() {
            MultipartBodyBuilder builder = new MultipartBodyBuilder();
            builder.addTextField("key", "value");

            byte[] body = buildToBytes(builder);
            String bodyStr = new String(body, StandardCharsets.UTF_8);

            // Extract boundary from content type
            String boundary = builder.getContentType()
                    .replace("multipart/form-data; boundary=", "");

            assertTrue(bodyStr.contains("--" + boundary + "--"),
                    "Body must end with closing boundary");
        }

        @Test
        @DisplayName("Mixed text and file fields produce valid body")
        void mixedFields_validBody() {
            MultipartBodyBuilder builder = new MultipartBodyBuilder();
            builder.addTextField("chat_id", "99999")
                   .addTextField("caption", "Test alert")
                   .addFileField("photo", "img.jpg", new byte[]{1, 2, 3}, "image/jpeg");

            byte[] body = buildToBytes(builder);
            String bodyStr = new String(body, StandardCharsets.UTF_8);

            String boundary = builder.getContentType()
                    .replace("multipart/form-data; boundary=", "");

            // Count boundary occurrences (should be 3 parts + 1 closing = boundary appears 4 times)
            int count = 0;
            int idx = 0;
            while ((idx = bodyStr.indexOf("--" + boundary, idx)) != -1) {
                count++;
                idx++;
            }
            assertEquals(4, count,
                    "Should have 3 part boundaries + 1 closing boundary");
        }

        @Test
        @DisplayName("build() returns a non-null BodyPublisher")
        void build_returnsPublisher() {
            MultipartBodyBuilder builder = new MultipartBodyBuilder();
            builder.addTextField("key", "val");
            HttpRequest.BodyPublisher publisher = builder.build();
            assertNotNull(publisher);
            assertTrue(publisher.contentLength() > 0,
                    "Publisher content length should be positive");
        }
    }

    // ==================== Helper ====================

    /**
     * Extracts raw bytes from the builder's BodyPublisher for string inspection.
     */
    private byte[] buildToBytes(MultipartBodyBuilder builder) {
        HttpRequest.BodyPublisher publisher = builder.build();
        // BodyPublishers.ofByteArray returns a publisher with known content length
        // We can reconstruct bytes by subscribing
        java.util.concurrent.CompletableFuture<byte[]> future = new java.util.concurrent.CompletableFuture<>();

        publisher.subscribe(new java.util.concurrent.Flow.Subscriber<>() {
            private final java.io.ByteArrayOutputStream baos = new java.io.ByteArrayOutputStream();

            @Override
            public void onSubscribe(java.util.concurrent.Flow.Subscription subscription) {
                subscription.request(Long.MAX_VALUE);
            }

            @Override
            public void onNext(java.nio.ByteBuffer item) {
                byte[] bytes = new byte[item.remaining()];
                item.get(bytes);
                baos.write(bytes, 0, bytes.length);
            }

            @Override
            public void onError(Throwable throwable) {
                future.completeExceptionally(throwable);
            }

            @Override
            public void onComplete() {
                future.complete(baos.toByteArray());
            }
        });

        try {
            return future.get(5, java.util.concurrent.TimeUnit.SECONDS);
        } catch (Exception e) {
            throw new RuntimeException("Failed to extract body bytes", e);
        }
    }
}
