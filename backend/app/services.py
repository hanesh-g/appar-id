import hashlib
from collections import Counter
from datetime import date, datetime
from zoneinfo import ZoneInfo

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from .config import Settings
from .context import request_id
from .db import uid, utcnow
from .errors import DomainError
from .models import Audit, Batch, BatchRow, Enrolment, History, Person, Programme, User
from .permissions import Permission, require_permission
from .registry import validate_identity
from .repositories import owned as owned
from .repositories import query_scope as query_scope
from .rule_catalog import ensure_current, require_executable
from .rules import issue, parse_csv, validate_rows
from .schemas import EnrolmentPatch
from .security import Crypto


def business_date() -> date:
    return datetime.now(ZoneInfo("Asia/Kolkata")).date()


def audit(db: Session, user: User, action: str, entity_id: str, details: dict | None = None) -> None:
    db.add(
        Audit(
            actor_id=user.id,
            institution_id=user.institution_id,
            action=action,
            entity_id=str(entity_id),
            details=details or {},
            request_id=request_id.get(),
        )
    )


def snapshot(enrolment: Enrolment) -> dict:
    return {
        "status": enrolment.status,
        "identity_status": enrolment.identity_status,
        "start_date": str(enrolment.start_date),
        "end_date": str(enrolment.end_date) if enrolment.end_date else None,
        "version": enrolment.version,
    }


def history(db: Session, enrolment: Enrolment, user: User) -> None:
    db.add(
        History(
            enrolment_id=enrolment.id,
            version=enrolment.version,
            snapshot=snapshot(enrolment),
            actor_id=user.id,
        )
    )


def has_error(row):
    return any(i["severity"] == "ERROR" for i in row["issues"])


def canonical(programme, year, ref):
    return programme, year, ref


def content_checks(db, rows, institution_id, crypto):
    enrolments = db.scalars(select(Enrolment).where(Enrolment.institution_id == institution_id)).all()
    existing = {canonical(e.programme_id, e.academic_year, e.student_ref): e for e in enrolments}
    people = {
        p.id: p
        for p in db.scalars(
            select(Person).where(Person.id.in_([e.person_id for e in enrolments if e.person_id]))
        ).all()
    }
    seen = {}
    for row in rows:
        if has_error(row):
            continue
        raw = row["raw"]
        key = canonical(row["programme_id"], raw["academic_year"], raw["student_ref"])
        old = existing.get(key)
        digest = crypto.digest(raw.get("apaar_id", ""))
        if (
            old
            and old.person_id
            and (row["identity_status"] != "VERIFIED" or people[old.person_id].apaar_digest != digest)
        ):
            row["issues"].append(
                issue(
                    "IDENTITY_REASSIGNMENT",
                    "apaar_id",
                    "A linked identity cannot be replaced automatically. Keep the verified identity and request review.",
                )
            )
        if row["identity_status"] == "VERIFIED":
            identity_key = (row["programme_id"], raw["academic_year"], digest)
            if identity_key in seen and seen[identity_key]["student_ref"] != row["student_ref"]:
                msg = issue(
                    "DUPLICATE_IDENTITY",
                    "apaar_id",
                    "The same verified identity appears under two student references in this programme.",
                )
                row["issues"].append(msg)
                seen[identity_key]["issues"].append(msg.copy())
            seen[identity_key] = row
            for enrolment in enrolments:
                if (
                    enrolment.person_id
                    and enrolment.programme_id == row["programme_id"]
                    and enrolment.academic_year == raw["academic_year"]
                    and enrolment.student_ref != raw["student_ref"]
                    and people[enrolment.person_id].apaar_digest == digest
                ):
                    row["issues"].append(
                        issue(
                            "DUPLICATE_IDENTITY",
                            "apaar_id",
                            "This identity already has an enrolment in the same programme and year.",
                        )
                    )
    return existing


def active(raw):
    return (
        raw["status"] == "ENROLLED"
        and date.fromisoformat(raw["start_date"]) <= business_date()
        and not raw.get("end_date")
    )


def summarize(db, rows, programmes, institution_id):
    current = db.scalars(select(Enrolment).where(Enrolment.institution_id == institution_id)).all()
    records = {
        canonical(e.programme_id, e.academic_year, e.student_ref): {
            "status": e.status,
            "start_date": str(e.start_date),
            "end_date": str(e.end_date) if e.end_date else "",
        }
        for e in current
    }
    before = Counter(key[0] for key, value in records.items() if active(value))
    for row in rows:
        if not has_error(row):
            raw = row["raw"]
            records[canonical(row["programme_id"], raw["academic_year"], raw["student_ref"])] = raw
    after = Counter(key[0] for key, value in records.items() if active(value))
    return {
        "rows_total": len(rows),
        "rows_ok": sum(not r["issues"] for r in rows),
        "rows_warning": sum(bool(r["issues"]) and not has_error(r) for r in rows),
        "rows_error": sum(has_error(r) for r in rows),
        "identity_counts": dict(Counter(r["identity_status"] for r in rows)),
        "issue_counts": dict(Counter(i["code"] for r in rows for i in r["issues"])),
        "intake": [
            {
                "programme_id": p.id,
                "programme": p.name,
                "before": before[p.id],
                "after": after[p.id],
                "approved": p.approved_intake,
                "excess": max(0, after[p.id] - p.approved_intake),
            }
            for p in programmes
        ],
        "registry_mode": "mock",
    }


def upload(
    db: Session,
    user: User,
    content: bytes,
    filename: str,
    year: str,
    key: str,
    crypto: Crypto,
    settings: Settings,
) -> Batch:
    require_permission(user, Permission.INSTITUTION_WRITE)
    fingerprint = hashlib.sha256(year.encode() + b"\0" + content).hexdigest()
    previous = db.scalar(
        select(Batch).where(Batch.institution_id == user.institution_id, Batch.idempotency_key == key)
    )
    if previous:
        if previous.file_hash != fingerprint:
            raise DomainError(
                "IDEMPOTENCY_CONFLICT", "Use a new request key for different upload content", 409
            )
        return previous
    programmes = db.scalars(
        select(Programme).where(
            Programme.institution_id == user.institution_id, Programme.academic_year == year
        )
    ).all()
    if not programmes:
        raise DomainError("PROGRAMMES_REQUIRED", "Add a programme for this academic year before uploading")
    rows = validate_rows(
        parse_csv(content), {p.name: p for p in programmes}, year, settings.mock_registry_outage
    )
    content_checks(db, rows, user.institution_id, crypto)
    batch = Batch(
        id=uid(),
        institution_id=user.institution_id,
        academic_year=year,
        filename=filename[:200],
        file_hash=fingerprint,
        idempotency_key=key,
        rule_set_id=ensure_current(db),
        summary=summarize(db, rows, programmes, user.institution_id),
    )
    db.add(batch)
    db.flush()
    for row in rows:
        db.add(
            BatchRow(
                batch_id=batch.id,
                row_no=row["row_no"],
                raw_enc=crypto.encrypt(row["raw"]),
                programme_id=row["programme_id"],
                student_ref=row["student_ref"],
                identity_status=row["identity_status"],
                identity_reason=row["identity_reason"],
                issues=row["issues"],
                status="ERROR" if has_error(row) else ("WARNING" if row["issues"] else "OK"),
            )
        )
    audit(db, user, "BATCH_UPLOADED", batch.id, {"rows": len(rows)})
    db.commit()
    return batch


def identity_fields(raw):
    return {k: raw.get(k, "") for k in ["apaar_id", "student_name", "date_of_birth"]}


def link_person(db: Session, raw: dict, crypto: Crypto) -> str:
    digest = crypto.digest(raw["apaar_id"])
    db.execute(
        insert(Person)
        .values(
            id=uid(),
            apaar_digest=digest,
            identity_enc=crypto.encrypt(identity_fields(raw)),
            suffix=raw["apaar_id"][-4:],
        )
        .on_conflict_do_nothing(index_elements=[Person.apaar_digest])
    )
    return db.scalar(select(Person.id).where(Person.apaar_digest == digest))


def commit_batch(db: Session, user: User, batch_id: str, mode: str, crypto: Crypto) -> Batch:
    require_permission(user, Permission.INSTITUTION_WRITE)
    batch = db.scalar(
        select(Batch)
        .where(Batch.id == batch_id, Batch.institution_id == user.institution_id)
        .with_for_update()
    )
    if not batch:
        raise DomainError("NOT_FOUND", "Batch not found", 404)
    if batch.status == "COMMITTED":
        return batch
    if batch.status != "DRY_RUN_READY":
        raise DomainError("BATCH_STATE", "Only a reviewed dry run can be committed", 409)
    require_executable(db, batch.rule_set_id)
    stored = db.scalars(select(BatchRow).where(BatchRow.batch_id == batch.id).order_by(BatchRow.row_no)).all()
    programmes = db.scalars(
        select(Programme)
        .where(
            Programme.institution_id == user.institution_id, Programme.academic_year == batch.academic_year
        )
        .order_by(Programme.id)
        .with_for_update()
    ).all()
    rows = [
        {
            "raw": crypto.decrypt(r.raw_enc),
            "programme_id": r.programme_id,
            "student_ref": r.student_ref,
            "issues": list(r.issues),
            "identity_status": r.identity_status,
            "identity_reason": r.identity_reason,
        }
        for r in stored
    ]
    originally_valid = [not has_error(r) for r in rows]
    existing = content_checks(db, rows, user.institution_id, crypto)
    if any(was_valid and has_error(row) for was_valid, row in zip(originally_valid, rows, strict=True)):
        raise DomainError(
            "STALE_PREVIEW",
            "Records changed after this preview. Upload again to review current conflicts",
            409,
        )
    if mode == "all_or_nothing" and any(has_error(r) for r in rows):
        raise DomainError(
            "BLOCKING_ERRORS", "Correct structural errors before using all-or-nothing commit", 409
        )
    batch.summary = summarize(db, rows, programmes, user.institution_id)
    created = updated = unchanged = held = 0
    for row, staged in zip(rows, stored, strict=True):
        if has_error(row):
            staged.status = "HELD"
            held += 1
            continue
        raw = row["raw"]
        key = canonical(row["programme_id"], raw["academic_year"], raw["student_ref"])
        enrolment = existing.get(key)
        person_id = link_person(db, raw, crypto) if row["identity_status"] == "VERIFIED" else None
        values = {
            "identity_status": row["identity_status"],
            "identity_reason": row["identity_reason"],
            "person_id": person_id,
            "status": raw["status"],
            "admission_date": date.fromisoformat(raw["admission_date"]),
            "start_date": date.fromisoformat(raw["start_date"]),
            "end_date": date.fromisoformat(raw["end_date"]) if raw["end_date"] else None,
            "flags": {k: raw[k] for k in ["seat_type", "supernumerary", "nri", "oci", "foreign_national"]},
        }
        identity = identity_fields(raw)
        if (
            enrolment
            and all(getattr(enrolment, k) == v for k, v in values.items())
            and crypto.decrypt(enrolment.identity_enc) == identity
        ):
            unchanged += 1
        else:
            if enrolment:
                enrolment.version += 1
                updated += 1
            else:
                enrolment = Enrolment(
                    id=uid(),
                    institution_id=user.institution_id,
                    programme_id=row["programme_id"],
                    academic_year=raw["academic_year"],
                    student_ref=raw["student_ref"],
                    version=1,
                )
                db.add(enrolment)
                existing[key] = enrolment
                created += 1
            for field, value in values.items():
                setattr(enrolment, field, value)
            enrolment.identity_enc = crypto.encrypt(identity)
            enrolment.batch_id, enrolment.updated_at = batch.id, utcnow()
            db.flush()
            history(db, enrolment, user)
        staged.status = "COMMITTED"
    batch.status = "COMMITTED"
    batch.result = {"created": created, "updated": updated, "unchanged": unchanged, "held": held}
    audit(db, user, "BATCH_COMMITTED", batch.id, batch.result)
    db.commit()
    return batch


def dashboard(db: Session, user: User, institution_id: str | None = None, year: str | None = None) -> dict:
    ps = query_scope(select(Programme), Programme, user)
    if institution_id:
        ps = ps.where(Programme.institution_id == institution_id)
    if year:
        ps = ps.where(Programme.academic_year == year)
    programmes = db.scalars(ps.order_by(Programme.name)).all()
    ids = [p.id for p in programmes]
    enrolments = db.scalars(select(Enrolment).where(Enrolment.programme_id.in_(ids))).all()
    active_records = [
        e
        for e in enrolments
        if e.status == "ENROLLED" and e.start_date <= business_date() and e.end_date is None
    ]
    counts = Counter(e.programme_id for e in active_records)
    existing_keys = {(e.programme_id, e.academic_year, e.student_ref) for e in enrolments}
    bs = query_scope(select(Batch), Batch, user).where(Batch.status != "DISCARDED")
    if institution_id:
        bs = bs.where(Batch.institution_id == institution_id)
    if year:
        bs = bs.where(Batch.academic_year == year)
    batches = db.scalars(bs.order_by(Batch.created_at.desc())).all()
    batch_map = {b.id: b for b in batches}
    held_rows = db.scalars(
        select(BatchRow).where(BatchRow.batch_id.in_(list(batch_map)), BatchRow.status.in_(["ERROR", "HELD"]))
    ).all()
    candidate_keys = {
        (r.programme_id, batch_map[r.batch_id].academic_year, r.student_ref)
        for r in held_rows
        if r.programme_id in ids and r.student_ref
    }
    intake = [
        {
            "id": p.id,
            "programme": p.name,
            "institution_id": p.institution_id,
            "academic_year": p.academic_year,
            "approved": p.approved_intake,
            "active": counts[p.id],
            "excess": max(0, counts[p.id] - p.approved_intake),
        }
        for p in programmes
    ]
    return {
        "active": len(active_records),
        "categories": {
            "base_count": sum(e.flags.get("supernumerary") == "N" for e in active_records),
            "supernumerary_count": sum(e.flags.get("supernumerary") == "Y" for e in active_records),
            "unclassified_count": sum(e.flags.get("supernumerary") not in {"Y", "N"} for e in active_records),
            "nri_count": sum(e.flags.get("nri") == "Y" for e in active_records),
            "oci_count": sum(e.flags.get("oci") == "Y" for e in active_records),
            "foreign_national_count": sum(e.flags.get("foreign_national") == "Y" for e in active_records),
        },
        "identity_counts": dict(Counter(e.identity_status for e in active_records)),
        "excess": sum(i["excess"] for i in intake),
        "programmes": intake,
        "held_candidates": len(candidate_keys - existing_keys),
        "unassignable_rows": sum(not r.programme_id or not r.student_ref for r in held_rows),
        "batches": [
            {
                "id": b.id,
                "filename": b.filename,
                "status": b.status,
                "rows_total": b.summary.get("rows_total", 0),
                "created_at": b.created_at,
            }
            for b in batches[:10]
        ],
        "registry_mode": "mock",
        "as_of": str(business_date()),
    }


def edit_enrolment(db: Session, user: User, object_id: str, data: EnrolmentPatch) -> Enrolment:
    require_permission(user, Permission.INSTITUTION_WRITE)
    # Use the same programme-before-enrolment lock order as commit/recheck.
    programme_id = db.scalar(
        select(Enrolment.programme_id).where(
            Enrolment.id == object_id, Enrolment.institution_id == user.institution_id
        )
    )
    if programme_id is None:
        raise DomainError("NOT_FOUND", "Record not found", 404)
    db.scalar(select(Programme.id).where(Programme.id == programme_id).with_for_update())
    record = db.scalar(
        select(Enrolment)
        .where(Enrolment.id == object_id, Enrolment.institution_id == user.institution_id)
        .with_for_update()
    )
    if not record:
        raise DomainError("NOT_FOUND", "Record not found", 404)
    if record.version != data.expected_version:
        raise DomainError("STALE_VERSION", "This record changed. Reload it before editing", 409)
    if data.status == "ENROLLED" and data.end_date is not None:
        raise DomainError("END_DATE", "An active enrolment must have no end date")
    if data.status != "ENROLLED" and (data.end_date is None or data.end_date < record.start_date):
        raise DomainError("END_DATE", "Provide an end date on or after the start date")
    if (record.status, record.end_date) != (data.status, data.end_date):
        record.status, record.end_date = data.status, data.end_date
        record.version += 1
        record.updated_at = utcnow()
        history(db, record, user)
        audit(db, user, "ENROLMENT_UPDATED", record.id, snapshot(record))
        db.commit()
    return record


def recheck(db: Session, user: User, crypto: Crypto, settings: Settings) -> dict:
    require_permission(user, Permission.INSTITUTION_WRITE)
    # Programme locks use the same order as commit and prevent identity-link races.
    db.scalars(
        select(Programme)
        .where(Programme.institution_id == user.institution_id)
        .order_by(Programme.id)
        .with_for_update()
    ).all()
    records = db.scalars(
        select(Enrolment)
        .where(
            Enrolment.institution_id == user.institution_id,
            Enrolment.identity_reason == "REGISTRY_UNAVAILABLE",
        )
        .order_by(Enrolment.id)
        .limit(500)
        .with_for_update()
    ).all()
    resolved = 0
    for record in records:
        raw = crypto.decrypt(record.identity_enc)
        state, reason = validate_identity(raw, settings.mock_registry_outage)
        person_id = None
        if state == "VERIFIED":
            person_id = link_person(db, raw, crypto)
            conflict = db.scalar(
                select(Enrolment.id).where(
                    Enrolment.person_id == person_id,
                    Enrolment.programme_id == record.programme_id,
                    Enrolment.academic_year == record.academic_year,
                    Enrolment.id != record.id,
                )
            )
            if conflict:
                state, reason, person_id = "PENDING_CHECK", "IDENTITY_CONFLICT", None
        if (state, reason) != (record.identity_status, record.identity_reason):
            record.identity_status, record.identity_reason, record.person_id = state, reason, person_id
            record.version += 1
            record.updated_at = utcnow()
            history(db, record, user)
            audit(db, user, "IDENTITY_RECHECKED", record.id, {"identity_status": state, "reason": reason})
        resolved += reason != "REGISTRY_UNAVAILABLE"
    db.commit()
    return {"checked": len(records), "resolved": resolved, "remaining": len(records) - resolved}
