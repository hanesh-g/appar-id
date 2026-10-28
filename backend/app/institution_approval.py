"""Synthetic evidence review and admission gates; no official AICTE integration."""

import hashlib
import json
from datetime import date
from pathlib import Path

from sqlalchemy import select, text

from .db import uid, utcnow
from .errors import DomainError
from .models import Institution, InstitutionApproval, InstitutionApprovalEvent, Programme, User
from .permissions import Permission, require_permission

CATALOGUE_PATH = Path(__file__).parent / "data" / "institution-approvals-demo.json"


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def catalogue():
    try:
        value = json.loads(CATALOGUE_PATH.read_text(encoding="utf-8"))
        if value["mode"] != "DEMO_FIXTURE" or not isinstance(value["institutions"], list):
            raise ValueError("Unsupported catalogue")
        for entry in value["institutions"]:
            if date.fromisoformat(entry["valid_until"]) < date.fromisoformat(entry["valid_from"]):
                raise ValueError("Invalid evidence dates")
        return value, digest(value)
    except (OSError, ValueError, KeyError, TypeError):
        raise DomainError(
            "APPROVAL_SOURCE_UNAVAILABLE", "Demo approval evidence is unavailable", 503
        ) from None


def lock_scope(db, institution_id):
    # Every decision, admission writer and programme edit takes this before
    # programme/person/enrolment locks; operation headers can precede it.
    key = int.from_bytes(
        hashlib.sha256(("institution-approval:" + institution_id).encode()).digest()[:8],
        "big",
        signed=True,
    )
    db.execute(text("SELECT pg_advisory_xact_lock(:key)"), {"key": key})


def programme_snapshot(programme):
    return {
        "id": programme.id,
        "name": programme.name,
        "academic_year": programme.academic_year,
        "intake": programme.approved_intake,
    }


def candidate(db, institution, year):
    from .services import business_date

    source, source_hash = catalogue()
    entry = next(
        (
            item
            for item in source["institutions"]
            if item["reference"] == institution.reference
            and item["name"] == institution.name
            and item["academic_year"] == year
        ),
        None,
    )
    programmes = db.scalars(
        select(Programme)
        .where(Programme.institution_id == institution.id, Programme.academic_year == year)
        .order_by(Programme.id)
        .execution_options(populate_existing=True)
    ).all()
    matched = [
        programme_snapshot(p)
        for p in programmes
        if entry
        and any(s["name"] == p.name and s["intake"] == p.approved_intake for s in entry["programmes"])
    ]
    live = bool(
        entry
        and date.fromisoformat(entry["valid_from"])
        <= business_date()
        <= date.fromisoformat(entry["valid_until"])
    )
    evidence = (
        {
            "mode": "DEMO_FIXTURE",
            "catalogue_version": source["version"],
            "catalogue_hash": source_hash,
            "institution_reference": institution.reference,
            "institution_name": institution.name,
            "aicte_id": entry["aicte_id"],
            "campus": entry["campus"],
            "academic_year": year,
            "approval_reference": entry["approval_reference"],
            "valid_from": entry["valid_from"],
            "valid_until": entry["valid_until"],
            "programmes": matched,
        }
        if entry
        else None
    )
    fingerprint = digest(
        {
            "catalogue_hash": source_hash,
            "institution_id": institution.id,
            "name": institution.name,
            "reference": institution.reference,
            "academic_year": year,
            "programmes": [programme_snapshot(p) for p in programmes],
        }
    )
    return {
        "evidence": evidence,
        "evidence_digest": fingerprint,
        "can_approve": bool(live and matched),
        "source_live": live,
        "source_programmes": entry["programmes"] if entry else [],
        "programmes": programmes,
    }


def approval_for(db, institution_id, year):
    return db.scalar(
        select(InstitutionApproval)
        .where(
            InstitutionApproval.institution_id == institution_id, InstitutionApproval.academic_year == year
        )
        .execution_options(populate_existing=True)
    )


def effective_status(approval, current):
    from .services import business_date

    if approval is None:
        return "PENDING"
    if approval.status == "SUSPENDED":
        return "SUSPENDED"
    evidence = approval.evidence_snapshot
    if evidence and business_date() > date.fromisoformat(evidence["valid_until"]):
        return "EXPIRED"
    source = current["evidence"]
    if (
        not evidence
        or not source
        or not current["source_live"]
        or evidence["catalogue_hash"] != source["catalogue_hash"]
        or evidence["institution_name"] != source["institution_name"]
        or evidence["institution_reference"] != source["institution_reference"]
    ):
        return "REVIEW_REQUIRED"
    return "APPROVED"


def programme_allowed(approval, programme):
    return bool(
        approval
        and approval.evidence_snapshot
        and programme_snapshot(programme) in approval.evidence_snapshot.get("programmes", [])
    )


def require_institution(db, user, year):
    require_permission(user, Permission.INSTITUTION_WRITE)
    lock_scope(db, user.institution_id)
    institution = db.get(Institution, user.institution_id)
    if institution is None:
        raise DomainError("NOT_FOUND", "Institution not found", 404)
    current = candidate(db, institution, year)
    approval = approval_for(db, institution.id, year)
    if effective_status(approval, current) != "APPROVED":
        raise DomainError(
            "INSTITUTION_APPROVAL_REQUIRED",
            "Admission submissions are blocked for this year. Ask the officer to review Institution approval.",
            403,
        )
    return approval


def require_programmes(approval, programmes):
    if any(not programme_allowed(approval, p) for p in programmes):
        raise DomainError(
            "PROGRAMME_APPROVAL_REQUIRED",
            "A programme or intake differs from its reviewed evidence. Ask the officer to review Institution approval.",
            403,
        )


def view(db, institution, year):
    current = candidate(db, institution, year)
    approval = approval_for(db, institution.id, year)
    status = effective_status(approval, current)
    events = (
        db.scalars(
            select(InstitutionApprovalEvent)
            .where(InstitutionApprovalEvent.approval_id == approval.id)
            .order_by(InstitutionApprovalEvent.version.desc())
            .limit(10)
        ).all()
        if approval
        else []
    )
    return {
        "institution_id": institution.id,
        "institution_name": institution.name,
        "institution_reference": institution.reference,
        "academic_year": year,
        "status": status,
        "version": approval.version if approval else 0,
        "mode": "DEMO_FIXTURE",
        "can_approve": current["can_approve"],
        "evidence_digest": current["evidence_digest"],
        "candidate_evidence": current["evidence"],
        "reviewed_evidence": approval.evidence_snapshot if approval else None,
        "reviewed_at": approval.reviewed_at if approval else None,
        "reviewer": db.get(User, approval.reviewer_id).name if approval else None,
        "programmes": [
            {
                **programme_snapshot(p),
                "source_matches": bool(
                    current["evidence"] and programme_snapshot(p) in current["evidence"]["programmes"]
                ),
                "source_intake": next(
                    (item["intake"] for item in current["source_programmes"] if item["name"] == p.name), None
                ),
                "admissions_enabled": status == "APPROVED" and programme_allowed(approval, p),
            }
            for p in current["programmes"]
        ],
        "events": [
            {
                "version": event.version,
                "status": event.status,
                "reason": event.reason,
                "actor": db.get(User, event.actor_id).name,
                "created_at": event.created_at,
            }
            for event in events
        ],
    }


def decide(db, user, institution_id, data):
    from .services import audit

    require_permission(user, Permission.INSTITUTION_APPROVAL)
    institution = db.get(Institution, institution_id)
    if institution is None:
        raise DomainError("NOT_FOUND", "Institution not found", 404)
    lock_scope(db, institution_id)
    db.scalars(
        select(Programme)
        .where(Programme.institution_id == institution_id)
        .order_by(Programme.id)
        .with_for_update()
    ).all()
    current = candidate(db, institution, data.academic_year)
    approval = approval_for(db, institution_id, data.academic_year)
    if (approval.version if approval else 0) != data.expected_version or current[
        "evidence_digest"
    ] != data.evidence_digest:
        raise DomainError("STALE_VERSION", "Approval evidence changed. Refresh and review again", 409)
    if data.action == "APPROVE_DEMO" and not current["can_approve"]:
        raise DomainError("APPROVAL_EVIDENCE_REQUIRED", "No current matching demo evidence is available", 409)
    if approval is None:
        approval = InstitutionApproval(
            id=uid(), institution_id=institution_id, academic_year=data.academic_year, version=0
        )
        db.add(approval)
    approval.status = "APPROVED" if data.action == "APPROVE_DEMO" else "SUSPENDED"
    approval.version += 1
    approval.evidence_mode = "DEMO_FIXTURE"
    if data.action == "APPROVE_DEMO":
        approval.evidence_snapshot = current["evidence"]
    approval.reviewer_id, approval.reviewed_at = user.id, utcnow()
    db.flush()
    reason = "DEMO_EVIDENCE_REVIEWED" if data.action == "APPROVE_DEMO" else "OFFICER_SUSPENDED"
    db.add(
        InstitutionApprovalEvent(
            approval_id=approval.id,
            actor_id=user.id,
            version=approval.version,
            status=approval.status,
            reason=reason,
            evidence_snapshot=approval.evidence_snapshot,
        )
    )
    audit(
        db,
        user,
        "INSTITUTION_APPROVAL_REVIEWED",
        approval.id,
        {
            "status": approval.status,
            "version": approval.version,
            "mode": "DEMO_FIXTURE",
            "academic_year": data.academic_year,
        },
    )
    db.commit()
    return view(db, institution, data.academic_year)
