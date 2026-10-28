"""Exact, expiring correction proposals over the existing validation/commit path."""

import csv
import hashlib
import io
from datetime import timedelta

from cryptography.exceptions import InvalidTag
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert

from . import services
from .db import uid, utcnow
from .errors import DomainError
from .institution_approval import require_institution, require_programmes
from .models import Batch, BatchRow, CaseOrigin, CorrectionOrigin, CorrectionProposal, Enrolment, Programme
from .resolution import case_event, own_case, work_key
from .rule_catalog import require_executable
from .schemas import HEADERS


def record_row(db, record, crypto):
    return {
        **crypto.decrypt(record.identity_enc),
        "student_ref": record.student_ref,
        "programme": db.get(Programme, record.programme_id).name,
        "academic_year": record.academic_year,
        "admission_date": record.admission_date.isoformat(),
        "start_date": record.start_date.isoformat(),
        "end_date": record.end_date.isoformat() if record.end_date else "",
        "status": record.status,
        **{
            key: record.flags.get(key, "")
            for key in ("seat_type", "supernumerary", "nri", "oci", "foreign_national")
        },
    }


def context(db, user, case_id, crypto):
    case = own_case(db, user, case_id)
    if case.enrolment_id:
        record = db.get(Enrolment, case.enrolment_id)
        raw = record_row(db, record, crypto)
        year = record.academic_year
    else:
        row = db.get(BatchRow, case.batch_row_id)
        batch = db.get(Batch, row.batch_id)
        if batch.status == "DISCARDED" or row.status == "SUPERSEDED_BY_CORRECTION":
            raise DomainError("ISSUE_CLOSED", "The source row is no longer active correction work", 409)
        raw = crypto.decrypt(row.raw_enc)
        year = batch.academic_year
    return case, {key: str(raw.get(key) or "") for key in HEADERS}, year


def evaluate(db, user, raw, year, settings, crypto):
    programmes = db.scalars(
        select(Programme)
        .where(Programme.institution_id == user.institution_id, Programme.academic_year == year)
        .order_by(Programme.id)
    ).all()
    rows = services.validate_rows([raw], {p.name: p for p in programmes}, year, settings.mock_registry_outage)
    existing = services.content_checks(db, rows, user.institution_id, crypto)
    row = rows[0]
    record = existing.get(
        services.canonical(row["programme_id"], row["raw"].get("academic_year"), row["student_ref"])
    )
    summary = services.summarize(db, rows, programmes, user.institution_id)
    snapshot = [
        {"programme_id": p["programme_id"], "active": p["before"], "approved": p["approved"]}
        for p in summary["intake"]
    ]
    return row, record, summary, snapshot


def masked(field, value):
    if not value:
        return "Not supplied"
    if field == "apaar_id":
        return "********" + value[-4:]
    if field in {"student_name", "date_of_birth"}:
        return "Protected value"
    return value


def preview(db, user, case_id, data, crypto, settings):
    case, original, year = context(db, user, case_id, crypto)
    approval = require_institution(db, user, year)
    if case.version != data.expected_version or case.status == "RESOLVED":
        raise DomainError("STALE_VERSION", "This case changed. Refresh before reviewing", 409)
    if set(data.changes) - set(HEADERS):
        raise DomainError("CORRECTION_FIELDS", "Only supported student fields can be corrected", 422)
    immutable = {"student_ref", "programme", "academic_year"} if case.enrolment_id else set()
    if any(key in immutable and value != original[key] for key, value in data.changes.items()):
        raise DomainError("CORRECTION_KEY", "This correction cannot move an existing enrolment key", 422)
    require_executable(db, case.rule_set_id)
    row, record, summary, snapshot = evaluate(db, user, {**original, **data.changes}, year, settings, crypto)
    if row["programme_id"]:
        require_programmes(approval, [db.get(Programme, row["programme_id"])])
    raw = row["raw"]
    blocked = services.has_error(row)
    same = (
        record is not None
        and record_row(db, record, crypto) == raw
        and record.identity_status == row["identity_status"]
    )
    outcome = {
        "created": int(not blocked and record is None),
        "updated": int(not blocked and record is not None and not same),
        "unchanged": int(not blocked and same),
        "held": int(blocked),
    }
    public = {
        "changes": [
            {
                "field": key,
                "before": masked(key, original.get(key, "")),
                "after": masked(key, str(raw.get(key) or "")),
            }
            for key in HEADERS
            if original.get(key, "") != str(raw.get(key) or "")
        ],
        "issues": row["issues"],
        "identity_status": row["identity_status"],
        "identity_reason": row["identity_reason"],
        "outcome": outcome,
        "active_delta": sum(p["after"] - p["before"] for p in summary["intake"]),
        "can_apply": not blocked,
        "rule_set_id": case.rule_set_id,
    }
    encrypted = crypto.encrypt(raw)
    proposal = CorrectionProposal(
        id=uid(),
        institution_id=user.institution_id,
        actor_id=user.id,
        case_id=case.id,
        case_version=case.version,
        target_enrolment_id=record.id if record else None,
        target_version=record.version if record else 0,
        rule_set_id=case.rule_set_id,
        payload_enc=encrypted,
        payload_hash=hashlib.sha256(encrypted).hexdigest(),
        intake_snapshot=snapshot,
        preview=public,
        expires_at=utcnow() + timedelta(minutes=10),
    )
    db.add(proposal)
    services.audit(
        db, user, "CORRECTION_PREVIEWED", proposal.id, {"case_id": case.id, "can_apply": not blocked}
    )
    db.commit()
    return {
        "id": proposal.id,
        "case_version": proposal.case_version,
        "target_version": proposal.target_version,
        "expires_at": proposal.expires_at,
        **public,
    }


def apply(db, user, proposal_id, data, crypto, settings):
    # Check the case capability even when an applied proposal is replayed.
    proposal = db.scalar(
        select(CorrectionProposal)
        .where(
            CorrectionProposal.id == proposal_id,
            CorrectionProposal.institution_id == user.institution_id,
            CorrectionProposal.actor_id == user.id,
        )
        .with_for_update()
    )
    if proposal is None:
        raise DomainError("NOT_FOUND", "Correction proposal not found", 404)
    own_case(db, user, proposal.case_id)
    if proposal.result is not None:
        return proposal.result
    if proposal.case_version != data.expected_version or proposal.expires_at <= utcnow():
        raise DomainError("STALE_PREVIEW", "The correction expired or changed. Review again", 409)
    if not proposal.preview["can_apply"]:
        raise DomainError("BLOCKING_ERRORS", "Correct blocking issues before applying", 422)
    if hashlib.sha256(proposal.payload_enc).hexdigest() != proposal.payload_hash:
        raise DomainError("PROPOSAL_INTEGRITY", "The proposal cannot be applied. Review again", 409)
    try:
        raw = crypto.decrypt(proposal.payload_enc)
    except (InvalidTag, ValueError):
        raise DomainError("PROPOSAL_INTEGRITY", "The proposal cannot be applied. Review again", 409) from None
    require_executable(db, proposal.rule_set_id)
    case = own_case(db, user, proposal.case_id)
    _, _, year = context(db, user, case.id, crypto)
    buffer = io.StringIO(newline="")
    writer = csv.DictWriter(buffer, fieldnames=HEADERS)
    writer.writeheader()
    writer.writerow(raw)
    batch = services.upload(
        db,
        user,
        buffer.getvalue().encode(),
        "inline-correction.csv",
        year,
        "correction:" + proposal.id,
        crypto,
        settings,
        finish=False,
        rule_set_id=proposal.rule_set_id,
    )

    def check_after_locks(db, child, rows, programmes):
        locked = own_case(db, user, proposal.case_id, lock=True)
        current, record, _, snapshot = evaluate(db, user, raw, year, settings, crypto)
        if (
            locked.version != proposal.case_version
            or locked.status == "RESOLVED"
            or snapshot != proposal.intake_snapshot
            or (record.id if record else None) != proposal.target_enrolment_id
            or (record.version if record else 0) != proposal.target_version
            or current["identity_status"] != proposal.preview["identity_status"]
            or current["identity_reason"] != proposal.preview["identity_reason"]
            or current["issues"] != proposal.preview["issues"]
        ):
            raise DomainError(
                "STALE_PREVIEW", "Records, intake, or identity results changed. Review again", 409
            )

    batch = services.commit_batch(
        db, user, batch.id, "all_or_nothing", crypto, finish=False, before_write=check_after_locks
    )
    case = own_case(db, user, proposal.case_id)
    target = db.scalar(
        select(Enrolment).where(
            Enrolment.institution_id == user.institution_id,
            Enrolment.academic_year == year,
            Enrolment.student_ref == raw["student_ref"],
            Enrolment.programme_id.in_(
                select(Programme.id).where(
                    Programme.institution_id == user.institution_id,
                    Programme.name == raw["programme"],
                    Programme.academic_year == year,
                )
            ),
        )
    )
    origins = db.scalars(
        select(BatchRow)
        .join(CaseOrigin, CaseOrigin.batch_row_id == BatchRow.id)
        .where(CaseOrigin.case_id == case.id)
    ).all()
    for origin in origins:
        origin.status = "SUPERSEDED_BY_CORRECTION"
        db.execute(
            insert(CorrectionOrigin)
            .values(id=uid(), proposal_id=proposal.id, batch_row_id=origin.id)
            .on_conflict_do_nothing(index_elements=[CorrectionOrigin.batch_row_id])
        )
    old_status = case.status
    case.batch_row_id, case.enrolment_id = None, target.id
    case.case_key = work_key(target.programme_id, target.academic_year, target.student_ref, case.issue_code)
    # Identity cases remain open until an actual mock match; clearing only one
    # identity warning must not hide the remaining identity gap.
    is_identity = case.issue_code.startswith("APAAR_") or case.issue_code in {
        "REGISTRY_UNAVAILABLE",
        "IDENTITY_MISMATCH",
        "IDENTITY_CONFLICT",
    }
    resolves = not is_identity or target.identity_status == "VERIFIED"
    if resolves:
        case.status, case.resolution_reason, case.evidence_kind, case.resolved_at = (
            "RESOLVED",
            "LOCAL_CORRECTION_APPLIED",
            "LOCAL",
            utcnow(),
        )
    case.version += 1
    case.updated_at = utcnow()
    case_event(db, case, user, old_status, "LOCAL_CORRECTION_APPLIED", proposal.id)
    proposal.applied_at = utcnow()
    proposal.result = {
        "proposal_id": proposal.id,
        "batch_id": batch.id,
        "enrolment_id": target.id,
        "case_id": case.id,
        "case_status": case.status,
        "case_version": case.version,
        "active_delta": proposal.preview["active_delta"],
        **batch.result,
    }
    db.commit()
    return proposal.result
