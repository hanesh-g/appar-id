from collections import deque
from time import monotonic
from typing import Annotated
from uuid import UUID

import jwt
from fastapi import APIRouter, Depends, File, Form, Header, Query, Request, UploadFile
from fastapi.responses import Response
from sqlalchemy import func, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from . import rule_catalog, services
from .errors import DomainError
from .models import Audit, Batch, BatchRow, Enrolment, History, Institution, Programme, User
from .permissions import Permission, permitted, require_permission
from .rules import MAX_BYTES, safe_csv
from .schemas import (
    HEADERS,
    AuditOut,
    BatchOut,
    BatchRowOut,
    CommitRequest,
    EnrolmentOut,
    EnrolmentPatch,
    Login,
    PageOut,
    ProgrammeCreate,
    ProgrammeOut,
    ProgrammePatch,
    UserOut,
)
from .security import DUMMY_HASH, issue_token, password_hash

router = APIRouter(prefix="/api/v1")


def session(request: Request):
    with Session(request.app.state.engine, expire_on_commit=False) as db:
        yield db


DB = Annotated[Session, Depends(session)]


def authenticated(request: Request, db: DB, authorization: Annotated[str | None, Header()] = None):
    if not authorization or not authorization.startswith("Bearer "):
        raise DomainError("UNAUTHENTICATED", "Sign in to continue", 401)
    settings = request.app.state.settings
    try:
        claims = jwt.decode(
            authorization[7:],
            settings.jwt_secret.get_secret_value(),
            algorithms=["HS256"],
            audience=settings.jwt_audience,
            issuer=settings.jwt_issuer,
            options={"require": ["exp", "iat", "sub", "iss", "aud"]},
        )
        user_id = str(UUID(claims["sub"]))
    except (jwt.PyJWTError, ValueError, KeyError, TypeError):
        raise DomainError("UNAUTHENTICATED", "Your session expired. Sign in again", 401) from None
    user = db.get(User, user_id)
    if not user or not user.active:
        raise DomainError("UNAUTHENTICATED", "Sign in to continue", 401)
    return user


SignedIn = Annotated[User, Depends(authenticated)]


def core_user(user: SignedIn):
    require_permission(user, Permission.CORE_READ)
    return user


Actor = Annotated[User, Depends(core_user)]


def institution_user(user: Actor):
    require_permission(user, Permission.INSTITUTION_WRITE)
    return user


Editor = Annotated[User, Depends(institution_user)]


@router.get("/health")
def health(request: Request):
    try:
        with request.app.state.engine.connect() as connection:
            connection.execute(select(1))
    except SQLAlchemyError:
        return Response(
            content='{"status":"unavailable","database":"unavailable"}',
            status_code=503,
            media_type="application/json",
        )
    return {"status": "ok", "database": "ok", "registry": "simulated"}


@router.post("/auth/login")
def login(data: Login, request: Request, db: DB):
    key = (request.client.host if request.client else "local", data.email.casefold())
    attempts = request.app.state.login_attempts
    now = monotonic()
    # Bound retained keys and prune expired failures. Rate limit is single-process demo scope.
    for old_key in list(attempts):
        if not attempts[old_key] or attempts[old_key][-1] < now - 60:
            del attempts[old_key]
    if len(attempts) >= 10000 and key not in attempts:
        raise DomainError("RATE_LIMIT", "Try again later", 429)
    recent = attempts.setdefault(key, deque())
    while recent and recent[0] < now - 60:
        recent.popleft()
    if len(recent) >= 5:
        raise DomainError("RATE_LIMIT", "Too many login attempts. Try again in one minute", 429)
    recent.append(now)
    user = db.scalar(select(User).where(User.email == data.email.casefold()))
    valid = password_hash.verify(data.password.get_secret_value(), user.password_hash if user else DUMMY_HASH)
    if not user or not valid or not permitted(user, Permission.SESSION):
        raise DomainError("LOGIN_FAILED", "Email or password is incorrect", 401)
    return {"token": issue_token(user.id, request.app.state.settings), "user": UserOut.model_validate(user)}


@router.get("/auth/me", response_model=UserOut)
def me(user: Actor):
    return user


@router.get("/institutions")
def institutions(db: DB, user: Actor):
    statement = select(Institution)
    if user.role == "institution_admin":
        statement = statement.where(Institution.id == user.institution_id)
    return [{"id": i.id, "name": i.name, "reference": i.reference} for i in db.scalars(statement).all()]


@router.get("/programmes", response_model=list[ProgrammeOut])
def programmes(db: DB, user: Actor, academic_year: str | None = None):
    statement = services.query_scope(select(Programme), Programme, user)
    if academic_year:
        statement = statement.where(Programme.academic_year == academic_year)
    return db.scalars(statement.order_by(Programme.name)).all()


@router.post("/programmes", response_model=ProgrammeOut, status_code=201)
def create_programme(data: ProgrammeCreate, db: DB, user: Editor):
    programme = Programme(institution_id=user.institution_id, **data.model_dump())
    db.add(programme)
    db.flush()
    services.audit(
        db, user, "PROGRAMME_CREATED", programme.id, {"approved_intake": programme.approved_intake}
    )
    db.commit()
    return programme


@router.patch("/programmes/{programme_id}", response_model=ProgrammeOut)
def edit_programme(programme_id: UUID, data: ProgrammePatch, db: DB, user: Editor):
    programme = services.owned(db, Programme, str(programme_id), user)
    programme.approved_intake = data.approved_intake
    services.audit(db, user, "INTAKE_UPDATED", programme.id, {"approved_intake": programme.approved_intake})
    db.commit()
    return programme


def csv_response(content, filename):
    return Response(
        content,
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"', "Cache-Control": "no-store"},
    )


@router.get("/templates/students.csv")
def template(user: Actor):
    return csv_response(safe_csv([], HEADERS), "students-template.csv")


def batch_out(batch):
    return {
        "id": batch.id,
        "filename": batch.filename,
        "academic_year": batch.academic_year,
        "rule_set_id": batch.rule_set_id,
        "status": batch.status,
        "summary": batch.summary,
        "result": batch.result,
        "created_at": batch.created_at,
    }


@router.post("/batches", status_code=201, response_model=BatchOut)
def upload_batch(
    request: Request,
    db: DB,
    user: Editor,
    file: Annotated[UploadFile, File()],
    academic_year: Annotated[str, Form(pattern=r"^20\d{2}-\d{2}$")],
    idempotency_key: Annotated[str, Header(min_length=1, max_length=100)],
):
    content = file.file.read(MAX_BYTES + 1)
    filename = (file.filename or "students.csv").replace("\\", "/").rsplit("/", 1)[-1]
    return batch_out(
        services.upload(
            db,
            user,
            content,
            filename,
            academic_year,
            idempotency_key,
            request.app.state.crypto,
            request.app.state.settings,
        )
    )


@router.get("/batches/{batch_id}", response_model=BatchOut)
def get_batch(batch_id: UUID, db: DB, user: Actor):
    return batch_out(services.owned(db, Batch, str(batch_id), user))


@router.get("/batches/{batch_id}/rows", response_model=PageOut[BatchRowOut])
def batch_rows(
    batch_id: UUID,
    request: Request,
    db: DB,
    user: Actor,
    status: str | None = None,
    code: str | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(100, ge=1, le=500),
):
    batch = services.owned(db, Batch, str(batch_id), user)
    rows = db.scalars(select(BatchRow).where(BatchRow.batch_id == batch.id).order_by(BatchRow.row_no)).all()
    rows = [
        r
        for r in rows
        if (not status or r.status == status) and (not code or any(i["code"] == code for i in r.issues))
    ]
    return {
        "total": len(rows),
        "items": [
            {
                "id": r.id,
                "row_no": r.row_no,
                "student_ref": r.student_ref,
                "identity_status": r.identity_status,
                "identity_reason": r.identity_reason,
                "status": r.status,
                "issues": r.issues,
            }
            for r in rows[(page - 1) * page_size : page * page_size]
        ],
    }


@router.get("/batches/{batch_id}/errors.csv")
def correction_csv(batch_id: UUID, request: Request, db: DB, user: Editor):
    batch = services.owned(db, Batch, str(batch_id), user)
    rows = db.scalars(select(BatchRow).where(BatchRow.batch_id == batch.id).order_by(BatchRow.row_no)).all()
    raw = [request.app.state.crypto.decrypt(r.raw_enc) for r in rows if r.issues]
    return csv_response(safe_csv(raw, HEADERS), "student-corrections.csv")


@router.post("/batches/{batch_id}/commit", response_model=BatchOut)
def commit(batch_id: UUID, data: CommitRequest, request: Request, db: DB, user: Editor):
    return batch_out(services.commit_batch(db, user, str(batch_id), data.mode, request.app.state.crypto))


@router.post("/batches/{batch_id}/discard", response_model=BatchOut)
def discard(batch_id: UUID, db: DB, user: Editor):
    batch = db.scalar(
        select(Batch)
        .where(Batch.id == str(batch_id), Batch.institution_id == user.institution_id)
        .with_for_update()
    )
    if not batch:
        raise DomainError("NOT_FOUND", "Batch not found", 404)
    if batch.status == "COMMITTED":
        raise DomainError("BATCH_STATE", "Committed batches cannot be discarded", 409)
    if batch.status != "DISCARDED":
        batch.status = "DISCARDED"
        services.audit(db, user, "BATCH_DISCARDED", batch.id)
        db.commit()
    return batch_out(batch)


@router.get("/dashboard")
def dashboard(
    request: Request,
    db: DB,
    user: Actor,
    institution_id: UUID | None = None,
    academic_year: str | None = None,
):
    return services.dashboard(db, user, str(institution_id) if institution_id else None, academic_year)


def enrolment_out(record, db, user, crypto):
    raw = crypto.decrypt(record.identity_enc)
    result = {
        "id": record.id,
        "student_ref": record.student_ref,
        "programme_id": record.programme_id,
        "programme": db.get(Programme, record.programme_id).name,
        "academic_year": record.academic_year,
        "identity_status": record.identity_status,
        "identity_reason": record.identity_reason,
        "apaar_masked": "********" + raw["apaar_id"][-4:] if raw.get("apaar_id") else "Not supplied",
        "status": record.status,
        "start_date": record.start_date,
        "end_date": record.end_date,
        "version": record.version,
    }
    if user.institution_id == record.institution_id:
        result["student_name"] = raw["student_name"]
    return result


@router.get("/enrolments", response_model=PageOut[EnrolmentOut], response_model_exclude_none=True)
def enrolments(
    request: Request,
    db: DB,
    user: Actor,
    search: str = Query("", max_length=100),
    status: str | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
):
    statement = services.query_scope(select(Enrolment), Enrolment, user)
    if search:
        statement = statement.where(Enrolment.student_ref.ilike(f"%{search}%"))
    if status:
        statement = statement.where(Enrolment.status == status)
    total = db.scalar(select(func.count()).select_from(statement.subquery()))
    records = db.scalars(
        statement.order_by(Enrolment.student_ref).offset((page - 1) * page_size).limit(page_size)
    ).all()
    return {"total": total, "items": [enrolment_out(e, db, user, request.app.state.crypto) for e in records]}


@router.get("/enrolments/{enrolment_id}", response_model=EnrolmentOut, response_model_exclude_none=True)
def get_enrolment(enrolment_id: UUID, request: Request, db: DB, user: Actor):
    record = services.owned(db, Enrolment, str(enrolment_id), user)
    data = enrolment_out(record, db, user, request.app.state.crypto)
    data["history"] = [
        {"version": h.version, "snapshot": h.snapshot, "created_at": h.created_at}
        for h in db.scalars(
            select(History).where(History.enrolment_id == record.id).order_by(History.version)
        ).all()
    ]
    return data


@router.patch("/enrolments/{enrolment_id}", response_model=EnrolmentOut, response_model_exclude_none=True)
def edit_enrolment(enrolment_id: UUID, data: EnrolmentPatch, request: Request, db: DB, user: Editor):
    return enrolment_out(
        services.edit_enrolment(db, user, str(enrolment_id), data), db, user, request.app.state.crypto
    )


@router.post("/enrolments/recheck-identities")
def retry_identities(request: Request, db: DB, user: Editor):
    return services.recheck(db, user, request.app.state.crypto, request.app.state.settings)


@router.get("/audit-events", response_model=PageOut[AuditOut])
def audit_events(db: DB, user: Actor, page: int = Query(1, ge=1)):
    statement = services.query_scope(select(Audit), Audit, user)
    total = db.scalar(select(func.count()).select_from(statement.subquery()))
    items = db.scalars(statement.order_by(Audit.created_at.desc()).offset((page - 1) * 50).limit(50)).all()
    return {
        "total": total,
        "items": [
            {
                "id": e.id,
                "action": e.action,
                "entity_id": e.entity_id,
                "created_at": e.created_at,
                "details": e.details,
                "actor": db.get(User, e.actor_id).name,
                "request_id": e.request_id,
            }
            for e in items
        ],
    }


@router.get("/rules")
def rules(db: DB, user: Actor, rule_set_id: str | None = Query(None, max_length=80)):
    return rule_catalog.read_pack(db, rule_set_id)


@router.get("/rules/{issue_code}")
def rule(issue_code: str, db: DB, user: Actor, rule_set_id: str | None = Query(None, max_length=80)):
    pack = rule_catalog.read_pack(db, rule_set_id)
    entry = pack["rules"].get(issue_code)
    if entry is None:
        raise DomainError("RULE_NOT_FOUND", "Rule explanation not found", 404)
    return {"rule_set_id": pack["rule_set_id"], **entry}
