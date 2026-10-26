"""Retained, hash-checked rule explanations. All current rules are demo rules."""

import hashlib
import json

from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from .errors import DomainError
from .models import RulePack
from .registry import MESSAGES

CURRENT_RULE_SET = "demo-core-v1"
VALIDATOR_VERSION = "core-v1"
SOURCE = "https://github.com/hanesh-g/appar-id/blob/3fec5024b83413e7130bd0632bbbb581ef66d7dc/backend/app/"

# Stable codes are retained; a new policy must create a new pack, not edit an old one.
_STRUCTURAL = {
    "FIELD_INVALID": (
        "A required field is missing or has an unsupported value.",
        "Use the CSV template and correct the indicated field.",
    ),
    "DATE_INVALID": (
        "Dates are missing, invalid, or inconsistent.",
        "Check YYYY-MM-DD dates and the admission, start, end, and status order.",
    ),
    "PROGRAMME_UNKNOWN": (
        "The programme is not configured for this institution and year.",
        "Select an existing programme or add it before uploading.",
    ),
    "YEAR_MISMATCH": (
        "A row uses a different academic year from this upload.",
        "Use the selected academic year or start a separate upload.",
    ),
    "DUPLICATE_IN_FILE": (
        "Two rows use the same programme, year, and student reference.",
        "Keep one intended row for that enrolment key.",
    ),
    "IDENTITY_REASSIGNMENT": (
        "An existing verified person cannot be replaced automatically.",
        "Keep the verified identity and request a separate identity-link review.",
    ),
    "DUPLICATE_IDENTITY": (
        "One verified person occurs under conflicting references in the same programme/year.",
        "Review local references; do not merge records using a name match.",
    ),
}


def manifest(rule_set_id: str = CURRENT_RULE_SET) -> dict:
    rules = {}
    for code in sorted(set(_STRUCTURAL) | set(MESSAGES) | {"IDENTITY_CONFLICT"}):
        structural = code in _STRUCTURAL
        message, action = _STRUCTURAL.get(
            code,
            (
                MESSAGES.get(code, "A recovered identity conflicts with an existing enrolment."),
                MESSAGES.get(code, "Review the existing person/programme link before retrying."),
            ),
        )
        rules[code] = {
            "issue_code": code,
            "severity": "ERROR" if structural else "WARNING",
            "explanation": message,
            "steps": [
                action,
                "Revalidate and review the result before saving. Registry results are simulated.",
            ],
            "owner_types": ["COLLEGE_STAFF", "STUDENT_ACTION", "UPSTREAM_AUTHORITY"]
            if code == "IDENTITY_MISMATCH"
            else ["COLLEGE_STAFF"],
            "authority_label": "Synthetic demo validation rule",
            "source_url": SOURCE
            + (
                "registry.py"
                if code in MESSAGES
                else "rules.py"
                if code not in {"IDENTITY_REASSIGNMENT", "DUPLICATE_IDENTITY", "IDENTITY_CONFLICT"}
                else "services.py"
            ),
            "applicability": "This synthetic admission demo only; not an official identity or quota ruling.",
            "effective_date": None,
            "reviewed_date": None,
            "review_status": "DEMO_ASSUMPTION",
        }
    return {"rule_set_id": rule_set_id, "validator_version": VALIDATOR_VERSION, "rules": rules}


def content_hash(content: dict) -> str:
    return hashlib.sha256(
        json.dumps(content, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    ).hexdigest()


def ensure_current(db: Session) -> str:
    content = manifest()
    db.execute(
        insert(RulePack)
        .values(
            id=CURRENT_RULE_SET,
            validator_version=VALIDATOR_VERSION,
            content=content,
            content_hash=content_hash(content),
        )
        .on_conflict_do_nothing(index_elements=[RulePack.id])
    )
    read_pack(db, CURRENT_RULE_SET)
    return CURRENT_RULE_SET


def read_pack(db: Session, rule_set_id: str | None = None) -> dict:
    target = rule_set_id or CURRENT_RULE_SET
    pack = db.get(RulePack, target)
    if pack is None:
        if target == CURRENT_RULE_SET:
            return manifest()  # Read-only help also works before the first upload.
        raise DomainError("RULESET_NOT_FOUND", "Rule version not found", 404)
    if (
        content_hash(pack.content) != pack.content_hash
        or pack.content.get("rule_set_id") != pack.id
        or pack.content.get("validator_version") != pack.validator_version
    ):
        raise DomainError("RULESET_INTEGRITY", "Rule snapshot integrity check failed", 503)
    return pack.content


def require_executable(db: Session, rule_set_id: str) -> None:
    content = read_pack(db, rule_set_id)
    if content.get("validator_version") != VALIDATOR_VERSION:
        raise DomainError(
            "RULESET_UNAVAILABLE", "This rule version cannot be executed. Upload again for a new review", 409
        )
