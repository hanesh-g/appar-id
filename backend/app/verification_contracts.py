from datetime import datetime
from typing import Literal, get_args

from pydantic import BaseModel, Field, SecretStr, field_validator

from .schemas import StrictModel

FieldName = Literal[
    "programme", "institution_name", "academic_year", "admission_status", "start_date", "masked_apaar"
]
Purpose = Literal["ADMISSION_CONFIRMATION", "EMPLOYMENT_CHECK", "SCHOLARSHIP_CHECK"]
ALLOWED_FIELDS = frozenset(get_args(FieldName))


def unique_fields(value):
    if len(value) != len(set(value)):
        raise ValueError("Select each field once")
    return value


class HandleCreate(StrictModel):
    expected_version: int = Field(ge=1)


class RequestCreate(StrictModel):
    handle: SecretStr = Field(min_length=1, max_length=200)
    purpose: Purpose
    requested_fields: list[FieldName] = Field(min_length=1, max_length=6)
    _unique = field_validator("requested_fields")(unique_fields)


class Approval(StrictModel):
    expected_version: int = Field(ge=1)
    expected_record_version: int = Field(ge=1)
    allowed_fields: list[FieldName] = Field(min_length=1, max_length=6)
    expires_in_minutes: int = Field(default=15, ge=1, le=60)
    _unique = field_validator("allowed_fields")(unique_fields)


class VersionRequest(StrictModel):
    expected_version: int = Field(ge=1)


class ResolveRequest(StrictModel):
    token: SecretStr = Field(min_length=1, max_length=400)


class OwnRecordOut(BaseModel):
    id: str
    version: int
    fields: dict[FieldName, str]


class HandleOut(BaseModel):
    handle: str
    expires_at: datetime


class SubmissionOut(BaseModel):
    request_id: str
    status: Literal["SUBMITTED"] = "SUBMITTED"


class SubmittedRequestOut(BaseModel):
    id: str
    status: str
    version: int
    purpose: Purpose
    requested_fields: list[FieldName]
    created_at: datetime
    expires_at: datetime


class StudentRequestOut(SubmittedRequestOut):
    verifier_organisation: str
    record: OwnRecordOut | None


class GrantOut(BaseModel):
    id: str
    request_id: str
    version: int
    purpose: Purpose
    allowed_fields: list[FieldName]
    record_version: int
    expires_at: datetime
    revoked_at: datetime | None
    verifier_organisation: str
    can_reissue: bool


class ApprovalOut(BaseModel):
    grant: GrantOut
    token: str | None = None
    newly_issued: bool


class AccessOut(BaseModel):
    id: str
    verifier_organisation: str
    purpose: Purpose
    disclosed_fields: list[FieldName]
    accessed_at: datetime


class ResolveOut(BaseModel):
    fields: dict[FieldName, str]
    valid_until: datetime
    source: Literal["SYNTHETIC_DEMO"] = "SYNTHETIC_DEMO"
