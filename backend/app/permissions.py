"""Explicit capabilities. Missing institution scope never grants global access."""

from enum import StrEnum

from .errors import DomainError
from .models import User


class Permission(StrEnum):
    SESSION = "session"
    CORE_READ = "core_read"
    INSTITUTION_WRITE = "institution_write"
    CASE_MANAGE = "case_manage"
    OVERLAP_REVIEW = "overlap_review"
    AUDIT_VERIFY = "audit_verify"
    STUDENT_SELF = "student_self"
    VERIFIER_REQUEST = "verifier_request"
    VERIFIER_RESOLVE = "verifier_resolve"


ROLE_PERMISSIONS = {
    "institution_admin": frozenset(
        {Permission.SESSION, Permission.CORE_READ, Permission.INSTITUTION_WRITE, Permission.CASE_MANAGE}
    ),
    "officer": frozenset(
        {Permission.SESSION, Permission.CORE_READ, Permission.OVERLAP_REVIEW, Permission.AUDIT_VERIFY}
    ),
    "student": frozenset({Permission.SESSION, Permission.STUDENT_SELF}),
    "verifier": frozenset({Permission.SESSION, Permission.VERIFIER_REQUEST, Permission.VERIFIER_RESOLVE}),
}


def permitted(user: User, permission: Permission) -> bool:
    if not user.active:
        return False
    if user.role == "institution_admin":
        valid_scope = (
            user.institution_id is not None and user.person_id is None and user.verifier_org_id is None
        )
    elif user.role == "officer":
        valid_scope = user.institution_id is None and user.person_id is None and user.verifier_org_id is None
    elif user.role == "student":
        valid_scope = (
            user.institution_id is None and user.person_id is not None and user.verifier_org_id is None
        )
    elif user.role == "verifier":
        valid_scope = (
            user.institution_id is None and user.person_id is None and user.verifier_org_id is not None
        )
    else:
        return False
    return valid_scope and permission in ROLE_PERMISSIONS[user.role]


def require_permission(user: User, permission: Permission) -> None:
    if not permitted(user, permission):
        raise DomainError("FORBIDDEN", "This account cannot perform this action", 403)
