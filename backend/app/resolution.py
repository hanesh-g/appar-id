"""Institution-owned issue work, without unrestricted personal-data comments."""

import hashlib
import json

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from .db import uid, utcnow
from .errors import DomainError
from .models import Batch, BatchRow, CaseEvent, CaseOrigin, Enrolment, ResolutionCase, User
from .permissions import Permission, require_permission
from .repositories import owned
from .rule_catalog import read_pack
from .services import audit

TRANSITIONS = {
    "OPEN": {"WAITING_ON_USER", "WAITING_ON_AUTHORITY", "READY_TO_RECHECK"},
    "WAITING_ON_USER": {"OPEN", "READY_TO_RECHECK"},
    "WAITING_ON_AUTHORITY": {"OPEN", "READY_TO_RECHECK"},
    "READY_TO_RECHECK": {"OPEN", "WAITING_ON_USER", "WAITING_ON_AUTHORITY", "RESOLVED"},
    "RESOLVED": {"OPEN"},
}


def work_key(programme_id, year, ref, issue_code, row_id=None):
    identity = [programme_id, year, ref] if programme_id and ref else ["row", row_id]
    return hashlib.sha256(json.dumps([identity, issue_code], separators=(",", ":")).encode()).hexdigest()


def case_event(db, case, user, old_status, reason, operation_id=None):
    db.add(
        CaseEvent(
            case_id=case.id,
            actor_id=user.id,
            old_status=old_status,
            new_status=case.status,
            owner_type=case.owner_type,
            reason=reason,
            version=case.version,
            operation_id=operation_id,
        )
    )
    audit(
        db,
        user,
        "CASE_CHANGED",
        case.id,
        {"status": case.status, "owner_type": case.owner_type, "reason": reason, "version": case.version},
    )


def own_case(db: Session, user: User, case_id: str, *, lock=False) -> ResolutionCase:
    require_permission(user, Permission.CASE_MANAGE)
    stmt = select(ResolutionCase).where(
        ResolutionCase.id == case_id, ResolutionCase.institution_id == user.institution_id
    )
    if lock:
        stmt = stmt.with_for_update().execution_options(populate_existing=True)
    case = db.scalar(stmt)
    if case is None:
        raise DomainError("NOT_FOUND", "Case not found", 404)
    return case


def open_case(db: Session, user: User, data) -> ResolutionCase:
    require_permission(user, Permission.CASE_MANAGE)
    origin = None
    if data.batch_row_id:
        origin = db.get(BatchRow, str(data.batch_row_id))
        if origin is None:
            raise DomainError("NOT_FOUND", "Row not found", 404)
        batch = owned(db, Batch, origin.batch_id, user)
        if batch.status == "DISCARDED" or origin.status == "SUPERSEDED_BY_CORRECTION":
            raise DomainError("ISSUE_CLOSED", "This row is no longer active correction work", 409)
        if not any(i["code"] == data.issue_code for i in origin.issues):
            raise DomainError("ISSUE_NOT_PRESENT", "Choose an issue reported on this row", 422)
        programme_id, year, ref = origin.programme_id, batch.academic_year, origin.student_ref
        record = None
        if origin.status == "COMMITTED":
            record = db.scalar(
                select(Enrolment).where(
                    Enrolment.institution_id == user.institution_id,
                    Enrolment.programme_id == programme_id,
                    Enrolment.academic_year == year,
                    Enrolment.student_ref == ref,
                )
            )
    else:
        record = owned(db, Enrolment, str(data.enrolment_id), user)
        batch = db.get(Batch, record.batch_id)
        programme_id, year, ref = record.programme_id, record.academic_year, record.student_ref
    if record is not None and (
        record.identity_status == "VERIFIED" or record.identity_reason != data.issue_code
    ):
        raise DomainError("ISSUE_NOT_PRESENT", "This issue is not present on the current record", 409)
    pack = read_pack(db, batch.rule_set_id)
    if data.issue_code not in pack["rules"]:
        raise DomainError("RULE_NOT_FOUND", "Rule explanation not found", 404)
    key = work_key(programme_id, year, ref, data.issue_code, origin.id if origin else None)
    created = db.scalar(
        insert(ResolutionCase)
        .values(
            id=uid(),
            institution_id=user.institution_id,
            case_key=key,
            batch_row_id=origin.id if record is None else None,
            enrolment_id=record.id if record else None,
            issue_code=data.issue_code,
            rule_set_id=batch.rule_set_id,
            owner_type="COLLEGE_STAFF",
            status="OPEN",
            version=1,
            episode=1,
        )
        .on_conflict_do_nothing(index_elements=[ResolutionCase.institution_id, ResolutionCase.case_key])
        .returning(ResolutionCase.id)
    )
    case = db.scalar(
        select(ResolutionCase)
        .where(ResolutionCase.institution_id == user.institution_id, ResolutionCase.case_key == key)
        .with_for_update()
    )
    if created:
        case_event(db, case, user, None, "ISSUE_OPENED")
    elif case.status == "RESOLVED":
        case.status, case.resolved_at, case.resolution_reason, case.evidence_kind = "OPEN", None, None, None
        case.version += 1
        case.episode += 1
        case.updated_at = utcnow()
        case_event(db, case, user, "RESOLVED", "ISSUE_REAPPEARED")
    if origin:
        db.execute(
            insert(CaseOrigin)
            .values(id=uid(), case_id=case.id, batch_row_id=origin.id)
            .on_conflict_do_nothing(index_elements=[CaseOrigin.case_id, CaseOrigin.batch_row_id])
        )
    db.commit()
    return case


def patch_case(db: Session, user: User, case_id: str, data) -> ResolutionCase:
    case = own_case(db, user, case_id, lock=True)
    if case.version != data.expected_version:
        raise DomainError("STALE_VERSION", "This case changed. Refresh before editing", 409)
    status = data.status or case.status
    owner = data.owner_type or case.owner_type
    if status != case.status and status not in TRANSITIONS[case.status]:
        raise DomainError("CASE_TRANSITION", "This case transition is not permitted", 422)
    if (status == "WAITING_ON_USER" and owner != "STUDENT_ACTION") or (
        status == "WAITING_ON_AUTHORITY" and owner != "UPSTREAM_AUTHORITY"
    ):
        raise DomainError("CASE_OWNER", "Choose the owner responsible for the next action", 422)
    assignee = str(data.assignee_id) if data.assignee_id else None
    if "assignee_id" not in data.model_fields_set:
        assignee = case.assignee_id
    if assignee:
        actor = db.scalar(
            select(User).where(
                User.id == assignee,
                User.institution_id == user.institution_id,
                User.role == "institution_admin",
                User.active.is_(True),
            )
        )
        if actor is None or owner != "COLLEGE_STAFF":
            raise DomainError("CASE_ASSIGNEE", "Choose an active staff member in this institution", 422)
    if status == "RESOLVED" and case.status != "RESOLVED":
        record = db.get(Enrolment, case.enrolment_id) if case.enrolment_id else None
        if record is None or record.identity_status != "VERIFIED":
            raise DomainError(
                "CASE_UNRESOLVED",
                "Apply a validated correction or complete an eligible recheck before closing",
                422,
            )
        case.resolution_reason, case.evidence_kind, case.resolved_at = "MOCK_RECHECK_PASSED", "MOCK", utcnow()
    if (status, owner, assignee) != (case.status, case.owner_type, case.assignee_id):
        old_status = case.status
        if old_status == "RESOLVED":
            case.episode += 1
            case.resolved_at = case.resolution_reason = case.evidence_kind = None
        case.status, case.owner_type, case.assignee_id = status, owner, assignee
        case.version += 1
        case.updated_at = utcnow()
        case_event(
            db, case, user, old_status, "ISSUE_REAPPEARED" if old_status == "RESOLVED" else "ROUTING_UPDATED"
        )
        db.commit()
    return case


def case_out(db: Session, case: ResolutionCase) -> dict:
    row = db.get(BatchRow, case.batch_row_id) if case.batch_row_id else None
    record = db.get(Enrolment, case.enrolment_id) if case.enrolment_id else None
    origin_id = db.scalar(select(CaseOrigin.batch_row_id).where(CaseOrigin.case_id == case.id).limit(1))
    origin = row or (db.get(BatchRow, origin_id) if origin_id else None)
    return {
        "id": case.id,
        "subject_kind": "STAGED_ROW" if row else "ENROLMENT",
        "batch_row_id": case.batch_row_id,
        "enrolment_id": case.enrolment_id,
        "origin_batch_id": origin.batch_id if origin else None,
        "student_ref": row.student_ref if row else record.student_ref,
        "issue_code": case.issue_code,
        "rule_set_id": case.rule_set_id,
        "owner_type": case.owner_type,
        "assignee_id": case.assignee_id,
        "status": case.status,
        "resolution_reason": case.resolution_reason,
        "evidence_kind": case.evidence_kind,
        "version": case.version,
        "episode": case.episode,
        "created_at": case.created_at,
        "updated_at": case.updated_at,
        "resolved_at": case.resolved_at,
    }
