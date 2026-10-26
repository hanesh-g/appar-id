from datetime import date, datetime
from typing import Annotated, Literal
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field, model_validator
from sqlalchemy import func, select

from . import overlaps
from .api import DB, Actor
from .errors import DomainError
from .models import OverlapEvent, OverlapReview, User
from .permissions import Permission, require_permission
from .schemas import PageOut, StrictModel

router = APIRouter(prefix="/api/v1/overlap-reviews")


def reviewer(user: Actor):
    require_permission(user, Permission.OVERLAP_REVIEW)
    return user


Reviewer = Annotated[User, Depends(reviewer)]


class IntervalRecordOut(BaseModel):
    institution: str
    programme: str
    start_date: date
    end_date: date | None
    status: str
    version: int


class ReviewOut(BaseModel):
    id: str
    status: str
    version: int
    overlap_start: date
    overlap_end: date | None
    scheduled: bool
    apaar_masked: str
    review_reason: str | None
    policy_reference: str | None
    resolved_at: datetime | None
    records: list[IntervalRecordOut]


class ReviewEventOut(BaseModel):
    version: int
    status: str
    reason: str
    created_at: datetime


class ReviewDetailOut(ReviewOut):
    events: list[ReviewEventOut]


class ReviewDecision(StrictModel):
    expected_version: int = Field(ge=1)
    status: Literal["REVIEWED_PERMITTED_DUAL", "REVIEWED_TRANSFER_LAG", "ESCALATED"]
    reason: Literal["DEMO_DUAL_REVIEW", "TRANSFER_RECORD_LAG", "NEEDS_MORE_EVIDENCE"]
    policy_reference: Literal["DEMO_INTERVAL_POLICY_V1"] = "DEMO_INTERVAL_POLICY_V1"

    @model_validator(mode="after")
    def matching_reason(self):
        expected = {
            "REVIEWED_PERMITTED_DUAL": "DEMO_DUAL_REVIEW",
            "REVIEWED_TRANSFER_LAG": "TRANSFER_RECORD_LAG",
            "ESCALATED": "NEEDS_MORE_EVIDENCE",
        }
        if self.reason != expected[self.status]:
            raise ValueError("Use the reason corresponding to the review decision")
        return self


@router.get("", response_model=PageOut[ReviewOut])
def reviews(db: DB, user: Reviewer, status: str = Query("", max_length=40), page: int = Query(1, ge=1)):
    stmt = select(OverlapReview)
    if status:
        stmt = stmt.where(OverlapReview.status == status)
    total = db.scalar(select(func.count()).select_from(stmt.subquery()))
    rows = db.scalars(
        stmt.order_by(OverlapReview.created_at.desc(), OverlapReview.id).offset((page - 1) * 50).limit(50)
    ).all()
    return {"total": total, "items": [overlaps.review_out(db, r) for r in rows]}


@router.get("/{review_id}", response_model=ReviewDetailOut)
def detail(review_id: UUID, db: DB, user: Reviewer):
    review = db.get(OverlapReview, str(review_id))
    if review is None:
        raise DomainError("NOT_FOUND", "Review not found", 404)
    events = db.scalars(
        select(OverlapEvent)
        .where(OverlapEvent.review_id == review.id)
        .order_by(OverlapEvent.version.desc())
        .limit(100)
    ).all()
    return {
        **overlaps.review_out(db, review),
        "events": [
            {"version": e.version, "status": e.status, "reason": e.reason, "created_at": e.created_at}
            for e in events
        ],
    }


@router.patch("/{review_id}", response_model=ReviewOut)
def decide(review_id: UUID, data: ReviewDecision, db: DB, user: Reviewer):
    return overlaps.review_out(db, overlaps.decide(db, user, str(review_id), data))
