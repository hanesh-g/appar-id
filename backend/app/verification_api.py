from typing import Annotated, Literal
from uuid import UUID

from fastapi import APIRouter, Depends, Header, Query, Request
from sqlalchemy import func, select

from . import verification as domain
from .api import DB, SignedIn
from .db import utcnow
from .errors import DomainError
from .models import (
    ConsentGrant,
    Enrolment,
    User,
    VerificationAccess,
    VerificationRequest,
    VerifierOrganisation,
)
from .permissions import Permission, require_permission
from .schemas import PageOut
from .verification_contracts import (
    AccessOut,
    Approval,
    ApprovalOut,
    GrantOut,
    HandleCreate,
    HandleOut,
    OwnRecordOut,
    RequestCreate,
    ResolveOut,
    ResolveRequest,
    StudentRequestOut,
    SubmissionOut,
    SubmittedRequestOut,
    VersionRequest,
)

router = APIRouter(prefix="/api/v1")


def student(request: Request, user: SignedIn):
    if not request.app.state.settings.consent_enabled:
        raise DomainError("NOT_FOUND", "Feature unavailable", 404)
    require_permission(user, Permission.STUDENT_SELF)
    return user


def verifier(request: Request, user: SignedIn):
    if not request.app.state.settings.consent_enabled:
        raise DomainError("NOT_FOUND", "Feature unavailable", 404)
    require_permission(user, Permission.VERIFIER_REQUEST)
    return user


Student = Annotated[User, Depends(student)]
Verifier = Annotated[User, Depends(verifier)]


def page_result(db, stmt, page, render):
    total = db.scalar(select(func.count()).select_from(stmt.subquery()))
    rows = db.scalars(stmt.offset((page - 1) * 50).limit(50)).all()
    return {"total": total, "items": [render(row) for row in rows]}


@router.get("/me/enrolments", response_model=PageOut[OwnRecordOut])
def own_records(db: DB, user: Student, page: int = Query(1, ge=1)):
    stmt = (
        select(Enrolment)
        .where(Enrolment.person_id == user.person_id, Enrolment.identity_status == "VERIFIED")
        .order_by(Enrolment.id)
    )
    return page_result(db, stmt, page, lambda row: domain.own_record_out(db, row))


@router.post("/me/enrolments/{enrolment_id}/request-handles", response_model=HandleOut, status_code=201)
def handle(enrolment_id: UUID, data: HandleCreate, request: Request, db: DB, user: Student):
    return domain.create_handle(db, user, str(enrolment_id), data, request.app.state.settings)


@router.post("/verification-requests", response_model=SubmissionOut, status_code=202)
def submit(
    data: RequestCreate,
    request: Request,
    db: DB,
    user: Verifier,
    idempotency_key: Annotated[str, Header(min_length=1, max_length=100, pattern=r"^[A-Za-z0-9_.-]+$")],
):
    return domain.create_request(db, user, data, idempotency_key, request.app.state.settings)


@router.get("/me/verification-requests/submitted", response_model=PageOut[SubmittedRequestOut])
def submitted(db: DB, user: Verifier, page: int = Query(1, ge=1)):
    stmt = (
        select(VerificationRequest)
        .where(
            VerificationRequest.verifier_user_id == user.id,
            VerificationRequest.verifier_org_id == user.verifier_org_id,
        )
        .order_by(VerificationRequest.created_at.desc(), VerificationRequest.id)
    )
    return page_result(db, stmt, page, domain.request_out)


@router.get("/me/verification-requests", response_model=PageOut[StudentRequestOut])
def inbox(
    db: DB,
    user: Student,
    page: int = Query(1, ge=1),
    status: Literal["PENDING", "APPROVED", "DENIED", "EXPIRED"] | None = None,
):
    stmt = (
        select(VerificationRequest)
        .where(VerificationRequest.student_person_id == user.person_id)
        .order_by(VerificationRequest.created_at.desc(), VerificationRequest.id)
    )

    if status == "PENDING":
        stmt = stmt.where(VerificationRequest.status == "PENDING", VerificationRequest.expires_at > utcnow())
    elif status == "EXPIRED":
        stmt = stmt.where(VerificationRequest.status == "PENDING", VerificationRequest.expires_at <= utcnow())
    elif status:
        stmt = stmt.where(VerificationRequest.status == status)

    def render(row):
        record = domain.record(db, user.person_id, row.enrolment_id)
        return {
            **domain.request_out(row),
            "verifier_organisation": db.get(VerifierOrganisation, row.verifier_org_id).name,
            "record": domain.own_record_out(db, record) if record else None,
        }

    return page_result(db, stmt, page, render)


@router.post(
    "/me/verification-requests/{request_id}/approve",
    response_model=ApprovalOut,
    response_model_exclude_none=True,
)
def approve(request_id: UUID, data: Approval, request: Request, db: DB, user: Student):
    return domain.approve(db, user, str(request_id), data, request.app.state.settings)


@router.post("/me/verification-requests/{request_id}/deny", response_model=SubmittedRequestOut)
def deny(request_id: UUID, data: VersionRequest, db: DB, user: Student):
    return domain.deny(db, user, str(request_id), data.expected_version)


@router.get("/me/consent-grants", response_model=PageOut[GrantOut])
def grants(db: DB, user: Student, page: int = Query(1, ge=1)):
    stmt = (
        select(ConsentGrant)
        .where(ConsentGrant.student_person_id == user.person_id)
        .order_by(ConsentGrant.created_at.desc(), ConsentGrant.id)
    )
    return page_result(db, stmt, page, lambda row: domain.grant_out(db, row))


@router.post("/me/consent-grants/{grant_id}/revoke", response_model=GrantOut)
def revoke(grant_id: UUID, data: VersionRequest, db: DB, user: Student):
    return domain.revoke(db, user, str(grant_id), data.expected_version)


@router.post(
    "/me/consent-grants/{grant_id}/reissue", response_model=ApprovalOut, response_model_exclude_none=True
)
def reissue(grant_id: UUID, data: VersionRequest, request: Request, db: DB, user: Student):
    return domain.reissue(db, user, str(grant_id), data.expected_version, request.app.state.settings)


@router.get("/me/verification-accesses", response_model=PageOut[AccessOut])
def accesses(db: DB, user: Student, page: int = Query(1, ge=1)):
    stmt = (
        select(VerificationAccess)
        .where(VerificationAccess.student_person_id == user.person_id)
        .order_by(VerificationAccess.created_at.desc(), VerificationAccess.id)
    )

    def render(row):
        grant = db.get(ConsentGrant, row.grant_id)
        return {
            "id": row.id,
            "verifier_organisation": db.get(VerifierOrganisation, grant.verifier_org_id).name,
            "purpose": grant.purpose,
            "disclosed_fields": row.disclosed_fields,
            "accessed_at": row.created_at,
        }

    return page_result(db, stmt, page, render)


@router.post("/verification/resolve", response_model=ResolveOut)
def resolve(data: ResolveRequest, request: Request, db: DB, user: Verifier):
    require_permission(user, Permission.VERIFIER_RESOLVE)
    return domain.resolve(db, user, data.token.get_secret_value(), request.app.state.settings)
