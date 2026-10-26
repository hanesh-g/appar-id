"""Idempotent seed of synthetic institutions and local accounts. Never resets data."""

import argparse

from sqlalchemy import select
from sqlalchemy.orm import Session

from .config import Settings
from .db import make_engine
from .models import Institution, Programme, User, VerifierOrganisation
from .security import Crypto, password_hash


def seed(db: Session, password: str):
    for reference, name in [
        ("DEMO-A", "Deccan Institute of Technology"),
        ("DEMO-B", "Riverdale Technical College"),
    ]:
        institution = db.scalar(select(Institution).where(Institution.reference == reference))
        if institution is None:
            institution = Institution(name=name, reference=reference)
            db.add(institution)
            db.flush()
        for programme in ["Computer Science", "Electronics"]:
            exists = db.scalar(
                select(Programme).where(
                    Programme.institution_id == institution.id,
                    Programme.name == programme,
                    Programme.academic_year == "2026-27",
                )
            )
            if not exists:
                db.add(
                    Programme(
                        institution_id=institution.id,
                        name=programme,
                        academic_year="2026-27",
                        approved_intake=60,
                    )
                )
        email = "collegea@example.test" if reference == "DEMO-A" else "collegeb@example.test"
        if not db.scalar(select(User).where(User.email == email)):
            db.add(
                User(
                    email=email,
                    name=f"{reference} administrator",
                    role="institution_admin",
                    institution_id=institution.id,
                    password_hash=password_hash.hash(password),
                )
            )
    if not db.scalar(select(User).where(User.email == "officer@example.test")):
        db.add(
            User(
                email="officer@example.test",
                name="Demo officer",
                role="officer",
                password_hash=password_hash.hash(password),
            )
        )
    db.commit()


def seed_verification(db: Session, password: str, crypto: Crypto):
    from .locking import lock_identity_keys
    from .services import audit, link_person

    officer = db.scalar(select(User).where(User.role == "officer", User.active.is_(True)))
    if officer is None:
        raise ValueError("Seed the active demo officer before verification accounts")
    identities = [
        {
            "apaar_id": f"{900000000000 + index}",
            "student_name": f"Demo Student {index:03d}",
            "date_of_birth": "2005-01-01",
        }
        for index in (1, 2)
    ]
    lock_identity_keys(db, crypto, identities)
    people = {
        raw["apaar_id"]: link_person(db, raw, crypto)
        for raw in sorted(identities, key=lambda raw: crypto.digest(raw["apaar_id"]))
    }
    added = 0
    for index in (1, 2):
        org = db.scalar(
            select(VerifierOrganisation).where(VerifierOrganisation.reference == f"DEMO-VERIFIER-{index}")
        )
        if org is None:
            org = VerifierOrganisation(
                name="Demo admissions verifier" if index == 1 else "Demo employer verifier",
                reference=f"DEMO-VERIFIER-{index}",
                approved=True,
                active=True,
            )
            db.add(org)
            db.flush()
        for role, person_id, org_id in [
            ("student", people[f"{900000000000 + index}"], None),
            ("verifier", None, org.id),
        ]:
            email = f"{role}{index}@example.test"
            account = db.scalar(select(User).where(User.email == email))
            if account is None:
                db.add(
                    User(
                        email=email,
                        name=f"Synthetic {role} {index}",
                        role=role,
                        person_id=person_id,
                        verifier_org_id=org_id,
                        password_hash=password_hash.hash(password),
                    )
                )
                added += 1
            elif (account.role, account.person_id, account.verifier_org_id) != (role, person_id, org_id):
                raise ValueError("Existing demo account binding differs; automatic relinking refused")
    if added:
        audit(db, officer, "DEMO_ACCOUNTS_PROVISIONED", officer.id, {"accounts_added": added})
    db.commit()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--demo", action="store_true", required=True)
    parser.parse_args()
    settings = Settings()
    if settings.app_env not in {"local", "demo"}:
        raise SystemExit("Seed is permitted only in explicitly local/demo environments")
    if settings.demo_password is None or len(settings.demo_password.get_secret_value()) < 12:
        raise SystemExit(
            "Choose a DEMO_PASSWORD of at least 12 characters in secure local/environment settings"
        )
    engine = make_engine(settings.database_url.get_secret_value())
    with Session(engine) as session:
        session.info["audit_settings"] = settings
        seed(session, settings.demo_password.get_secret_value())
        if settings.consent_enabled:
            seed_verification(session, settings.demo_password.get_secret_value(), Crypto(settings))
    engine.dispose()
    print("Synthetic institutions and accounts seeded. Existing accounts/data were preserved.")
    print("Accounts: collegea@example.test, collegeb@example.test, officer@example.test")
    if settings.consent_enabled:
        print(
            "Adult synthetic accounts: student1@example.test, student2@example.test, verifier1@example.test, verifier2@example.test"
        )
