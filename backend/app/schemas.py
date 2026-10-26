import re
from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, SecretStr, field_validator, model_validator

YEAR = r"^20\d{2}-\d{2}$"
Status = Literal["ENROLLED", "WITHDRAWN", "TRANSFERRED", "COMPLETED"]


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class Login(StrictModel):
    email: str = Field(min_length=3, max_length=200)
    password: SecretStr = Field(min_length=1, max_length=200)


class ProgrammeCreate(StrictModel):
    name: str = Field(min_length=2, max_length=120)
    academic_year: str = Field(pattern=YEAR)
    approved_intake: int = Field(ge=0, le=100000)

    @field_validator("academic_year")
    @classmethod
    def valid_year(cls, value: str) -> str:
        if int(value[-2:]) != (int(value[:4]) + 1) % 100:
            raise ValueError("Use consecutive academic years, such as 2026-27")
        return value


class ProgrammePatch(StrictModel):
    approved_intake: int = Field(ge=0, le=100000)


class StudentRow(StrictModel):
    student_ref: str = Field(min_length=1, max_length=100)
    apaar_id: str = Field(default="", max_length=40)
    student_name: str = Field(min_length=1, max_length=150)
    date_of_birth: date
    programme: str = Field(min_length=2, max_length=120)
    academic_year: str = Field(pattern=YEAR)
    admission_date: date
    start_date: date
    end_date: date | None = None
    status: Status
    seat_type: str = Field(default="", max_length=100)
    supernumerary: Literal["Y", "N"]
    nri: Literal["Y", "N"]
    oci: Literal["Y", "N"]
    foreign_national: Literal["Y", "N"]

    @field_validator("end_date", mode="before")
    @classmethod
    def empty_date(cls, value):
        return None if value == "" else value

    @field_validator("apaar_id")
    @classmethod
    def normalize_id(cls, value: str) -> str:
        return re.sub(r"[ -]", "", value)

    @model_validator(mode="after")
    def dates(self):
        if self.date_of_birth >= self.admission_date:
            raise ValueError("Date of birth must precede admission")
        if self.start_date < self.admission_date:
            raise ValueError("Start date must not precede admission")
        if self.status == "ENROLLED" and self.end_date is not None:
            raise ValueError("An active enrolment must have no end date")
        if self.status != "ENROLLED" and self.end_date is None:
            raise ValueError("An end date is required for this status")
        if self.end_date is not None and self.end_date < self.start_date:
            raise ValueError("End date must not precede start date")
        return self


HEADERS = list(StudentRow.model_fields)


class CommitRequest(StrictModel):
    mode: Literal["commit_valid", "all_or_nothing"] = "commit_valid"


class EnrolmentPatch(StrictModel):
    expected_version: int = Field(ge=1)
    status: Status
    end_date: date | None = None


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    email: str
    name: str
    role: str
    institution_id: str | None


class ProgrammeOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    institution_id: str
    name: str
    academic_year: str
    approved_intake: int


class IssueOut(BaseModel):
    code: str
    field: str
    message: str
    severity: Literal["ERROR", "WARNING"]


class BatchOut(BaseModel):
    id: str
    filename: str
    academic_year: str
    rule_set_id: str
    status: str
    summary: dict
    commit_summary: dict | None = None
    result: dict[str, int] | None
    created_at: datetime


class BatchRowOut(BaseModel):
    id: str
    row_no: int
    student_ref: str
    identity_status: str
    identity_reason: str
    status: str
    issues: list[IssueOut]


class PageOut[T](BaseModel):
    total: int
    items: list[T]


class EnrolmentOut(BaseModel):
    id: str
    student_ref: str
    student_name: str | None = None
    programme_id: str
    programme: str
    academic_year: str
    identity_status: str
    identity_reason: str
    apaar_masked: str
    status: str
    start_date: date
    end_date: date | None
    version: int
    history: list[dict] | None = None


class AuditOut(BaseModel):
    id: str
    action: str
    entity_id: str
    created_at: datetime
    details: dict
    actor: str
    request_id: str | None
