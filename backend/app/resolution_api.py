from datetime import datetime
from typing import Annotated, Literal
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field, model_validator
from sqlalchemy import func, select

from . import resolution
from .api import DB, Editor
from .models import CaseEvent, ResolutionCase, User
from .permissions import Permission, require_permission
from .schemas import PageOut, StrictModel

router = APIRouter(prefix="/api/v1/resolution-cases")
Owner = Literal["COLLEGE_STAFF", "STUDENT_ACTION", "UPSTREAM_AUTHORITY"]
CaseStatus = Literal["OPEN", "WAITING_ON_USER", "WAITING_ON_AUTHORITY", "READY_TO_RECHECK", "RESOLVED"]


def case_user(user: Editor):
    require_permission(user, Permission.CASE_MANAGE)
    return user


CaseActor = Annotated[User, Depends(case_user)]


class CaseOut(BaseModel):
    id: str
    subject_kind: Literal["STAGED_ROW", "ENROLMENT"]
    batch_row_id: str | None
    enrolment_id: str | None
    origin_batch_id: str | None
    student_ref: str
    issue_code: str
    rule_set_id: str
    owner_type: Owner
    assignee_id: str | None
    status: CaseStatus
    resolution_reason: str | None
    evidence_kind: str | None
    version: int
    episode: int
    created_at: datetime
    updated_at: datetime
    resolved_at: datetime | None


class CaseEventOut(BaseModel):
    old_status: str | None
    new_status: str
    owner_type: str
    reason: str
    version: int
    created_at: datetime


class CaseDetailOut(CaseOut):
    events: list[CaseEventOut]


class CaseCreate(StrictModel):
    batch_row_id: UUID | None = None
    enrolment_id: UUID | None = None
    issue_code: str = Field(min_length=1, max_length=60, pattern=r"^[A-Z_]+$")

    @model_validator(mode="after")
    def one_subject(self):
        if (self.batch_row_id is None) == (self.enrolment_id is None):
            raise ValueError("Supply exactly one row or enrolment")
        return self


class CasePatch(StrictModel):
    expected_version: int = Field(ge=1)
    owner_type: Owner | None = None
    status: CaseStatus | None = None
    assignee_id: UUID | None = None


@router.post("", status_code=201, response_model=CaseOut)
def create(data: CaseCreate, db: DB, user: CaseActor):
    return resolution.case_out(db, resolution.open_case(db, user, data))


@router.get("", response_model=PageOut[CaseOut])
def cases(
    db: DB,
    user: CaseActor,
    status: CaseStatus | None = None,
    owner_type: Owner | None = None,
    code: str = Query("", max_length=60),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
):
    stmt = select(ResolutionCase).where(ResolutionCase.institution_id == user.institution_id)
    if status:
        stmt = stmt.where(ResolutionCase.status == status)
    if owner_type:
        stmt = stmt.where(ResolutionCase.owner_type == owner_type)
    if code:
        stmt = stmt.where(ResolutionCase.issue_code == code)
    total = db.scalar(select(func.count()).select_from(stmt.subquery()))
    items = db.scalars(
        stmt.order_by(ResolutionCase.updated_at.desc(), ResolutionCase.id)
        .offset((page - 1) * page_size)
        .limit(page_size)
    ).all()
    return {"total": total, "items": [resolution.case_out(db, c) for c in items]}


@router.get("/{case_id}", response_model=CaseDetailOut)
def detail(case_id: UUID, db: DB, user: CaseActor):
    case = resolution.own_case(db, user, str(case_id))
    events = db.scalars(
        select(CaseEvent).where(CaseEvent.case_id == case.id).order_by(CaseEvent.version.desc()).limit(100)
    ).all()
    return {
        **resolution.case_out(db, case),
        "events": [
            {
                "old_status": e.old_status,
                "new_status": e.new_status,
                "owner_type": e.owner_type,
                "reason": e.reason,
                "version": e.version,
                "created_at": e.created_at,
            }
            for e in events
        ],
    }


@router.patch("/{case_id}", response_model=CaseOut)
def change(case_id: UUID, data: CasePatch, db: DB, user: CaseActor):
    return resolution.case_out(db, resolution.patch_case(db, user, str(case_id), data))
