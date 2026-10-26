import csv
import io

from conftest import commit, login


def test_category_dimensions_are_scoped_and_do_not_double_count(client, headers, fixtures_path):
    reader = csv.DictReader(io.StringIO((fixtures_path / "intake-65.csv").read_text()))
    rows = [next(reader) for _ in range(6)]
    for row in rows:
        for flag in ("supernumerary", "nri", "oci", "foreign_national"):
            row[flag] = "N"
    rows[0]["nri"] = "Y"
    rows[1].update(supernumerary="Y", nri="Y", oci="Y", foreign_national="Y")
    rows[2]["supernumerary"] = "Y"
    rows[3].update(status="WITHDRAWN", end_date="2026-09-01", foreign_national="Y")
    content = io.StringIO()
    writer = csv.DictWriter(content, fieldnames=reader.fieldnames)
    writer.writeheader()
    writer.writerows(rows)
    batch = client.post(
        "/api/v1/batches",
        headers={**headers, "Idempotency-Key": "categories"},
        data={"academic_year": "2026-27"},
        files={"file": ("categories.csv", content.getvalue(), "text/csv")},
    ).json()
    assert commit(client, headers, batch["id"]).status_code == 200
    dashboard = client.get("/api/v1/dashboard", headers=headers).json()
    assert dashboard["active"] == 5
    assert dashboard["categories"] == {
        "base_count": 3,
        "supernumerary_count": 2,
        "unclassified_count": 0,
        "nri_count": 2,
        "oci_count": 1,
        "foreign_national_count": 1,
    }
    other = login(client, "collegeb@example.test")
    assert all(v == 0 for v in client.get("/api/v1/dashboard", headers=other).json()["categories"].values())
    officer = login(client, "officer@example.test")
    assert client.get("/api/v1/dashboard", headers=officer).json()["categories"] == dashboard["categories"]
