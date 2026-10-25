"""Deterministic synthetic registry. Not an official APAAR service."""

import re
import unicodedata


def normalized_name(value: str) -> str:
    return " ".join(sorted(unicodedata.normalize("NFKC", value).casefold().split()))


def validate_identity(raw: dict, unavailable: bool = False) -> tuple[str, str]:
    value = raw.get("apaar_id", "").replace(" ", "").replace("-", "")
    if not value:
        return "MISSING", "APAAR_MISSING"
    if not re.fullmatch(r"[0-9]{12}", value):
        return "INVALID", "APAAR_INVALID_FORMAT"
    if unavailable:
        return "PENDING_CHECK", "REGISTRY_UNAVAILABLE"
    number = int(value) - 900000000000
    if not 1 <= number <= 1000:
        return "INVALID", "APAAR_NOT_FOUND"
    if number == 999:
        return "INVALID", "APAAR_INACTIVE"
    expected = f"Demo Student {number:03d}"
    if (
        normalized_name(raw["student_name"]) != normalized_name(expected)
        or raw["date_of_birth"] != "2005-01-01"
    ):
        return "PENDING_CHECK", "IDENTITY_MISMATCH"
    return "VERIFIED", "MOCK_MATCH"


MESSAGES = {
    "APAAR_MISSING": "No APAAR ID supplied. Add it later; this admission remains counted.",
    "APAAR_INVALID_FORMAT": "Check the ID format. The demo assumes exactly 12 digits.",
    "APAAR_NOT_FOUND": "ID not found in the simulated registry. Check the submitted ID.",
    "APAAR_INACTIVE": "The simulated registry marks this ID inactive. Review the identity.",
    "REGISTRY_UNAVAILABLE": "Simulated registry unavailable. Retry the identity check after recovery.",
    "IDENTITY_MISMATCH": "Name or date of birth differs from the simulated registry. Review both fields.",
}
