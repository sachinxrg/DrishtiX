package com.drishtix.model;

import java.time.LocalDateTime;

/**
 * Entity representing an entry in the audit_log table.
 * Records every administrative action for accountability and compliance.
 */
public class AuditLogEntry {

    private long auditId;
    private String actionType;
    private Integer targetId;
    private String performedBy;
    private String details;
    private LocalDateTime performedAt;

    public AuditLogEntry() {
    }

    /**
     * Creates an audit log entry for a target-related action.
     */
    public AuditLogEntry(String actionType, Integer targetId, String performedBy, String details) {
        this.actionType = actionType;
        this.targetId = targetId;
        this.performedBy = performedBy;
        this.details = details;
        this.performedAt = LocalDateTime.now();
    }

    /**
     * Creates a system-level audit log entry.
     */
    public static AuditLogEntry systemAction(String actionType, String details) {
        return new AuditLogEntry(actionType, null, "SYSTEM", details);
    }

    /**
     * Creates a target-related audit log entry.
     */
    public static AuditLogEntry targetAction(String actionType, int targetId, String details) {
        return new AuditLogEntry(actionType, targetId, "OPERATOR", details);
    }

    // ==================== Getters & Setters ====================

    public long getAuditId() {
        return auditId;
    }

    public void setAuditId(long auditId) {
        this.auditId = auditId;
    }

    public String getActionType() {
        return actionType;
    }

    public void setActionType(String actionType) {
        this.actionType = actionType;
    }

    public Integer getTargetId() {
        return targetId;
    }

    public void setTargetId(Integer targetId) {
        this.targetId = targetId;
    }

    public String getPerformedBy() {
        return performedBy;
    }

    public void setPerformedBy(String performedBy) {
        this.performedBy = performedBy;
    }

    public String getDetails() {
        return details;
    }

    public void setDetails(String details) {
        this.details = details;
    }

    public LocalDateTime getPerformedAt() {
        return performedAt;
    }

    public void setPerformedAt(LocalDateTime performedAt) {
        this.performedAt = performedAt;
    }

    @Override
    public String toString() {
        return "AuditLogEntry{" + actionType + ", targetId=" + targetId +
                ", by=" + performedBy + ", at=" + performedAt + '}';
    }
}
