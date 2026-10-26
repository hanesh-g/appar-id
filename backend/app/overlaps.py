"""Date intersections are review evidence, never automatic fraud findings."""

import hashlib
import json
from itertools import combinations

from sqlalchemy import or_, select

from .db import uid, utcnow
from .errors import DomainError
from .models import Enrolment, Institution, OverlapEvent, OverlapReview, Person, Programme
from .permissions import Permission, require_permission


def evidence(a, b):
    return {
        "records": [
            {
                "id": r.id,
                "version": r.version,
                "start_date": r.start_date.isoformat(),
                "end_date": r.end_date.isoformat() if r.end_date else None,
                "status": r.status,
            }
            for r in (a, b)
        ],
        "convention": "INCLUSIVE_DATES_DEMO_V1",
    }


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def reconcile(db, user, person_ids):
    # Call only while holding the shared person's digest lock, before final audit commit.
    from .services import audit

    for person_id in sorted(set(person_ids)):
        records = db.scalars(
            select(Enrolment)
            .where(Enrolment.person_id == person_id, Enrolment.identity_status == "VERIFIED")
            .order_by(Enrolment.id)
        ).all()
        existing = {
            (r.enrolment_a_id, r.enrolment_b_id): r
            for r in db.scalars(
                select(OverlapReview)
                .where(OverlapReview.person_id == person_id)
                .order_by(OverlapReview.id)
                .with_for_update()
            ).all()
        }
        seen = set()
        for a, b in combinations(records, 2):
            key = (a.id, b.id)
            start = max(a.start_date, b.start_date)
            ends = [r.end_date for r in (a, b) if r.end_date is not None]
            end = min(ends) if ends else None
            if end is not None and start > end:
                continue
            seen.add(key)
            current = evidence(a, b)
            fingerprint = digest(current)
            review = existing.get(key)
            if review and review.evidence_hash == fingerprint and review.status != "NO_LONGER_OVERLAPPING":
                continue
            if review is None:
                review = OverlapReview(
                    id=uid(),
                    person_id=person_id,
                    enrolment_a_id=a.id,
                    enrolment_b_id=b.id,
                    overlap_start=start,
                    overlap_end=end,
                    evidence=current,
                    evidence_hash=fingerprint,
                    status="OPEN",
                    version=1,
                )
                db.add(review)
            else:
                review.overlap_start, review.overlap_end = start, end
                review.evidence, review.evidence_hash = current, fingerprint
                (
                    review.status,
                    review.reviewer_id,
                    review.review_reason,
                    review.policy_reference,
                    review.resolved_at,
                ) = "OPEN", None, None, None, None
                review.version += 1
            db.flush()
            db.add(
                OverlapEvent(
                    review_id=review.id,
                    actor_id=user.id,
                    version=review.version,
                    status=review.status,
                    reason="EVIDENCE_CHANGED" if key in existing else "INTERVAL_DETECTED",
                    evidence=current,
                )
            )
            # Institution-visible audit contains only its own enrolment, never a pair ID or foreign facts.
            own = (
                a
                if a.institution_id == user.institution_id
                else b
                if b.institution_id == user.institution_id
                else None
            )
            if own:
                audit(db, user, "INTERVAL_NOTICE_UPDATED", own.id, {"pending_review": True})
            elif user.role == "officer":
                audit(db, user, "INTERVAL_QUEUE_RECONCILED", review.id, {"status": review.status})
        for key, review in existing.items():
            if key in seen or review.status == "NO_LONGER_OVERLAPPING":
                continue
            review.status, review.resolved_at = "NO_LONGER_OVERLAPPING", utcnow()
            review.version += 1
            db.add(
                OverlapEvent(
                    review_id=review.id,
                    actor_id=user.id,
                    version=review.version,
                    status=review.status,
                    reason="INTERVAL_CLEARED",
                    evidence=review.evidence,
                )
            )
            for record_id in key:
                own = db.get(Enrolment, record_id)
                if own.institution_id == user.institution_id:
                    audit(db, user, "INTERVAL_NOTICE_UPDATED", own.id, {"pending_review": False})
                    break
            else:
                if user.role == "officer":
                    audit(db, user, "INTERVAL_QUEUE_RECONCILED", review.id, {"status": review.status})


def pending_notice(db, enrolment_id):
    return (
        db.scalar(
            select(OverlapReview.id)
            .where(
                or_(
                    OverlapReview.enrolment_a_id == enrolment_id, OverlapReview.enrolment_b_id == enrolment_id
                ),
                OverlapReview.status.in_(["OPEN", "ESCALATED"]),
            )
            .limit(1)
        )
        is not None
    )


def review_out(db, review):
    from .services import business_date

    records = [db.get(Enrolment, review.enrolment_a_id), db.get(Enrolment, review.enrolment_b_id)]
    return {
        "id": review.id,
        "status": review.status,
        "version": review.version,
        "overlap_start": review.overlap_start,
        "overlap_end": review.overlap_end,
        "scheduled": review.overlap_start > business_date(),
        "apaar_masked": "********" + db.get(Person, review.person_id).suffix,
        "review_reason": review.review_reason,
        "policy_reference": review.policy_reference,
        "resolved_at": review.resolved_at,
        "records": [
            {
                "institution": db.get(Institution, r.institution_id).name,
                "programme": db.get(Programme, r.programme_id).name,
                "start_date": r.start_date,
                "end_date": r.end_date,
                "status": r.status,
                "version": r.version,
            }
            for r in records
        ],
    }


def decide(db, user, review_id, data):
    from .services import audit

    require_permission(user, Permission.OVERLAP_REVIEW)
    review = db.scalar(select(OverlapReview).where(OverlapReview.id == review_id).with_for_update())
    if review is None:
        raise DomainError("NOT_FOUND", "Review not found", 404)
    if review.version != data.expected_version:
        raise DomainError("STALE_VERSION", "The interval evidence changed. Review again", 409)
    if review.status == "NO_LONGER_OVERLAPPING":
        raise DomainError("INTERVAL_CLOSED", "These recorded intervals no longer overlap", 409)
    if (review.status, review.review_reason, review.policy_reference) == (
        data.status,
        data.reason,
        data.policy_reference,
    ):
        return review
    review.status, review.review_reason, review.policy_reference = (
        data.status,
        data.reason,
        data.policy_reference,
    )
    review.reviewer_id, review.resolved_at = (
        user.id,
        utcnow() if data.status.startswith("REVIEWED_") else None,
    )
    review.version += 1
    db.add(
        OverlapEvent(
            review_id=review.id,
            actor_id=user.id,
            version=review.version,
            status=review.status,
            reason=data.reason,
            evidence=review.evidence,
        )
    )
    audit(
        db,
        user,
        "INTERVAL_REVIEWED",
        review.id,
        {"status": review.status, "reason": data.reason, "version": review.version},
    )
    db.commit()
    return review
