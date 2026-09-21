# Feature Update Spec: Fix Target Deletion ForeignKey Integrity Error & Complete Cascade Deletion

**Date:** 2026-09-01  
**Author:** Product Manager & Systems Architect (AI)  
**Status:** Pending User Approval  
**Scope:** Data Tier (`target_registry.py`, `detection_log.py`, `target_dao.py`), Presentation Tier (`registry_view.py`), and Integration Tests

---

## 1. Problem Statement

When attempting to delete a target from the Target Watchlist Registry (`RegistryView`), the operation fails with a modal error:
```
(sqlite3.IntegrityError) NOT NULL constraint failed: detection_log.target_id
[SQL: UPDATE detection_log SET target_id=? WHERE detection_log.log_id = ?]
```

### Root Cause Analysis
1. **Missing Cascade Specification on `TargetRegistry.detection_logs` Relationship:**
   - In `TargetRegistry`, `images` and `embeddings` have `cascade="all, delete-orphan"`, but `detection_logs` was configured without a cascade option (`relationship(back_populates="target")`).
   - When `session.delete(target)` is invoked, SQLAlchemy's default behavior for a one-to-many relationship without a delete cascade is to disassociate child records by setting their foreign key to `NULL` (`UPDATE detection_log SET target_id=NULL WHERE log_id=?`).
   - Because `detection_log.target_id` is defined as `nullable=False`, the SQL `UPDATE` fails with `NOT NULL constraint failed: detection_log.target_id`.
2. **Missing `ondelete="CASCADE"` on `DetectionLog.target_id` ForeignKey:**
   - Unlike `FaceEmbedding` and `TargetImage` which specify `ForeignKey("target_registry.target_id", ondelete="CASCADE")`, `DetectionLog.target_id` only specifies `ForeignKey("target_registry.target_id")`.
3. **Incomplete Cleanup in `RegistryView._delete_target`:**
   - `RegistryView._delete_target` directly calls `TargetDAO.delete()`, bypassing `ErasureService.erase_target()`, which leaves orphaned snapshot image files on disk and does not purge in-memory Re-ID gallery profiles.

---

## 2. User Stories & Acceptance Criteria

### US-1: Clean Target Deletion with Cascade
**As an** operator, **I want** to delete any watchlist target even if it has hundreds of historical detection logs, **so that** the deletion succeeds without database integrity errors.

**Acceptance Criteria:**
- Deleting a target with existing detection log entries removes the target, its face embeddings, target images, and detection logs in a single atomic transaction.
- Zero `sqlite3.IntegrityError` exceptions raised.

### US-2: Complete Multi-Layer Data Erasure via UI
**As a** system administrator, **I want** deleting a target from the Registry View to perform full physical file and memory cleanup (DPDP Act §8(9) compliance), **so that** disk space is reclaimed and in-memory matching galleries are purged immediately.

**Acceptance Criteria:**
- `RegistryView._delete_target()` utilizes `ErasureService.erase_target()` (with `TargetDAO.delete()` fallback).
- In-memory gallery and Re-ID profiles are automatically reloaded/purged.

### US-3: Automated Regression & Cascade Tests
**As a** developer, **I want** unit and integration tests verifying target deletion with associated detection logs, **so that** future schema changes never reintroduce cascade deletion regressions.

**Acceptance Criteria:**
- Automated test `test_target_deletion_with_detection_logs` added to `tests/test_dao.py`.
- 100% pass rate across the full pytest suite (42+ tests).

---

## 3. Technical Architecture & Modifications

### Database Models
1. **`drishtix/models/detection_log.py`**:
   - Update `target_id` column definition to include `ForeignKey("target_registry.target_id", ondelete="CASCADE")`.
2. **`drishtix/models/target_registry.py`**:
   - Update `detection_logs` relationship to include `cascade="all, delete-orphan", passive_deletes=True`.

### Business & Presentation Logic
3. **`drishtix/ui/views/registry_view.py`**:
   - Refactor `_delete_target()` to call `ErasureService.erase_target()` with `TargetDAO.delete()` fallback, ensuring forensic snapshots on disk and Re-ID cache are also purged.

### Verification
4. **`tests/test_dao.py`**:
   - Add integration test for deleting targets that contain detection logs.
