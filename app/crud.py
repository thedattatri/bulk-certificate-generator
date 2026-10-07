import logging
import uuid
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy.orm import Session

from app import database
from app.models import GenerationJob, Certificate, JobStatus, CertificateStatus, get_utc_now
from app.schemas import JobCreateRequest
from app.services.certificate_generator import generate_certificate_pdf

logger = logging.getLogger(__name__)


def create_generation_job(db: Session, job_data: JobCreateRequest) -> GenerationJob:
    """
    Creates a new GenerationJob and attaches all recipient Certificate records in PENDING state.
    """
    default_date = job_data.issue_date or datetime.now(timezone.utc).strftime("%B %d, %Y")
    job_id = str(uuid.uuid4())

    job = GenerationJob(
        id=job_id,
        status=JobStatus.PENDING,
        total_records=len(job_data.recipients),
        successful_records=0,
        failed_records=0,
        created_at=get_utc_now()
    )
    db.add(job)

    # Pre-populate all Certificate records linked to this job
    for recipient in job_data.recipients:
        cert_course = recipient.course_name or job_data.course_name
        cert_date = recipient.issue_date or default_date
        cert = Certificate(
            id=str(uuid.uuid4()),
            job_id=job_id,
            recipient_name=recipient.name,
            recipient_email=recipient.email,
            course_name=cert_course,
            issue_date=cert_date,
            status=CertificateStatus.PENDING,
            created_at=get_utc_now()
        )
        db.add(cert)

    db.commit()
    db.refresh(job)
    return job


def get_job_by_id(db: Session, job_id: str) -> Optional[GenerationJob]:
    """
    Fetches a job and its associated certificates by job ID.
    """
    return db.query(GenerationJob).filter(GenerationJob.id == job_id).first()


def get_certificate_by_id(db: Session, certificate_id: str) -> Optional[Certificate]:
    """
    Fetches a single certificate by certificate ID.
    """
    return db.query(Certificate).filter(Certificate.id == certificate_id).first()


def process_bulk_job(job_id: str) -> None:
    """
    Background worker task to process all recipients for a job.
    Processes each recipient independently:
    - If one certificate fails, its error is logged and its status is marked FAILED.
    - Subsequent certificates continue generating normally without stopping the batch.
    - Real-time progress updates are committed after each recipient.
    """
    db: Session = database.SessionLocal()
    try:
        job = db.query(GenerationJob).filter(GenerationJob.id == job_id).first()
        if not job:
            logger.error(f"Job {job_id} not found in background worker.")
            return

        # Mark job as PROCESSING
        job.status = JobStatus.PROCESSING
        db.commit()

        # Query all certificates for this job
        certificates = (
            db.query(Certificate)
            .filter(Certificate.job_id == job_id)
            .order_by(Certificate.created_at)
            .all()
        )

        for cert in certificates:
            try:
                # Generate PDF for individual recipient
                pdf_path = generate_certificate_pdf(
                    certificate_id=cert.id,
                    job_id=job.id,
                    recipient_name=cert.recipient_name,
                    course_name=cert.course_name,
                    issue_date=cert.issue_date
                )
                cert.status = CertificateStatus.GENERATED
                cert.certificate_file_path = pdf_path
                cert.error_message = None
                job.successful_records += 1
            except Exception as exc:
                logger.warning(
                    f"Failed to generate certificate {cert.id} for {cert.recipient_name}: {exc}"
                )
                cert.status = CertificateStatus.FAILED
                cert.error_message = str(exc)
                job.failed_records += 1

            # Commit after each certificate so that GET /jobs/{job_id} provides real-time progress
            db.commit()

        # Mark overall job completed
        job.status = JobStatus.COMPLETED
        job.completed_at = get_utc_now()
        db.commit()

    except Exception as e:
        logger.exception(f"Unhandled error while executing bulk job {job_id}: {e}")
        try:
            job = db.query(GenerationJob).filter(GenerationJob.id == job_id).first()
            if job:
                job.status = JobStatus.FAILED
                job.completed_at = get_utc_now()
                db.commit()
        except Exception:
            pass
    finally:
        db.close()
