"""Idempotent seed of synthetic institutions and local accounts. Never resets data."""

import argparse

from sqlalchemy import select
from sqlalchemy.orm import Session

from .config import Settings
from .db import make_engine
from .models import Institution, Programme, User
from .security import password_hash


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
        seed(session, settings.demo_password.get_secret_value())
    engine.dispose()
    print("Synthetic institutions and accounts seeded. Existing accounts/data were preserved.")
    print("Accounts: collegea@example.test, collegeb@example.test, officer@example.test")
