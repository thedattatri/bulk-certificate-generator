from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, EmailStr, Field, field_validator, ConfigDict


class RecipientInput(BaseModel):
    """
    Schema for an individual recipient entry in a bulk request.
    Validates name, email, and optional per-recipient course/date overrides.
    """
    name: str = Field(..., min_length=2, max_length=120, description="Recipient's full name")
    email: EmailStr = Field(..., description="Recipient's valid email address")
    course_name: Optional[str] = Field(None, max_length=200, description="Optional custom course override")
    issue_date: Optional[str] = Field(None, max_length=50, description="Optional custom issue date (e.g. YYYY-MM-DD)")

    @field_validator("name")
    @classmethod
    def validate_name_not_blank(cls, v: str) -> str:
        trimmed = v.strip()
        if not trimmed:
            raise ValueError("Recipient name cannot be blank or whitespace only")
        # Ensure name doesn't contain unprintable characters
        if not all(c.isprintable() for c in trimmed):
            raise ValueError("Recipient name contains invalid characters")
        return trimmed


class JobCreateRequest(BaseModel):
    """
    Schema for submitting a bulk certificate generation job.
    Requires at least one recipient and a default course title.
    """
    course_name: str = Field(..., min_length=2, max_length=200, description="Name of the course / certification")
    issue_date: Optional[str] = Field(None, description="Issue date formatted as string (default: current date)")
    recipients: List[RecipientInput] = Field(
        ...,
        min_length=1,
        max_length=5000,
        description="List of recipients to generate certificates for (at least 1 required)"
    )

    @field_validator("course_name")
    @classmethod
    def validate_course_not_blank(cls, v: str) -> str:
        trimmed = v.strip()
        if not trimmed:
            raise ValueError("Course name cannot be blank or whitespace only")
        return trimmed


class CertificateResponse(BaseModel):
    """
    Schema for certificate details in API responses.
    """
    model_config = ConfigDict(from_attributes=True)

    id: str
    job_id: str
    recipient_name: str
    recipient_email: str
    course_name: str
    issue_date: str
    status: str
    certificate_file_path: Optional[str] = None
    error_message: Optional[str] = None
    download_url: Optional[str] = None
    created_at: datetime


class JobSummaryResponse(BaseModel):
    """
    Lightweight schema returned immediately upon job creation.
    """
    job_id: str
    status: str
    total_records: int
    message: str


class JobDetailResponse(BaseModel):
    """
    Full schema for tracking job progress and status, including all individual certificates.
    """
    model_config = ConfigDict(from_attributes=True)

    id: str
    status: str
    total_records: int
    successful_records: int
    failed_records: int
    created_at: datetime
    completed_at: Optional[datetime] = None
    certificates: List[CertificateResponse] = []
