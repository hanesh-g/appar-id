"""Generate synthetic CSVs for the documented demo. No real personal data."""
import csv
from pathlib import Path

from app.schemas import HEADERS

root = Path(__file__).resolve().parents[1] / "fixtures"
root.mkdir(exist_ok=True)


def row(number):
    return dict(student_ref=f"STU-{number:03d}", apaar_id=str(900000000000 + number),
        student_name=f"Demo Student {number:03d}", date_of_birth="2005-01-01", programme="Computer Science",
        academic_year="2026-27", admission_date="2026-07-01", start_date="2026-07-15", end_date="",
        status="ENROLLED", seat_type="General", supernumerary="N", nri="N", oci="N", foreign_national="N")


def write(name, rows):
    with (root / name).open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=HEADERS)
        writer.writeheader()
        writer.writerows(rows)


if __name__ == "__main__":
    identity = [row(i) for i in range(1, 7)]
    identity[1]["apaar_id"] = ""
    identity[2]["apaar_id"] = "bad-id"
    identity[3]["apaar_id"] = "111111111111"
    identity[4]["apaar_id"] = "900000000999"
    identity[5]["date_of_birth"] = "2005-02-02"
    write("identity-cases.csv", identity)
    intake = [row(i) for i in range(1, 66)]
    for item in intake[60:]:
        item["apaar_id"] = ""
    write("intake-65.csv", intake)
    write("max-supported.csv", [row(i) for i in range(1, 501)])
    corrected = row(1)
    corrected["seat_type"] = "Updated demo category"
    write("corrections.csv", [corrected, row(2)])
    errors = [row(i) for i in range(80, 83)]
    errors[0]["start_date"] = "not-a-date"
    errors[1]["programme"] = "Unknown Programme"
    errors[2]["student_name"] = ""
    write("structural-errors.csv", errors)
    write("duplicate-keys.csv", [row(90), row(90)])
    print("Generated six synthetic fixture CSV files.")
