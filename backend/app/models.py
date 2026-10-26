from datetime import date, datetime

from sqlalchemy import (
    JSON,
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    LargeBinary,
    String,
    UniqueConstraint,
    Uuid,
)
from sqlalchemy.orm import Mapped, mapped_column

from .db import Base, uid, utcnow


class Institution(Base):
    __tablename__ = "institutions"
    id: Mapped[str] = mapped_column(Uuid(as_uuid=False), primary_key=True, default=uid)
    name: Mapped[str] = mapped_column(String(200))
    reference: Mapped[str] = mapped_column(String(40), unique=True)


class User(Base):
    __tablename__ = "users"
    __table_args__ = (
        CheckConstraint("role IN ('institution_admin','officer')"),
        CheckConstraint("(role = 'institution_admin') = (institution_id IS NOT NULL)"),
    )
    id: Mapped[str] = mapped_column(Uuid(as_uuid=False), primary_key=True, default=uid)
    email: Mapped[str] = mapped_column(String(200), unique=True)
    name: Mapped[str] = mapped_column(String(100))
    password_hash: Mapped[str] = mapped_column(String(300))
    role: Mapped[str] = mapped_column(String(30))
    institution_id: Mapped[str | None] = mapped_column(ForeignKey("institutions.id"))
    active: Mapped[bool] = mapped_column(Boolean, default=True)


class Programme(Base):
    __tablename__ = "programmes"
    __table_args__ = (
        UniqueConstraint("institution_id", "name", "academic_year"),
        CheckConstraint("approved_intake >= 0"),
    )
    id: Mapped[str] = mapped_column(Uuid(as_uuid=False), primary_key=True, default=uid)
    institution_id: Mapped[str] = mapped_column(ForeignKey("institutions.id"), index=True)
    name: Mapped[str] = mapped_column(String(120))
    academic_year: Mapped[str] = mapped_column(String(7))
    approved_intake: Mapped[int] = mapped_column(Integer)


class Person(Base):
    __tablename__ = "persons"
    id: Mapped[str] = mapped_column(Uuid(as_uuid=False), primary_key=True, default=uid)
    apaar_digest: Mapped[str] = mapped_column(String(64), unique=True)
    identity_enc: Mapped[bytes] = mapped_column(LargeBinary)
    suffix: Mapped[str] = mapped_column(String(4))


class RulePack(Base):
    __tablename__ = "rule_packs"
    id: Mapped[str] = mapped_column(String(80), primary_key=True)
    validator_version: Mapped[str] = mapped_column(String(40))
    content: Mapped[dict] = mapped_column(JSON)
    content_hash: Mapped[str] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class Batch(Base):
    __tablename__ = "upload_batches"
    __table_args__ = (UniqueConstraint("institution_id", "idempotency_key"),)
    id: Mapped[str] = mapped_column(Uuid(as_uuid=False), primary_key=True, default=uid)
    institution_id: Mapped[str] = mapped_column(ForeignKey("institutions.id"), index=True)
    academic_year: Mapped[str] = mapped_column(String(7))
    filename: Mapped[str] = mapped_column(String(200))
    file_hash: Mapped[str] = mapped_column(String(64))
    idempotency_key: Mapped[str] = mapped_column(String(100))
    rule_set_id: Mapped[str] = mapped_column(ForeignKey("rule_packs.id"))
    status: Mapped[str] = mapped_column(String(30), default="DRY_RUN_READY")
    summary: Mapped[dict] = mapped_column(JSON, default=dict)
    commit_summary: Mapped[dict | None] = mapped_column(JSON)
    result: Mapped[dict | None] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class BatchRow(Base):
    __tablename__ = "batch_rows"
    __table_args__ = (UniqueConstraint("batch_id", "row_no"),)
    id: Mapped[str] = mapped_column(Uuid(as_uuid=False), primary_key=True, default=uid)
    batch_id: Mapped[str] = mapped_column(ForeignKey("upload_batches.id"), index=True)
    row_no: Mapped[int] = mapped_column(Integer)
    raw_enc: Mapped[bytes] = mapped_column(LargeBinary)
    programme_id: Mapped[str | None] = mapped_column(ForeignKey("programmes.id"))
    student_ref: Mapped[str] = mapped_column(String(100))
    identity_status: Mapped[str] = mapped_column(String(30))
    identity_reason: Mapped[str] = mapped_column(String(50))
    status: Mapped[str] = mapped_column(String(30))
    issues: Mapped[list] = mapped_column(JSON, default=list)
    expected_enrolment_version: Mapped[int] = mapped_column(Integer, default=-1)


class Enrolment(Base):
    __tablename__ = "enrolments"
    __table_args__ = (
        UniqueConstraint("institution_id", "programme_id", "academic_year", "student_ref"),
        UniqueConstraint("person_id", "programme_id", "academic_year"),
        CheckConstraint("identity_status IN ('VERIFIED','MISSING','INVALID','PENDING_CHECK')"),
        CheckConstraint("status IN ('ENROLLED','WITHDRAWN','TRANSFERRED','COMPLETED')"),
        CheckConstraint("version >= 1", name="enrolment_positive_version"),
        CheckConstraint("start_date >= admission_date", name="enrolment_date_order"),
        CheckConstraint("end_date IS NULL OR end_date >= start_date", name="enrolment_end_date"),
        CheckConstraint("(status = 'ENROLLED') = (end_date IS NULL)", name="enrolment_status_end_date"),
        CheckConstraint(
            "(identity_status = 'VERIFIED') = (person_id IS NOT NULL)", name="enrolment_identity_link"
        ),
    )
    id: Mapped[str] = mapped_column(Uuid(as_uuid=False), primary_key=True, default=uid)
    institution_id: Mapped[str] = mapped_column(ForeignKey("institutions.id"), index=True)
    programme_id: Mapped[str] = mapped_column(ForeignKey("programmes.id"), index=True)
    academic_year: Mapped[str] = mapped_column(String(7))
    student_ref: Mapped[str] = mapped_column(String(100))
    person_id: Mapped[str | None] = mapped_column(ForeignKey("persons.id"))
    identity_enc: Mapped[bytes] = mapped_column(LargeBinary)
    identity_status: Mapped[str] = mapped_column(String(30))
    identity_reason: Mapped[str] = mapped_column(String(50))
    status: Mapped[str] = mapped_column(String(30))
    admission_date: Mapped[date] = mapped_column(Date)
    start_date: Mapped[date] = mapped_column(Date)
    end_date: Mapped[date | None] = mapped_column(Date)
    flags: Mapped[dict] = mapped_column(JSON, default=dict)
    version: Mapped[int] = mapped_column(Integer, default=1)
    batch_id: Mapped[str] = mapped_column(ForeignKey("upload_batches.id"))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class History(Base):
    __tablename__ = "enrolment_history"
    id: Mapped[str] = mapped_column(Uuid(as_uuid=False), primary_key=True, default=uid)
    enrolment_id: Mapped[str] = mapped_column(ForeignKey("enrolments.id"), index=True)
    version: Mapped[int] = mapped_column(Integer)
    snapshot: Mapped[dict] = mapped_column(JSON)
    actor_id: Mapped[str] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class Audit(Base):
    __tablename__ = "audit_events"
    id: Mapped[str] = mapped_column(Uuid(as_uuid=False), primary_key=True, default=uid)
    institution_id: Mapped[str | None] = mapped_column(ForeignKey("institutions.id"), index=True)
    actor_id: Mapped[str] = mapped_column(ForeignKey("users.id"))
    action: Mapped[str] = mapped_column(String(60))
    entity_id: Mapped[str] = mapped_column(String(100))
    details: Mapped[dict] = mapped_column(JSON, default=dict)
    request_id: Mapped[str | None] = mapped_column(String(36))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class ResolutionCase(Base):
    __tablename__ = "resolution_cases"
    __table_args__ = (
        UniqueConstraint("institution_id", "case_key"),
        CheckConstraint("(batch_row_id IS NOT NULL) != (enrolment_id IS NOT NULL)", name="case_one_subject"),
        CheckConstraint("owner_type IN ('COLLEGE_STAFF','STUDENT_ACTION','UPSTREAM_AUTHORITY')"),
        CheckConstraint(
            "status IN ('OPEN','WAITING_ON_USER','WAITING_ON_AUTHORITY','READY_TO_RECHECK','RESOLVED')"
        ),
        CheckConstraint("version >= 1 AND episode >= 1"),
    )
    id: Mapped[str] = mapped_column(Uuid(as_uuid=False), primary_key=True, default=uid)
    institution_id: Mapped[str] = mapped_column(ForeignKey("institutions.id"), index=True)
    case_key: Mapped[str] = mapped_column(String(64))
    batch_row_id: Mapped[str | None] = mapped_column(ForeignKey("batch_rows.id"))
    enrolment_id: Mapped[str | None] = mapped_column(ForeignKey("enrolments.id"))
    issue_code: Mapped[str] = mapped_column(String(60))
    rule_set_id: Mapped[str] = mapped_column(ForeignKey("rule_packs.id"))
    owner_type: Mapped[str] = mapped_column(String(30), default="COLLEGE_STAFF")
    assignee_id: Mapped[str | None] = mapped_column(ForeignKey("users.id"))
    status: Mapped[str] = mapped_column(String(30), default="OPEN")
    resolution_reason: Mapped[str | None] = mapped_column(String(40))
    evidence_kind: Mapped[str | None] = mapped_column(String(30))
    version: Mapped[int] = mapped_column(Integer, default=1)
    episode: Mapped[int] = mapped_column(Integer, default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class CaseOrigin(Base):
    __tablename__ = "resolution_case_origins"
    __table_args__ = (UniqueConstraint("case_id", "batch_row_id"),)
    id: Mapped[str] = mapped_column(Uuid(as_uuid=False), primary_key=True, default=uid)
    case_id: Mapped[str] = mapped_column(ForeignKey("resolution_cases.id"), index=True)
    batch_row_id: Mapped[str] = mapped_column(ForeignKey("batch_rows.id"))


class CaseEvent(Base):
    __tablename__ = "resolution_case_events"
    id: Mapped[str] = mapped_column(Uuid(as_uuid=False), primary_key=True, default=uid)
    case_id: Mapped[str] = mapped_column(ForeignKey("resolution_cases.id"), index=True)
    actor_id: Mapped[str] = mapped_column(ForeignKey("users.id"))
    old_status: Mapped[str | None] = mapped_column(String(30))
    new_status: Mapped[str] = mapped_column(String(30))
    owner_type: Mapped[str] = mapped_column(String(30))
    reason: Mapped[str] = mapped_column(String(40))
    version: Mapped[int] = mapped_column(Integer)
    operation_id: Mapped[str | None] = mapped_column(
        ForeignKey("correction_proposals.id", name="case_event_operation")
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class CorrectionProposal(Base):
    __tablename__ = "correction_proposals"
    __table_args__ = (CheckConstraint("case_version >= 1 AND target_version >= 0"),)
    id: Mapped[str] = mapped_column(Uuid(as_uuid=False), primary_key=True, default=uid)
    institution_id: Mapped[str] = mapped_column(ForeignKey("institutions.id"), index=True)
    actor_id: Mapped[str] = mapped_column(ForeignKey("users.id"))
    case_id: Mapped[str] = mapped_column(ForeignKey("resolution_cases.id"))
    case_version: Mapped[int] = mapped_column(Integer)
    target_enrolment_id: Mapped[str | None] = mapped_column(ForeignKey("enrolments.id"))
    target_version: Mapped[int] = mapped_column(Integer)
    rule_set_id: Mapped[str] = mapped_column(ForeignKey("rule_packs.id"))
    payload_enc: Mapped[bytes] = mapped_column(LargeBinary)
    payload_hash: Mapped[str] = mapped_column(String(64))
    intake_snapshot: Mapped[list] = mapped_column(JSON)
    preview: Mapped[dict] = mapped_column(JSON)
    result: Mapped[dict | None] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    applied_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class CorrectionOrigin(Base):
    __tablename__ = "correction_origins"
    id: Mapped[str] = mapped_column(Uuid(as_uuid=False), primary_key=True, default=uid)
    proposal_id: Mapped[str] = mapped_column(ForeignKey("correction_proposals.id"), index=True)
    batch_row_id: Mapped[str] = mapped_column(ForeignKey("batch_rows.id"), unique=True)
