import enum
import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Enum, Text
from sqlalchemy.orm import relationship

from app.database import Base


class JobStatus(str, enum.Enum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class CertificateStatus(str, enum.Enum):
    PENDING = "PENDING"
    GENERATED = "GENERATED"
    FAILED = "FAILED"


def get_utc_now():
    return datetime.now(timezone.utc)


class GenerationJob(Base):
    """
    Represents a bulk certificate generation request.
    Tracks overall progress, total recipients, successes, and failures.
    """
    __tablename__ = "generation_jobs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    status = Column(Enum(JobStatus), default=JobStatus.PENDING, nullable=False, index=True)
    total_records = Column(Integer, default=0, nullable=False)
    successful_records = Column(Integer, default=0, nullable=False)
    failed_records = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime, default=get_utc_now, nullable=False)
    completed_at = Column(DateTime, nullable=True)

    # One-to-many relationship with certificates
    certificates = relationship(
        "Certificate",
        back_populates="job",
        cascade="all, delete-orphan",
        order_by="Certificate.created_at"
    )

    def __repr__(self):
        return f"<GenerationJob id={self.id} status={self.status} total={self.total_records}>"


class Certificate(Base):
    """
    Represents an individual certificate for a single recipient.
    Tracks the recipient details, generation status, saved file path, or failure reason.
    """
    __tablename__ = "certificates"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    job_id = Column(String(36), ForeignKey("generation_jobs.id"), nullable=False, index=True)
    recipient_name = Column(String(255), nullable=False)
    recipient_email = Column(String(255), nullable=False)
    course_name = Column(String(255), nullable=False)
    issue_date = Column(String(50), nullable=False)
    status = Column(Enum(CertificateStatus), default=CertificateStatus.PENDING, nullable=False, index=True)
    certificate_file_path = Column(String(500), nullable=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=get_utc_now, nullable=False)

    # Many-to-one relationship with generation_job
    job = relationship("GenerationJob", back_populates="certificates")

    def __repr__(self):
        return f"<Certificate id={self.id} recipient={self.recipient_name} status={self.status}>"
