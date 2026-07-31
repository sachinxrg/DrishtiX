package com.drishtix.util;

import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Nested;
import org.junit.jupiter.api.Test;

import static org.junit.jupiter.api.Assertions.*;

/**
 * Unit tests for {@link VectorMathUtil} — the mathematical core of the ReID matching pipeline.
 * <p>
 * These tests verify cosine similarity computation and best-match lookup across
 * embedding vectors, covering happy paths, edge cases, and error conditions.
 * </p>
 */
class VectorMathUtilTest {

    // ==================== cosineSimilarity() ====================

    @Nested
    @DisplayName("cosineSimilarity()")
    class CosineSimilarityTests {

        @Test
        @DisplayName("Identical vectors → similarity = 1.0")
        void identicalVectors_returnOne() {
            double[] v = {0.5, 0.3, -0.2, 0.8, 0.1};
            assertEquals(1.0, VectorMathUtil.cosineSimilarity(v, v), 1e-9);
        }

        @Test
        @DisplayName("Opposite vectors → similarity = -1.0")
        void oppositeVectors_returnNegativeOne() {
            double[] a = {1.0, 2.0, 3.0};
            double[] b = {-1.0, -2.0, -3.0};
            assertEquals(-1.0, VectorMathUtil.cosineSimilarity(a, b), 1e-9);
        }

        @Test
        @DisplayName("Orthogonal vectors → similarity = 0.0")
        void orthogonalVectors_returnZero() {
            double[] a = {1.0, 0.0};
            double[] b = {0.0, 1.0};
            assertEquals(0.0, VectorMathUtil.cosineSimilarity(a, b), 1e-9);
        }

        @Test
        @DisplayName("Known computation: (1,2,3) vs (4,5,6)")
        void knownVectors_correctResult() {
            double[] a = {1, 2, 3};
            double[] b = {4, 5, 6};
            // dot = 32, |a| = sqrt(14), |b| = sqrt(77)
            double expected = 32.0 / (Math.sqrt(14) * Math.sqrt(77));
            assertEquals(expected, VectorMathUtil.cosineSimilarity(a, b), 1e-9);
        }

        @Test
        @DisplayName("512-dimensional identical vectors → similarity = 1.0")
        void highDimensional_identicalVectors() {
            double[] v = new double[512];
            for (int i = 0; i < 512; i++) {
                v[i] = Math.sin(i * 0.1); // arbitrary non-trivial values
            }
            assertEquals(1.0, VectorMathUtil.cosineSimilarity(v, v), 1e-9);
        }

        @Test
        @DisplayName("Zero vector → returns 0.0 (no crash)")
        void zeroVector_returnsZero() {
            double[] zero = {0.0, 0.0, 0.0};
            double[] nonZero = {1.0, 2.0, 3.0};
            assertEquals(0.0, VectorMathUtil.cosineSimilarity(zero, nonZero), 1e-9);
        }

        @Test
        @DisplayName("Both zero vectors → returns 0.0")
        void bothZeroVectors_returnsZero() {
            double[] z = {0.0, 0.0};
            assertEquals(0.0, VectorMathUtil.cosineSimilarity(z, z), 1e-9);
        }

        @Test
        @DisplayName("Null first vector → IllegalArgumentException")
        void nullFirstVector_throwsException() {
            double[] b = {1.0, 2.0};
            assertThrows(IllegalArgumentException.class,
                    () -> VectorMathUtil.cosineSimilarity(null, b));
        }

        @Test
        @DisplayName("Null second vector → IllegalArgumentException")
        void nullSecondVector_throwsException() {
            double[] a = {1.0, 2.0};
            assertThrows(IllegalArgumentException.class,
                    () -> VectorMathUtil.cosineSimilarity(a, null));
        }

        @Test
        @DisplayName("Dimension mismatch → IllegalArgumentException")
        void dimensionMismatch_throwsException() {
            double[] a = {1.0, 2.0};
            double[] b = {1.0, 2.0, 3.0};
            IllegalArgumentException ex = assertThrows(IllegalArgumentException.class,
                    () -> VectorMathUtil.cosineSimilarity(a, b));
            assertTrue(ex.getMessage().contains("2 vs 3"));
        }

        @Test
        @DisplayName("Empty vectors → IllegalArgumentException")
        void emptyVectors_throwsException() {
            double[] empty = {};
            assertThrows(IllegalArgumentException.class,
                    () -> VectorMathUtil.cosineSimilarity(empty, empty));
        }

        @Test
        @DisplayName("Result is always in [-1.0, 1.0] range")
        void result_inValidRange() {
            double[] a = {100.0, -200.0, 300.0};
            double[] b = {-50.0, 100.0, -150.0};
            double sim = VectorMathUtil.cosineSimilarity(a, b);
            assertTrue(sim >= -1.0 && sim <= 1.0,
                    "Similarity " + sim + " out of range [-1, 1]");
        }
    }

    // ==================== findBestMatch() ====================

    @Nested
    @DisplayName("findBestMatch()")
    class FindBestMatchTests {

        @Test
        @DisplayName("Exact match found above threshold")
        void exactMatch_returnsCorrectIndex() {
            double[] query = {1.0, 0.0, 0.0};
            double[][] candidates = {
                    {0.0, 1.0, 0.0},  // orthogonal = 0.0
                    {1.0, 0.0, 0.0},  // identical = 1.0
                    {0.5, 0.5, 0.0},  // partial match
            };
            assertEquals(1, VectorMathUtil.findBestMatch(query, candidates, 0.85));
        }

        @Test
        @DisplayName("No candidate above threshold → returns -1")
        void noCandidateAboveThreshold_returnsNegativeOne() {
            double[] query = {1.0, 0.0, 0.0};
            double[][] candidates = {
                    {0.0, 1.0, 0.0},  // 0.0 similarity
                    {0.0, 0.0, 1.0},  // 0.0 similarity
            };
            assertEquals(-1, VectorMathUtil.findBestMatch(query, candidates, 0.85));
        }

        @Test
        @DisplayName("Returns highest similarity when multiple exceed threshold")
        void multipleAboveThreshold_returnsBest() {
            double[] query = {1.0, 0.0, 0.0};
            double[][] candidates = {
                    {0.9, 0.1, 0.0},  // high similarity
                    {1.0, 0.0, 0.0},  // perfect = 1.0 (best)
                    {0.95, 0.05, 0.0}, // very high
            };
            assertEquals(1, VectorMathUtil.findBestMatch(query, candidates, 0.5));
        }

        @Test
        @DisplayName("Null query → returns -1")
        void nullQuery_returnsNegativeOne() {
            double[][] candidates = {{1.0, 0.0}};
            assertEquals(-1, VectorMathUtil.findBestMatch(null, candidates, 0.85));
        }

        @Test
        @DisplayName("Null candidates array → returns -1")
        void nullCandidates_returnsNegativeOne() {
            double[] query = {1.0, 0.0};
            assertEquals(-1, VectorMathUtil.findBestMatch(query, null, 0.85));
        }

        @Test
        @DisplayName("Empty candidates array → returns -1")
        void emptyCandidates_returnsNegativeOne() {
            double[] query = {1.0, 0.0};
            assertEquals(-1, VectorMathUtil.findBestMatch(query, new double[0][], 0.85));
        }

        @Test
        @DisplayName("Null candidate in array is skipped gracefully")
        void nullCandidateEntry_skipped() {
            double[] query = {1.0, 0.0};
            double[][] candidates = {
                    null,
                    {1.0, 0.0},  // perfect match
            };
            assertEquals(1, VectorMathUtil.findBestMatch(query, candidates, 0.85));
        }

        @Test
        @DisplayName("Dimension-mismatched candidate is skipped")
        void mismatchedCandidate_skipped() {
            double[] query = {1.0, 0.0};
            double[][] candidates = {
                    {1.0, 0.0, 0.5},  // wrong dimensions — skipped
                    {1.0, 0.0},       // correct — match
            };
            assertEquals(1, VectorMathUtil.findBestMatch(query, candidates, 0.85));
        }

        @Test
        @DisplayName("Threshold of 0.0 matches any non-orthogonal candidate")
        void zeroThreshold_matchesAny() {
            double[] query = {1.0, 0.5};
            double[][] candidates = {
                    {0.5, 1.0},  // some positive similarity
            };
            assertEquals(0, VectorMathUtil.findBestMatch(query, candidates, 0.0));
        }
    }
}
