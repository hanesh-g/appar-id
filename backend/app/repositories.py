"""Scope-aware database access shared by HTTP routes and domain services."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from .errors import DomainError
from .models import User


def query_scope(statement, model, user: User):
    if user.institution_id:
        statement = statement.where(model.institution_id == user.institution_id)
    return statement


def owned(db: Session, model, object_id: str, user: User):
    obj = db.scalar(query_scope(select(model).where(model.id == object_id), model, user))
    if obj is None:
        raise DomainError("NOT_FOUND", "Record not found", 404)
    return obj
