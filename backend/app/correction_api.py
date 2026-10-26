from datetime import datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Request
from pydantic import BaseModel, Field, StringConstraints

from . import corrections
from .api import DB
from .resolution_api import CaseActor
from .schemas import IssueOut, StrictModel

router = APIRouter(prefix="/api/v1")


class PreviewRequest(StrictModel):
    expected_version: int = Field(ge=1)
    changes: dict[str, Annotated[str, StringConstraints(max_length=200)]] = Field(max_length=15)


class ApplyRequest(StrictModel):
    expected_version: int = Field(ge=1)


class CorrectionContextOut(BaseModel):
    case_version: int
    fields: dict[str, str]
    immutable_fields: list[str]


class FieldDiff(BaseModel):
    field: str
    before: str
    after: str


class CorrectionPreviewOut(BaseModel):
    id: str
    case_version: int
    target_version: int
    expires_at: datetime
    changes: list[FieldDiff]
    issues: list[IssueOut]
    identity_status: str
    identity_reason: str
    outcome: dict[str, int]
    active_delta: int
    can_apply: bool
    rule_set_id: str


class CorrectionResultOut(BaseModel):
    proposal_id: str
    batch_id: str
    enrolment_id: str
    case_id: str
    case_status: str
    case_version: int
    active_delta: int
    created: int
    updated: int
    unchanged: int
    held: int


@router.get("/resolution-cases/{case_id}/correction-context", response_model=CorrectionContextOut)
def editor_context(case_id: UUID, db: DB, user: CaseActor, request: Request):
    case, fields, _ = corrections.context(db, user, str(case_id), request.app.state.crypto)
    return {
        "case_version": case.version,
        "fields": fields,
        "immutable_fields": ["student_ref", "programme", "academic_year"] if case.enrolment_id else [],
    }


@router.post(
    "/resolution-cases/{case_id}/correction-previews", status_code=201, response_model=CorrectionPreviewOut
)
def preview(case_id: UUID, data: PreviewRequest, db: DB, user: CaseActor, request: Request):
    return corrections.preview(
        db, user, str(case_id), data, request.app.state.crypto, request.app.state.settings
    )


@router.post("/correction-proposals/{proposal_id}/apply", response_model=CorrectionResultOut)
def apply(proposal_id: UUID, data: ApplyRequest, db: DB, user: CaseActor, request: Request):
    return corrections.apply(
        db, user, str(proposal_id), data, request.app.state.crypto, request.app.state.settings
    )
