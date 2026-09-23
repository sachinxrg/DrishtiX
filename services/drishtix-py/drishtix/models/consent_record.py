"""
DrishtiX v4.0 — Consent Record ORM model.

Tracks data processing consent per target as required by DPDP Act 2023 §6.
Each record captures when consent was obtained, by whom, and the legal
basis for processing. Supports consent withdrawal (§6(6)) via the
withdrawn_at timestamp.

This model does NOT implement the consent collection UI itself — it is
the persistence layer that the UI writes to and reads from.
"""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from drishtix.models.base import Base

if TYPE_CHECKING:
    from drishtix.models.target_registry import TargetRegistry


class ConsentRecord(Base):
    """
    DPDP Act §6 consent tracking record.

    Each target in the watchlist should have a corresponding consent record
    documenting the legal basis for processing their biometric data.
    """

    __tablename__ = "consent_record"

    consent_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    target_id: Mapped[int] = mapped_column(
        ForeignKey("target_registry.target_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    legal_basis: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="Legal basis: CONSENT, LAW_ENFORCEMENT, MISSING_PERSON, PUBLIC_INTEREST",
    )
    notice_version: Mapped[str] = mapped_column(
        String(20),
        default="1.0",
        nullable=False,
        comment="Version of the data processing notice shown at consent time",
    )
    collected_by: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        comment="Operator who collected consent",
    )
    consent_text: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Specific consent statement acknowledged",
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        comment="False if consent has been withdrawn",
    )
    collected_at: Mapped[datetime] = mapped_column(
        DateTime, default=func.now(), nullable=False
    )
    withdrawn_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True, comment="Timestamp of consent withdrawal (§6(6))"
    )

    # ─── Relationships ──────────────────────────────────────────────
    target: Mapped["TargetRegistry"] = relationship()

    def __repr__(self) -> str:
        status = "active" if self.is_active else f"withdrawn@{self.withdrawn_at}"
        return (
            f"ConsentRecord(id={self.consent_id}, target_id={self.target_id}, "
            f"basis={self.legal_basis}, status={status})"
        )
