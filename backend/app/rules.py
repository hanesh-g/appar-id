import csv
import io
from collections import Counter

from pydantic import ValidationError

from .errors import DomainError
from .registry import MESSAGES, validate_identity
from .schemas import HEADERS, StudentRow

MAX_BYTES = 2 * 1024 * 1024
MAX_ROWS = 500


def issue(code: str, field: str, message: str, severity: str = "ERROR") -> dict:
    return {"code": code, "field": field, "message": message, "severity": severity}


def parse_csv(content: bytes) -> list[dict]:
    if not content or len(content) > MAX_BYTES:
        raise DomainError("FILE_SIZE", "Upload a non-empty CSV of at most 2 MiB", 413 if content else 400)
    try:
        text = content.decode("utf-8-sig")
        if "\x00" in text:
            raise ValueError()
        reader = csv.DictReader(io.StringIO(text, newline=""), strict=True)
        if reader.fieldnames != HEADERS:
            raise DomainError("CSV_HEADER", "Use the provided CSV template with its exact header order")
        rows = []
        for raw in reader:
            if len(rows) >= MAX_ROWS:
                raise DomainError("ROW_LIMIT", "The demo accepts at most 500 rows", 413)
            if None in raw or any(v is None for v in raw.values()):
                raise DomainError("CSV_COLUMNS", "Every row must have the same columns as the header")
            rows.append({key: value.strip() for key, value in raw.items()})
        if not rows:
            raise DomainError("CSV_EMPTY", "Add at least one student row below the header")
        return rows
    except (UnicodeDecodeError, csv.Error, ValueError):
        raise DomainError("CSV_ENCODING", "Upload a valid UTF-8 CSV, not a workbook or binary file") from None


def validate_rows(raw_rows: list[dict], programmes: dict, year: str, unavailable: bool) -> list[dict]:
    keys = Counter((r.get("programme"), r.get("academic_year"), r.get("student_ref")) for r in raw_rows)
    results = []
    for index, raw in enumerate(raw_rows, 1):
        issues = []
        programme = programmes.get(raw.get("programme"))
        try:
            row = StudentRow.model_validate(raw)
            raw = row.model_dump(mode="json")
            raw["end_date"] = raw["end_date"] or ""
        except ValidationError as exc:
            for error in exc.errors(include_input=False, include_url=False):
                field = str(error["loc"][0]) if error["loc"] else "dates"
                message = str(error["msg"]).removeprefix("Value error, ")
                issues.append(
                    issue(
                        "DATE_INVALID" if "date" in field or field == "dates" else "FIELD_INVALID",
                        field,
                        message,
                    )
                )
        if not programme:
            issues.append(
                issue(
                    "PROGRAMME_UNKNOWN",
                    "programme",
                    "Add or select a programme for this institution and year",
                )
            )
        if raw.get("academic_year") != year:
            issues.append(
                issue("YEAR_MISMATCH", "academic_year", "Use the academic year selected for this upload")
            )
        if keys[(raw.get("programme"), raw.get("academic_year"), raw.get("student_ref"))] > 1:
            issues.append(
                issue("DUPLICATE_IN_FILE", "student_ref", "Keep one row per student reference and programme")
            )
        state, reason = "PENDING_CHECK", "STRUCTURAL_ERROR"
        if not issues:
            state, reason = validate_identity(raw, unavailable)
            if state != "VERIFIED":
                issues.append(issue(reason, "apaar_id", MESSAGES[reason], "WARNING"))
        results.append(
            {
                "row_no": index,
                "raw": raw,
                "programme_id": programme.id if programme else None,
                "student_ref": raw.get("student_ref", "")[:100],
                "identity_status": state,
                "identity_reason": reason,
                "issues": issues,
            }
        )
    return results


def safe_csv(rows: list[dict], headers: list[str]) -> str:
    output = io.StringIO(newline="")
    writer = csv.DictWriter(output, fieldnames=headers)
    writer.writeheader()
    for raw in rows:
        safe = {}
        for key in headers:
            value = str(raw.get(key) or "")
            safe[key] = "'" + value if value.lstrip().startswith(("=", "+", "-", "@", "\t", "\r")) else value
        writer.writerow(safe)
    return output.getvalue()
