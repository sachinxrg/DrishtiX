# DrishtiX — Data Processing Notice

**Pursuant to India Digital Personal Data Protection Act, 2023**

---

## 1. Identity of the Data Fiduciary

**Organization:** [YOUR ORGANIZATION NAME]
**Contact:** [DATA PROTECTION OFFICER EMAIL]
**Address:** [REGISTERED ADDRESS]

---

## 2. Purpose of Processing

This system processes facial biometric data for the following lawful purposes:

| Purpose | Legal Basis (DPDP Act) |
|---------|----------------------|
| **Criminal identification** | §7(a) — Consent of the Data Principal, or §7(i) — Reasonable purpose for law enforcement |
| **Missing person search** | §7(i) — Reasonable purpose in the interest of the Data Principal |
| **Access control** | §7(a) — Consent of the Data Principal |

---

## 3. Categories of Personal Data Processed

| Data Category | Description | Retention Period |
|--------------|-------------|-----------------|
| **Facial images** | Photographs uploaded during target registration | Until erasure request or target deletion |
| **Face embeddings** | 128/512-dimensional mathematical vectors derived from facial features | Until erasure request or target deletion |
| **Body embeddings** | 512-dimensional vectors for whole-body re-identification | Session-only (in-memory, not persisted) |
| **Detection logs** | Timestamp, camera ID, confidence score of matches | Configurable (default: 30 days) |
| **Snapshot images** | Cropped face images captured during detection events | Configurable (default: 30 days) |
| **Demographic estimates** | Age range and gender estimates (not stored, display-only) | Not retained |

---

## 4. Rights of the Data Principal (§8)

Under the DPDP Act 2023, you have the right to:

1. **Access** (§8(3)): Request a summary of your personal data being processed.
2. **Correction** (§8(4)): Request correction of inaccurate personal data.
3. **Erasure** (§8(9)): Request complete deletion of your data when it is no longer necessary for the purpose of processing.
4. **Grievance Redressal** (§8(10)): File a complaint with the Data Protection Board of India.

### Exercising Your Rights

To exercise any of the above rights, contact the Data Protection Officer at the address listed in Section 1.

**Erasure requests** are processed via the system's built-in `ErasureService`, which performs:
- Database deletion of all target records, images, and embeddings
- Disk deletion of all snapshot image files
- Memory purge of in-memory body re-identification profiles
- Full audit trail of the erasure action

---

## 5. Data Security Measures (§9)

| Measure | Implementation |
|---------|---------------|
| **Encryption at rest** | SQLCipher AES-256 database encryption (opt-in via configuration) |
| **Access control** | Application-level authentication required for target management |
| **Audit trail** | All mutable operations logged with timestamps and action types |
| **Data minimization** | Embeddings are mathematical vectors — original biometric features cannot be reconstructed |
| **Retention limits** | Automatic purge of detection logs and snapshots beyond configurable retention period |

---

## 6. Data Breach Notification (§9(6))

In the event of a personal data breach, the Data Fiduciary will:
1. Notify the Data Protection Board of India without unreasonable delay.
2. Notify affected Data Principals as required by the Board.

---

## 7. Consent Record

By registering a target in DrishtiX, the authorized operator confirms that:
- [ ] The Data Principal has been informed of this notice (§6(1))
- [ ] Valid consent has been obtained where required (§7(a))
- [ ] The processing falls within a lawful exception under §7(i) if consent is not obtained

**Consent timestamp:** _______________
**Operator signature:** _______________

---

*This notice template should be customized for your specific deployment context and reviewed by legal counsel familiar with the DPDP Act 2023.*
