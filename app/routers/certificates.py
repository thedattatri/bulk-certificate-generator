import os
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import CertificateStatus
from app.schemas import CertificateResponse
from app.crud import get_certificate_by_id

router = APIRouter(prefix="/certificates", tags=["Certificates"])


@router.get(
    "/{certificate_id}",
    summary="Download generated PDF certificate",
    description="Downloads the generated certificate PDF for a given certificate ID."
)
def download_certificate(
    certificate_id: str,
    db: Session = Depends(get_db)
):
    cert = get_certificate_by_id(db, certificate_id)
    if not cert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Certificate with ID '{certificate_id}' not found."
        )

    if cert.status == CertificateStatus.PENDING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Certificate generation is still in progress. Please check back shortly."
        )

    if cert.status == CertificateStatus.FAILED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Certificate generation failed for this recipient: {cert.error_message}"
        )

    if not cert.certificate_file_path or not os.path.exists(cert.certificate_file_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Certificate PDF file is missing on server storage."
        )

    # Sanitize file name for download header
    clean_name = "".join(c for c in cert.recipient_name if c.isalnum() or c in (" ", "_", "-")).strip()
    clean_name = clean_name.replace(" ", "_")
    filename = f"Certificate_{clean_name}_{cert.id[:8]}.pdf"

    return FileResponse(
        path=cert.certificate_file_path,
        media_type="application/pdf",
        filename=filename
    )


@router.get(
    "/{certificate_id}/metadata",
    response_model=CertificateResponse,
    summary="Get certificate metadata",
    description="Fetches metadata and generation status for a specific certificate without downloading the file."
)
def get_certificate_metadata(
    certificate_id: str,
    request: Request,
    db: Session = Depends(get_db)
):
    cert = get_certificate_by_id(db, certificate_id)
    if not cert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Certificate with ID '{certificate_id}' not found."
        )

    base_url = str(request.base_url).rstrip("/")
    cert_data = CertificateResponse.model_validate(cert)
    if cert.status == CertificateStatus.GENERATED:
        cert_data.download_url = f"{base_url}/certificates/{cert.id}"

    return cert_data
