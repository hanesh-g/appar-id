"""Transactional HMAC chain; the head is locked only after business writes flush."""

import base64
import copy
import hashlib
import hmac
import json
from datetime import UTC

from sqlalchemy import event, func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from .config import Settings
from .context import request_id
from .db import uid, utcnow
from .errors import DomainError
from .models import Audit, AuditChainHead

ZERO = "0" * 64
VERSION = "hmac-json-v1"


def encoded(value):
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False
    ).encode()


def base_payload(item):
    return {
        "id": item.id,
        "actor_id": item.actor_id,
        "institution_id": item.institution_id,
        "action": item.action,
        "entity_id": item.entity_id,
        "request_id": item.request_id,
        "created_at": item.created_at.astimezone(UTC).isoformat(timespec="microseconds"),
        "details": item.details,
    }


def signed_hash(item, head, key):
    payload = {
        **base_payload(item),
        "chain_version": item.chain_version,
        "key_id": item.key_id,
        "sequence_no": item.sequence_no,
        "prev_hash": item.prev_hash,
        "epoch": head.epoch,
        "baseline_count": head.baseline_count,
        "baseline_hash": head.baseline_hash,
    }
    return hmac.new(key, encoded(payload), hashlib.sha256).hexdigest()


def baseline(db, excluded=()):
    statement = select(Audit).where(Audit.event_hash.is_(None))
    if excluded:
        statement = statement.where(Audit.id.not_in(excluded))
    stream = db.scalars(statement.order_by(Audit.created_at, Audit.id).execution_options(yield_per=500))
    digest = hashlib.sha256()
    count = 0
    for item in stream:
        value = encoded(base_payload(item))
        digest.update(len(value).to_bytes(8, "big"))
        digest.update(value)
        count += 1
    return count, digest.hexdigest()


def enqueue(db, user, action, entity_id, details=None):
    item = Audit(
        id=uid(),
        actor_id=user.id,
        institution_id=user.institution_id,
        action=action,
        entity_id=str(entity_id),
        details=copy.deepcopy(details or {}),
        request_id=request_id.get(),
        created_at=utcnow(),
    )
    db.add(item)
    db.info.setdefault("pending_audit", []).append(item)


def finalize(db):
    pending = db.info.get("pending_audit", [])
    if not pending:
        return
    settings = db.info.get("audit_settings") or Settings()
    db.flush()  # Acquire/finish all business and FK locks before the chain head.
    if not settings.audit_chain_enabled:
        head = db.get(AuditChainHead, 1)
        if head and head.sequence_no:
            raise DomainError(
                "AUDIT_CONFIGURATION",
                "This database requires its retained audit key and enabled integrity setting",
                503,
            )
        db.info.pop("pending_audit", None)
        return
    if settings.audit_hmac_key is None:
        raise DomainError("AUDIT_CONFIGURATION", "Audit integrity is unavailable", 503)
    key = base64.b64decode(settings.audit_hmac_key.get_secret_value())
    head = db.scalar(select(AuditChainHead).where(AuditChainHead.id == 1).with_for_update())
    if head is None:
        if db.scalar(select(Audit.id).where(Audit.event_hash.is_not(None)).limit(1)):
            raise DomainError(
                "AUDIT_HEAD_MISSING", "Audit head is missing; automatic chain reset refused", 503
            )
        db.execute(
            insert(AuditChainHead)
            .values(id=1, epoch=uid(), sequence_no=0, last_hash=ZERO, baseline_count=0, baseline_hash=ZERO)
            .on_conflict_do_nothing(index_elements=[AuditChainHead.id])
        )
        head = db.scalar(select(AuditChainHead).where(AuditChainHead.id == 1).with_for_update())
    if head.sequence_no == 0:
        if head.last_hash != ZERO or db.scalar(
            select(Audit.id).where(Audit.event_hash.is_not(None)).limit(1)
        ):
            raise DomainError("AUDIT_HEAD_INVALID", "Audit head cannot restart an existing chain", 503)
        head.baseline_count, head.baseline_hash = baseline(db, [item.id for item in pending])
        head.baseline_at = utcnow()
    else:
        last = db.scalar(select(Audit).where(Audit.sequence_no == head.sequence_no))
        if (
            last is None
            or last.key_id != settings.audit_key_id
            or last.event_hash != head.last_hash
            or not hmac.compare_digest(signed_hash(last, head, key), last.event_hash)
        ):
            raise DomainError("AUDIT_INTEGRITY", "Audit tail or key does not match; mutation refused", 503)
    for item in pending:
        item.sequence_no = head.sequence_no + 1
        item.prev_hash = head.last_hash
        item.chain_version, item.key_id = VERSION, settings.audit_key_id
        item.event_hash = signed_hash(item, head, key)
        head.sequence_no, head.last_hash = item.sequence_no, item.event_hash
    db.info.pop("pending_audit", None)


def clear_pending(db, *args):
    db.info.pop("pending_audit", None)


# Session-local queues keep all existing transaction boundaries, including inline
# upload + commit + case changes. Direct SQL tampering is never silently re-signed.
event.listen(Session, "before_commit", finalize)
event.listen(Session, "after_soft_rollback", clear_pending)


def verify(db, settings):
    if not settings.audit_chain_enabled or settings.audit_hmac_key is None:
        raise DomainError("AUDIT_DISABLED", "Audit integrity has not been enabled for this environment", 409)
    head = db.get(AuditChainHead, 1)
    if head is None:
        raise DomainError("AUDIT_NOT_INITIALIZED", "Audit integrity has no initialized head", 503)
    result = {
        "verified": False,
        "checked_events": 0,
        "through_sequence": head.sequence_no,
        "last_event_hash": head.last_hash,
        "legacy_events": head.baseline_count,
        "first_broken_sequence": None,
        "reason": "",
        "scope": "New events and the legacy snapshot as seen at activation; not original legacy authenticity or external rollback protection.",
    }
    if head.sequence_no == 0:
        if head.last_hash != ZERO or db.scalar(
            select(Audit.id).where(Audit.event_hash.is_not(None)).limit(1)
        ):
            result.update(reason="HEAD_MISMATCH", first_broken_sequence=1)
            return result
        result.update(
            verified=True,
            reason="NO_CHAINED_EVENTS",
            legacy_events=db.scalar(select(func.count()).select_from(Audit)),
        )
        return result
    legacy_count, legacy_hash = baseline(db)
    if (legacy_count, legacy_hash) != (head.baseline_count, head.baseline_hash):
        result.update(reason="BASELINE_MISMATCH", first_broken_sequence=0)
        return result
    if head.sequence_no > 100000:
        raise DomainError(
            "AUDIT_CAPACITY", "This synchronous verifier supports at most 100000 chained events", 503
        )
    key = base64.b64decode(settings.audit_hmac_key.get_secret_value())
    previous = ZERO
    expected = 1
    for item in db.scalars(
        select(Audit)
        .where(Audit.sequence_no.is_not(None))
        .order_by(Audit.sequence_no)
        .execution_options(yield_per=500)
    ):
        if item.sequence_no != expected or item.prev_hash != previous:
            result.update(reason="SEQUENCE_OR_LINK_MISMATCH", first_broken_sequence=expected)
            return result
        if item.key_id != settings.audit_key_id or item.chain_version != VERSION:
            result.update(reason="UNSUPPORTED_KEY_OR_VERSION", first_broken_sequence=expected)
            return result
        if not hmac.compare_digest(signed_hash(item, head, key), item.event_hash):
            result.update(reason="EVENT_HASH_MISMATCH", first_broken_sequence=expected)
            return result
        previous, expected = item.event_hash, expected + 1
        result["checked_events"] += 1
    if expected - 1 != head.sequence_no or previous != head.last_hash:
        result.update(reason="HEAD_MISMATCH", first_broken_sequence=expected)
        return result
    if db.scalar(select(func.count()).select_from(Audit)) != legacy_count + result["checked_events"]:
        result.update(reason="UNCLASSIFIED_EVENT")
        return result
    result.update(verified=True, reason="VERIFIED")
    return result
