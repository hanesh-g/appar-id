"""Live consent checks over narrowly addressed records. No raw tokens are stored."""

import base64
import hashlib
import hmac
import json
import secrets
from datetime import timedelta

from sqlalchemy import func, select, text

from .db import uid, utcnow
from .errors import DomainError
from .locking import lock_identity_keys
from .models import (
    ConsentGrant,
    Enrolment,
    Institution,
    Person,
    Programme,
    RecordRequestHandle,
    User,
    VerificationAccess,
    VerificationRequest,
    VerifierOrganisation,
)
from .services import audit
from .verification_contracts import ALLOWED_FIELDS


def token_digest(settings, value, namespace):
    if settings.grant_token_key is None:
        raise DomainError("VERIFICATION_UNAVAILABLE", "Verification is unavailable", 503)
    key = base64.b64decode(settings.grant_token_key.get_secret_value())
    return hmac.new(key, (namespace + ":" + value).encode(), hashlib.sha256).hexdigest()


def unavailable():
    raise DomainError("VERIFICATION_UNAVAILABLE", "Verification is unavailable", 404)


def active_verifier(db, user_id, org_id):
    return (
        db.scalar(
            select(User.id)
            .join(VerifierOrganisation, VerifierOrganisation.id == User.verifier_org_id)
            .where(
                User.id == user_id,
                User.role == "verifier",
                User.active.is_(True),
                User.verifier_org_id == org_id,
                VerifierOrganisation.active.is_(True),
                VerifierOrganisation.approved.is_(True),
            )
        )
        is not None
    )


def record(db, person_id, enrolment_id, *, lock=False):
    stmt = select(Enrolment).where(
        Enrolment.id == enrolment_id,
        Enrolment.person_id == person_id,
        Enrolment.identity_status == "VERIFIED",
    )
    current = db.scalar(stmt)
    if current is None:
        return None
    if lock:
        db.scalar(select(Programme.id).where(Programme.id == current.programme_id).with_for_update(read=True))
        lock_identity_keys(db, None, old_person_ids=[person_id])
        current = db.scalar(stmt.with_for_update(read=True).execution_options(populate_existing=True))
    return current


def fields(db, enrolment, approved):
    if not set(approved) <= ALLOWED_FIELDS:
        unavailable()
    values = {
        "programme": db.get(Programme, enrolment.programme_id).name,
        "institution_name": db.get(Institution, enrolment.institution_id).name,
        "academic_year": enrolment.academic_year,
        "admission_status": enrolment.status,
        "start_date": enrolment.start_date.isoformat(),
        "masked_apaar": "********" + db.get(Person, enrolment.person_id).suffix,
    }
    return {key: values[key] for key in approved}


def own_record_out(db, enrolment):
    return {
        "id": enrolment.id,
        "version": enrolment.version,
        "fields": fields(db, enrolment, sorted(ALLOWED_FIELDS)),
    }


def create_handle(db, user, enrolment_id, data, settings):
    enrolment = record(db, user.person_id, enrolment_id, lock=True)
    if enrolment is None:
        raise DomainError("NOT_FOUND", "Record not found", 404)
    if enrolment.version != data.expected_version:
        raise DomainError("STALE_VERSION", "The record changed. Refresh before sharing a request code", 409)
    raw = secrets.token_urlsafe(32)
    handle = RecordRequestHandle(
        id=uid(),
        student_person_id=user.person_id,
        enrolment_id=enrolment.id,
        token_digest=token_digest(settings, raw, "request-handle-v1"),
        token_key_id=settings.grant_key_id,
        expires_at=utcnow() + timedelta(minutes=15),
    )
    db.add(handle)
    audit(db, user, "REQUEST_HANDLE_CREATED", handle.id, {"record_version": enrolment.version})
    db.commit()
    return {"handle": raw, "expires_at": handle.expires_at}


def create_request(db, user, data, key, settings):
    # This operation-header lock serialises per-verifier rate/idempotency checks
    # without row-locking the actor, which other transactions reference via FKs.
    actor_digest = token_digest(settings, user.id, "request-rate-v1")
    db.execute(
        text("SELECT pg_advisory_xact_lock(:key)"),
        {"key": int.from_bytes(bytes.fromhex(actor_digest)[:8], "big", signed=True)},
    )
    digest = token_digest(settings, data.handle.get_secret_value(), "request-handle-v1")
    payload_hash = hashlib.sha256(
        json.dumps([digest, data.purpose, sorted(data.requested_fields)], separators=(",", ":")).encode()
    ).hexdigest()
    previous = db.scalar(
        select(VerificationRequest).where(
            VerificationRequest.verifier_user_id == user.id, VerificationRequest.idempotency_key == key
        )
    )
    if previous:
        if previous.payload_hash != payload_hash:
            raise DomainError("IDEMPOTENCY_CONFLICT", "Use a new request key for changed input", 409)
        return {"request_id": previous.id, "status": "SUBMITTED"}
    recent = db.scalar(
        select(func.count())
        .select_from(VerificationRequest)
        .where(
            VerificationRequest.verifier_user_id == user.id,
            VerificationRequest.created_at > utcnow() - timedelta(minutes=1),
        )
    )
    if recent >= 10:
        raise DomainError("RATE_LIMIT", "Wait before submitting another request", 429)
    handle = db.scalar(
        select(RecordRequestHandle).where(
            RecordRequestHandle.token_digest == digest,
            RecordRequestHandle.token_key_id == settings.grant_key_id,
        )
    )
    bound = None
    if handle and handle.expires_at > utcnow() and handle.consumed_at is None:
        bound = record(db, handle.student_person_id, handle.enrolment_id, lock=True)
        handle = db.scalar(
            select(RecordRequestHandle)
            .where(RecordRequestHandle.id == handle.id)
            .with_for_update()
            .execution_options(populate_existing=True)
        )
        if handle.expires_at <= utcnow() or handle.consumed_at is not None:
            bound = None
    if not active_verifier(db, user.id, user.verifier_org_id):
        unavailable()
    request = VerificationRequest(
        id=uid(),
        student_person_id=handle.student_person_id if bound else None,
        enrolment_id=bound.id if bound else None,
        handle_id=handle.id if bound else None,
        verifier_user_id=user.id,
        verifier_org_id=user.verifier_org_id,
        purpose=data.purpose,
        requested_fields=sorted(data.requested_fields),
        idempotency_key=key,
        payload_hash=payload_hash,
        status="PENDING",
        version=1,
        expires_at=utcnow() + timedelta(hours=24),
    )
    if bound:
        handle.consumed_at = utcnow()
    db.add(request)
    audit(
        db,
        user,
        "VERIFICATION_REQUESTED",
        request.id,
        {"purpose": data.purpose, "field_count": len(data.requested_fields)},
    )
    db.commit()
    # Invalid/expired/used handles produce the same acknowledgement and own
    # pending submission, with no linked student inbox. No identity lookup oracle.
    return {"request_id": request.id, "status": "SUBMITTED"}


def request_out(request):
    return {
        "id": request.id,
        "status": "EXPIRED"
        if request.status == "PENDING" and request.expires_at <= utcnow()
        else request.status,
        "version": request.version,
        "purpose": request.purpose,
        "requested_fields": request.requested_fields,
        "created_at": request.created_at,
        "expires_at": request.expires_at,
    }


def student_request(db, user, request_id, *, lock=False):
    stmt = select(VerificationRequest).where(
        VerificationRequest.id == request_id, VerificationRequest.student_person_id == user.person_id
    )
    result = db.scalar(stmt.with_for_update().execution_options(populate_existing=True) if lock else stmt)
    if result is None:
        raise DomainError("NOT_FOUND", "Request not found", 404)
    return result


def grant_out(db, grant):
    request = db.get(VerificationRequest, grant.request_id)
    current = record(db, grant.student_person_id, grant.enrolment_id)
    latest = db.scalar(
        select(ConsentGrant.id)
        .where(ConsentGrant.request_id == grant.request_id)
        .order_by(ConsentGrant.created_at.desc(), ConsentGrant.id.desc())
        .limit(1)
    )
    return {
        "id": grant.id,
        "request_id": grant.request_id,
        "version": grant.version,
        "purpose": grant.purpose,
        "allowed_fields": grant.allowed_fields,
        "record_version": grant.record_version,
        "expires_at": grant.expires_at,
        "revoked_at": grant.revoked_at,
        "verifier_organisation": db.get(VerifierOrganisation, grant.verifier_org_id).name,
        "can_reissue": bool(
            current
            and current.version == grant.record_version
            and request.expires_at > utcnow()
            and latest == grant.id
        ),
    }


def mint(db, request, enrolment, approved, minutes, settings):
    if not set(approved) <= set(request.requested_fields) or not set(approved) <= ALLOWED_FIELDS:
        raise DomainError("CONSENT_FIELDS", "Approve only fields included in this request", 422)
    if not active_verifier(db, request.verifier_user_id, request.verifier_org_id):
        raise DomainError("REQUEST_UNAVAILABLE", "The verifier account is unavailable", 409)
    now = utcnow()
    raw = secrets.token_urlsafe(32)
    grant = ConsentGrant(
        id=uid(),
        request_id=request.id,
        student_person_id=request.student_person_id,
        enrolment_id=enrolment.id,
        record_version=enrolment.version,
        verifier_user_id=request.verifier_user_id,
        verifier_org_id=request.verifier_org_id,
        purpose=request.purpose,
        allowed_fields=sorted(approved),
        token_digest=token_digest(settings, raw, "verification-grant-v1"),
        token_key_id=settings.grant_key_id,
        version=1,
        created_at=now,
        expires_at=min(now + timedelta(minutes=minutes), request.expires_at),
    )
    db.add(grant)
    return grant, raw


def approve(db, user, request_id, data, settings):
    initial = student_request(db, user, request_id)
    enrolment = record(db, user.person_id, initial.enrolment_id, lock=True)
    if enrolment is None:
        raise DomainError("REQUEST_UNAVAILABLE", "The linked record needs institution review", 409)
    request = student_request(db, user, request_id, lock=True)
    if request.status == "APPROVED":
        prior = db.scalar(
            select(ConsentGrant)
            .where(ConsentGrant.request_id == request.id)
            .order_by(ConsentGrant.created_at.desc())
            .limit(1)
        )
        return {"grant": grant_out(db, prior), "newly_issued": False}
    if request.version != data.expected_version:
        raise DomainError("STALE_VERSION", "The request changed. Refresh before approving", 409)
    if request.status != "PENDING" or request.expires_at <= utcnow():
        raise DomainError("REQUEST_UNAVAILABLE", "This request is no longer pending", 409)
    if enrolment.version != data.expected_record_version:
        raise DomainError(
            "STALE_VERSION", "The record changed. Review the current fields before approving", 409
        )
    grant, raw = mint(db, request, enrolment, data.allowed_fields, data.expires_in_minutes, settings)
    request.status, request.version = "APPROVED", request.version + 1
    audit(
        db,
        user,
        "CONSENT_APPROVED",
        grant.id,
        {"purpose": request.purpose, "allowed_fields": grant.allowed_fields},
    )
    db.commit()
    return {"grant": grant_out(db, grant), "token": raw, "newly_issued": True}


def deny(db, user, request_id, expected_version):
    request = student_request(db, user, request_id, lock=True)
    if request.status == "DENIED":
        return request_out(request)
    if request.status != "PENDING" or request.version != expected_version or request.expires_at <= utcnow():
        raise DomainError("STALE_VERSION", "The request changed or expired. Refresh before acting", 409)
    request.status, request.version = "DENIED", request.version + 1
    audit(db, user, "CONSENT_DENIED", request.id, {"purpose": request.purpose})
    db.commit()
    return request_out(request)


def own_grant(db, user, grant_id, *, lock=False):
    stmt = select(ConsentGrant).where(
        ConsentGrant.id == grant_id, ConsentGrant.student_person_id == user.person_id
    )
    result = db.scalar(stmt.with_for_update().execution_options(populate_existing=True) if lock else stmt)
    if result is None:
        raise DomainError("NOT_FOUND", "Grant not found", 404)
    return result


def revoke(db, user, grant_id, expected_version):
    initial = own_grant(db, user, grant_id)
    student_request(db, user, initial.request_id, lock=True)
    grant = own_grant(db, user, grant_id, lock=True)
    if grant.revoked_at is None:
        if grant.version != expected_version:
            raise DomainError("STALE_VERSION", "The grant changed. Refresh before revoking", 409)
        grant.revoked_at, grant.version = utcnow(), grant.version + 1
        audit(db, user, "CONSENT_REVOKED", grant.id, {"purpose": grant.purpose})
        db.commit()
    return grant_out(db, grant)


def reissue(db, user, grant_id, expected_version, settings):
    initial = own_grant(db, user, grant_id)
    enrolment = record(db, user.person_id, initial.enrolment_id, lock=True)
    if enrolment is None or enrolment.version != initial.record_version:
        raise DomainError(
            "RENEW_CONSENT", "The record changed. Create a new request and review consent again", 409
        )
    request = student_request(db, user, initial.request_id, lock=True)
    grant = own_grant(db, user, grant_id, lock=True)
    latest = db.scalar(
        select(ConsentGrant.id)
        .where(ConsentGrant.request_id == request.id)
        .order_by(ConsentGrant.created_at.desc(), ConsentGrant.id.desc())
        .limit(1)
    )
    if grant.version != expected_version or request.expires_at <= utcnow() or latest != grant.id:
        raise DomainError(
            "STALE_VERSION", "The grant or request changed. Refresh before replacing the link", 409
        )
    grant.revoked_at, grant.version = grant.revoked_at or utcnow(), grant.version + 1
    replacement, raw = mint(db, request, enrolment, grant.allowed_fields, 15, settings)
    request.version += 1
    audit(
        db,
        user,
        "CONSENT_REISSUED",
        replacement.id,
        {"purpose": grant.purpose, "allowed_fields": grant.allowed_fields},
    )
    db.commit()
    return {"grant": grant_out(db, replacement), "token": raw, "newly_issued": True}


def resolve(db, user, raw, settings):
    digest = token_digest(settings, raw, "verification-grant-v1")
    initial = db.scalar(
        select(ConsentGrant).where(
            ConsentGrant.token_digest == digest,
            ConsentGrant.token_key_id == settings.grant_key_id,
            ConsentGrant.verifier_user_id == user.id,
            ConsentGrant.verifier_org_id == user.verifier_org_id,
        )
    )
    if initial is None:
        unavailable()
    enrolment = record(db, initial.student_person_id, initial.enrolment_id, lock=True)
    if enrolment is None:
        unavailable()
    db.scalar(
        select(VerificationRequest).where(VerificationRequest.id == initial.request_id).with_for_update()
    )
    grant = db.scalar(
        select(ConsentGrant)
        .where(ConsentGrant.id == initial.id)
        .with_for_update()
        .execution_options(populate_existing=True)
    )
    student_active = (
        db.scalar(
            select(User.id).where(
                User.role == "student", User.person_id == grant.student_person_id, User.active.is_(True)
            )
        )
        is not None
    )
    if (
        grant.revoked_at is not None
        or grant.expires_at <= utcnow()
        or grant.record_version != enrolment.version
        or not student_active
        or not active_verifier(db, user.id, user.verifier_org_id)
    ):
        unavailable()
    values = fields(db, enrolment, grant.allowed_fields)
    db.add(
        VerificationAccess(
            id=uid(),
            grant_id=grant.id,
            student_person_id=grant.student_person_id,
            verifier_user_id=user.id,
            disclosed_fields=list(grant.allowed_fields),
        )
    )
    audit(
        db,
        user,
        "VERIFICATION_ACCESSED",
        grant.id,
        {"purpose": grant.purpose, "disclosed_fields": grant.allowed_fields},
    )
    db.commit()  # Failed access auditing must never return a successful disclosure.
    return {"fields": values, "valid_until": grant.expires_at, "source": "SYNTHETIC_DEMO"}
