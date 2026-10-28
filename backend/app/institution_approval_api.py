from datetime import datetime
from typing import Annotated, Literal
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from pydantic import AfterValidator, BaseModel, Field, StringConstraints
from sqlalchemy import select

from . import institution_approval as domain
from .api import DB, Actor
from .models import Institution, User
from .permissions import Permission, require_permission
from .schemas import ProgrammeCreate, StrictModel

router = APIRouter(prefix="/api/v1/institution-approvals")
ApprovalYear = Annotated[
    str, StringConstraints(pattern=r"^20\d{2}-\d{2}$"), AfterValidator(ProgrammeCreate.valid_year)
]


class ApprovalProgrammeOut(BaseModel):
    id: str
    name: str
    academic_year: str
    intake: int
    source_intake: int | None
    source_matches: bool
    admissions_enabled: bool


class EvidenceProgrammeOut(BaseModel):
    id: str
    name: str
    academic_year: str
    intake: int


class EvidenceOut(BaseModel):
    mode: Literal["DEMO_FIXTURE"]
    catalogue_version: str
    catalogue_hash: str
    institution_reference: str
    institution_name: str
    aicte_id: str
    campus: str
    academic_year: str
    approval_reference: str
    valid_from: str
    valid_until: str
    programmes: list[EvidenceProgrammeOut]


class ApprovalEventOut(BaseModel):
    version: int
    status: str
    reason: str
    actor: str
    created_at: datetime


class ApprovalOut(BaseModel):
    institution_id: str
    institution_name: str
    institution_reference: str
    academic_year: str
    status: Literal["PENDING", "APPROVED", "SUSPENDED", "EXPIRED", "REVIEW_REQUIRED"]
    version: int
    mode: Literal["DEMO_FIXTURE"]
    can_approve: bool
    evidence_digest: str
    candidate_evidence: EvidenceOut | None
    reviewed_evidence: EvidenceOut | None
    reviewed_at: datetime | None
    reviewer: str | None
    programmes: list[ApprovalProgrammeOut]
    events: list[ApprovalEventOut]


class ApprovalDecision(StrictModel):
    academic_year: ApprovalYear
    expected_version: int = Field(ge=0)
    evidence_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    action: Literal["APPROVE_DEMO", "SUSPEND"]


def reviewer(user: Actor):
    require_permission(user, Permission.INSTITUTION_APPROVAL)
    return user


Reviewer = Annotated[User, Depends(reviewer)]


@router.get("", response_model=list[ApprovalOut])
def approvals(db: DB, user: Actor, academic_year: Annotated[ApprovalYear, Query()] = "2026-27"):
    statement = select(Institution).order_by(Institution.name)
    if user.role == "institution_admin":
        statement = statement.where(Institution.id == user.institution_id)
    return [domain.view(db, institution, academic_year) for institution in db.scalars(statement).all()]


@router.post("/{institution_id}/decisions", response_model=ApprovalOut)
def decide(institution_id: UUID, data: ApprovalDecision, db: DB, user: Reviewer):
    return domain.decide(db, user, str(institution_id), data)
