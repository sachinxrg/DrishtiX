package com.drishtix.model;

import com.drishtix.util.AppConstants;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Nested;
import org.junit.jupiter.api.Test;

import static org.junit.jupiter.api.Assertions.*;

/**
 * Unit tests for {@link LockedTarget} confidence fusion math and lifecycle logic.
 * <p>
 * Validates the α/β weighting transitions:
 * - Face visible:        E_fused = 0.8·S_face + 0.2·S_body
 * - Face lost < 30f:     E_fused = 0.4·S_face + 0.6·S_body
 * - Face lost ≥ 30f:     E_fused = 0.0·S_face + 1.0·S_body
 * </p>
 */
class LockedTargetTest {

    /**
     * Creates a LockedTarget with known test values (no actual CSRT tracker).
     * We pass null for bodyTracker since fusion math doesn't touch it.
     */
    private LockedTarget createTestLock(double faceSimilarity, long acquiredFrame) {
        return new LockedTarget(
                42,                             // targetId
                "John Doe | CASE-001",          // label
                new int[]{46, 77, 255},         // COLOR_CRIMINAL_BGR
                null,                           // bodyTracker (not needed for math tests)
                null,                           // bodyBox (not needed for math tests)
                new float[128],                 // faceEmbedding placeholder
                faceSimilarity,
                acquiredFrame
        );
    }

    @Nested
    @DisplayName("Fusion Weight Transitions (α/β)")
    class FusionWeightTests {

        @Test
        @DisplayName("Face visible: α=0.8, β=0.2 → E_fused = 0.8·face + 0.2·body")
        void faceVisible_usesHighFaceWeight() {
            LockedTarget lock = createTestLock(0.90, 0);
            lock.setLastBodySimilarity(0.70);

            // Face is visible (default state at construction)
            lock.recomputeFusedConfidence(5);

            // E_fused = 0.8 × 0.90 + 0.2 × 0.70 = 0.72 + 0.14 = 0.86
            assertEquals(0.86, lock.getFusedConfidence(), 0.001,
                    "Face-visible fusion should weight α=0.8 for face, β=0.2 for body");
        }

        @Test
        @DisplayName("Face lost < 30 frames (grace): α=0.4, β=0.6")
        void faceLostGracePeriod_usesTransitionWeights() {
            LockedTarget lock = createTestLock(0.90, 0);
            lock.setLastBodySimilarity(0.70);

            // Simulate face loss at frame 10
            lock.markFaceLost();

            // Recompute at frame 25 → 15 frames since face (< 30 grace threshold)
            lock.recomputeFusedConfidence(25);

            // E_fused = 0.4 × 0.90 + 0.6 × 0.70 = 0.36 + 0.42 = 0.78
            assertEquals(0.78, lock.getFusedConfidence(), 0.001,
                    "Grace period fusion should use α=0.4, β=0.6");
        }

        @Test
        @DisplayName("Face lost ≥ 30 frames: α=0.0, β=1.0 (full body reliance)")
        void faceLostBeyondGrace_usesBodyOnly() {
            LockedTarget lock = createTestLock(0.90, 0);
            lock.setLastBodySimilarity(0.70);

            // Simulate face loss — lastFaceVisibleFrame stays at 0 (construction default)
            lock.markFaceLost();

            // Recompute at frame 50 → 50 frames since face (≥ 30)
            lock.recomputeFusedConfidence(50);

            // E_fused = 0.0 × 0.90 + 1.0 × 0.70 = 0.70
            assertEquals(0.70, lock.getFusedConfidence(), 0.001,
                    "Body-only mode should use α=0.0, β=1.0");
        }

        @Test
        @DisplayName("Face re-confirmation resets back to α=0.8 mode")
        void faceReconfirmed_resetsToFaceWeighted() {
            LockedTarget lock = createTestLock(0.90, 0);
            lock.setLastBodySimilarity(0.70);

            // Lose face → go to body-only
            lock.markFaceLost();
            lock.recomputeFusedConfidence(50);
            assertEquals(0.70, lock.getFusedConfidence(), 0.001);

            // Re-confirm face with updated embedding at frame 55
            lock.reconfirmFace(new float[128], 0.85, 55);
            lock.recomputeFusedConfidence(56);

            // E_fused = 0.8 × 0.85 + 0.2 × 0.70 = 0.68 + 0.14 = 0.82
            assertEquals(0.82, lock.getFusedConfidence(), 0.001,
                    "Re-confirmation should reset to face-weighted mode");
        }
    }

    @Nested
    @DisplayName("Release Conditions")
    class ReleaseTests {

        @Test
        @DisplayName("Should NOT release during normal operation")
        void normalOperation_shouldNotRelease() {
            LockedTarget lock = createTestLock(0.90, 100);
            lock.setLastBodySimilarity(0.80);
            lock.recomputeFusedConfidence(200);

            assertFalse(lock.shouldRelease(200),
                    "Lock with high confidence and recent face should not release");
        }

        @Test
        @DisplayName("Should release after max frames without face re-confirmation")
        void maxDurationExceeded_shouldRelease() {
            LockedTarget lock = createTestLock(0.90, 0);
            lock.setLastBodySimilarity(0.80);
            lock.markFaceLost();

            // Simulate exceeding max lock duration (900 frames) without face
            long frame = AppConstants.BODY_LOCK_MAX_FRAMES + AppConstants.BODY_LOCK_GRACE_FRAMES + 1;
            lock.recomputeFusedConfidence(frame);

            assertTrue(lock.shouldRelease(frame),
                    "Lock should release after max frames without face re-confirmation");
        }

        @Test
        @DisplayName("Should release after consecutive low-confidence frames")
        void lowConfidence_shouldRelease() {
            LockedTarget lock = createTestLock(0.10, 0);
            lock.setLastBodySimilarity(0.10);
            lock.markFaceLost();

            // Accumulate LOW_CONF_FRAMES consecutive frames below threshold
            for (int i = 1; i <= AppConstants.BODY_LOCK_LOW_CONF_FRAMES; i++) {
                lock.recomputeFusedConfidence(50 + i);
            }

            assertTrue(lock.shouldRelease(50 + AppConstants.BODY_LOCK_LOW_CONF_FRAMES),
                    "Lock should release after " + AppConstants.BODY_LOCK_LOW_CONF_FRAMES +
                            " consecutive low-confidence frames");
        }

        @Test
        @DisplayName("Active flag: setActive(false) forces release")
        void deactivated_shouldRelease() {
            LockedTarget lock = createTestLock(0.90, 0);
            lock.setActive(false);

            assertTrue(lock.shouldRelease(10),
                    "Deactivated lock should always release");
        }
    }

    @Nested
    @DisplayName("Body Re-Verification Scheduling")
    class ReverifyTests {

        @Test
        @DisplayName("Should NOT re-verify while face is visible")
        void faceVisible_noReverify() {
            LockedTarget lock = createTestLock(0.90, 0);
            // Face is visible by default → never needs body re-verification
            assertFalse(lock.needsBodyReverification(100),
                    "Body re-verification should not trigger while face is visible");
        }

        @Test
        @DisplayName("Should re-verify after interval when face is lost")
        void faceLost_reverifyAfterInterval() {
            LockedTarget lock = createTestLock(0.90, 0);
            lock.markFaceLost();

            // Not enough frames elapsed since lastBodyVerifyFrame (initialized to 0)
            assertFalse(lock.needsBodyReverification(
                            AppConstants.BODY_LOCK_REVERIFY_INTERVAL - 1),
                    "Should not re-verify before interval elapses");

            // Exactly at interval boundary
            assertTrue(lock.needsBodyReverification(
                            AppConstants.BODY_LOCK_REVERIFY_INTERVAL),
                    "Should re-verify at interval boundary");
        }

        @Test
        @DisplayName("setLastBodyVerifyFrame resets the interval counter")
        void setVerifyFrame_resetsCounter() {
            LockedTarget lock = createTestLock(0.90, 0);
            lock.markFaceLost();

            // Advance past interval
            assertTrue(lock.needsBodyReverification(AppConstants.BODY_LOCK_REVERIFY_INTERVAL));

            // Reset the verify frame
            lock.setLastBodyVerifyFrame(AppConstants.BODY_LOCK_REVERIFY_INTERVAL);

            // Should NOT need re-verify immediately after reset
            assertFalse(lock.needsBodyReverification(
                            AppConstants.BODY_LOCK_REVERIFY_INTERVAL + 1),
                    "Re-verify counter should reset after setLastBodyVerifyFrame");
        }
    }

    @Nested
    @DisplayName("Display Label & Color")
    class DisplayTests {

        @Test
        @DisplayName("Face visible → original label, no suffix")
        void faceVisible_originalLabel() {
            LockedTarget lock = createTestLock(0.90, 0);
            assertEquals("John Doe | CASE-001", lock.getDisplayLabel());
            assertArrayEquals(new int[]{46, 77, 255}, lock.getDisplayColor(),
                    "Face-visible should use original target color");
        }

        @Test
        @DisplayName("Face lost → [BODY] suffix + amber color")
        void faceLost_bodyLabelAndAmberColor() {
            LockedTarget lock = createTestLock(0.90, 0);
            lock.markFaceLost();
            assertEquals("John Doe | CASE-001 [BODY]", lock.getDisplayLabel());
            assertArrayEquals(AppConstants.COLOR_BODY_LOCK_BGR, lock.getDisplayColor(),
                    "Face-lost should use amber body lock color");
        }
    }
}
