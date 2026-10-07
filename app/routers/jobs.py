from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, status, Request
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import JobCreateRequest, JobSummaryResponse, JobDetailResponse, CertificateResponse
from app.crud import create_generation_job, get_job_by_id, process_bulk_job

router = APIRouter(prefix="/jobs", tags=["Jobs"])


@router.post(
    "",
    response_model=JobSummaryResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Submit bulk certificate generation job",
    description="Accepts bulk recipient details and starts an asynchronous background generation job."
)
def submit_bulk_job(
    job_in: JobCreateRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    # Persist job and certificates with initial PENDING status
    job = create_generation_job(db, job_in)

    # Queue execution in background so the API responds immediately
    background_tasks.add_task(process_bulk_job, job.id)

    return JobSummaryResponse(
        job_id=job.id,
        status=job.status.value,
        total_records=job.total_records,
        message="Bulk certificate job submitted successfully. Processing in background."
    )


@router.get(
    "/{job_id}",
    response_model=JobDetailResponse,
    summary="Get job status and recipient details",
    description="Check the current progress, counts of successful/failed certificates, and individual recipient statuses."
)
def get_job_status(
    job_id: str,
    request: Request,
    db: Session = Depends(get_db)
):
    job = get_job_by_id(db, job_id)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job with ID '{job_id}' not found."
        )

    base_url = str(request.base_url).rstrip("/")

    # Format certificates with dynamic download URLs for generated items
    certificates_out = []
    for cert in job.certificates:
        cert_data = CertificateResponse.model_validate(cert)
        if cert.status.value == "GENERATED":
            cert_data.download_url = f"{base_url}/certificates/{cert.id}"
        certificates_out.append(cert_data)

    return JobDetailResponse(
        id=job.id,
        status=job.status.value,
        total_records=job.total_records,
        successful_records=job.successful_records,
        failed_records=job.failed_records,
        created_at=job.created_at,
        completed_at=job.completed_at,
        certificates=certificates_out
    )
