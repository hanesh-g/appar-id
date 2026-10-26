"""Transaction locks for verified identities, including people not created yet."""

from sqlalchemy import select, text

from .models import Person


def lock_identity_keys(db, crypto, verified_rows=(), old_person_ids=()):
    old = db.scalars(select(Person).where(Person.id.in_(list(old_person_ids)))).all()
    digests = {person.apaar_digest for person in old}
    digests.update(crypto.digest(raw["apaar_id"]) for raw in verified_rows)
    # An absent person row cannot be row-locked. A stable, private digest lock
    # serialises creation/promotions across institutions without logging identity.
    for digest in sorted(digests):
        key = int.from_bytes(bytes.fromhex(digest)[:8], "big", signed=True)
        db.execute(text("SELECT pg_advisory_xact_lock(:key)"), {"key": key})
    db.scalars(
        select(Person).where(Person.apaar_digest.in_(digests)).order_by(Person.id).with_for_update()
    ).all()
