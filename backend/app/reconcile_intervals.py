"""Explicit, bounded demo backfill. Never runs as a hidden server-start task."""

import argparse

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from .config import Settings
from .db import make_engine
from .errors import DomainError
from .locking import lock_identity_keys
from .models import Enrolment, OverlapReview, Person, Programme, User
from .overlaps import reconcile
from .permissions import Permission, require_permission


def reconcile_existing(db, user):
    require_permission(user, Permission.OVERLAP_REVIEW)
    db.scalars(select(Programme.id).order_by(Programme.id).with_for_update()).all()
    person_ids = db.scalars(select(Person.id).order_by(Person.id).limit(501)).all()
    if len(person_ids) > 500:
        raise DomainError("RECONCILE_LIMIT", "This explicit demo backfill supports at most 500 people", 409)
    lock_identity_keys(db, None, old_person_ids=person_ids)
    db.scalars(
        select(Enrolment.id)
        .where(Enrolment.person_id.in_(person_ids))
        .order_by(Enrolment.id)
        .with_for_update()
    ).all()
    reconcile(db, user, person_ids)
    db.commit()
    return {
        "people_checked": len(person_ids),
        "reviews": db.scalar(select(func.count()).select_from(OverlapReview)),
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--demo", action="store_true", required=True)
    parser.add_argument("--officer-email", default="officer@example.test")
    args = parser.parse_args()
    settings = Settings()
    if settings.app_env not in {"local", "demo"}:
        raise SystemExit("Reconciliation is permitted only in explicitly local/demo environments")
    engine = make_engine(settings.database_url.get_secret_value())
    with Session(engine) as db:
        officer = db.scalar(
            select(User).where(
                User.email == args.officer_email, User.role == "officer", User.active.is_(True)
            )
        )
        if officer is None:
            raise SystemExit("An active, explicitly selected demo officer account is required")
        result = reconcile_existing(db, officer)
        print(
            f"Reconciled {result['people_checked']} synthetic people; {result['reviews']} retained review items."
        )
    engine.dispose()
