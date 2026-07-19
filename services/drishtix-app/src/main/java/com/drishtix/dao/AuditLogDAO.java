package com.drishtix.dao;

import com.drishtix.exception.DatabaseException;
import com.drishtix.model.AuditLogEntry;
import com.mongodb.client.MongoCollection;
import org.bson.Document;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.util.Date;

/**
 * Data Access Object for the {@code audit_log} collection.
 * Insert-only — audit logs are immutable records.
 */
public class AuditLogDAO {

    private static final Logger log = LoggerFactory.getLogger(AuditLogDAO.class);
    private static final String COLLECTION = "audit_log";

    private MongoCollection<Document> collection() {
        return DatabaseManager.getInstance().getCollection(COLLECTION);
    }

    /**
     * Inserts an audit log entry. Fire-and-forget — errors are logged but not propagated
     * to avoid disrupting the primary operation.
     */
    public void insert(AuditLogEntry entry) {
        try {
            long id = DatabaseManager.getInstance().getNextSequenceLong(COLLECTION);
            Document doc = new Document("_id", id)
                    .append("action_type", entry.getActionType())
                    .append("target_id", entry.getTargetId())
                    .append("performed_by", entry.getPerformedBy())
                    .append("details", entry.getDetails())
                    .append("performed_at", new Date());

            collection().insertOne(doc);
            log.debug("Audit log recorded: action={}, targetId={}", entry.getActionType(), entry.getTargetId());

        } catch (Exception e) {
            // Audit logging should never crash the application
            log.error("Failed to insert audit log entry: {}", entry, e);
        }
    }
}
