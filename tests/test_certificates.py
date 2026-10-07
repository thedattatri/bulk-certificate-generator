import os
import pytest


def test_certificate_download_and_format(client):
    """
    Test generating a certificate and downloading the resulting PDF:
    - Verifies HTTP 200 and Content-Type: application/pdf
    - Verifies the binary content has valid PDF magic header (%PDF-)
    - Verifies content-disposition contains sanitized filename
    """
    payload = {
        "course_name": "Full Stack Web Development",
        "recipients": [
            {"name": "Devin Learner", "email": "devin@example.com"}
        ]
    }
    submit_res = client.post("/jobs", json=payload)
    job_id = submit_res.json()["job_id"]

    job_res = client.get(f"/jobs/{job_id}")
    cert_id = job_res.json()["certificates"][0]["id"]

    # Download certificate
    download_res = client.get(f"/certificates/{cert_id}")
    assert download_res.status_code == 200
    assert download_res.headers["content-type"] == "application/pdf"
    assert download_res.content.startswith(b"%PDF-")
    assert "Certificate_Devin_Learner" in download_res.headers["content-disposition"]


def test_individual_failure_does_not_block_others(client):
    """
    CRITICAL REQUIREMENT:
    Ensure that when one recipient fails, subsequent valid recipients continue,
    and their certificates are successfully generated and downloadable.
    """
    payload = {
        "course_name": "Resilient Systems Architecture",
        "recipients": [
            {"name": "Good Recipient One", "email": "one@example.com"},
            {"name": "FAIL_TRIGGER_TEST", "email": "fail@example.com"},  # triggers generator error
            {"name": "Good Recipient Two", "email": "two@example.com"}
        ]
    }

    # Submit the mixed batch
    submit_res = client.post("/jobs", json=payload)
    assert submit_res.status_code == 202
    job_id = submit_res.json()["job_id"]

    # Fetch status
    job_res = client.get(f"/jobs/{job_id}")
    assert job_res.status_code == 200
    job_data = job_res.json()

    # Verify counts
    assert job_data["total_records"] == 3
    assert job_data["successful_records"] == 2
    assert job_data["failed_records"] == 1
    assert job_data["status"] == "COMPLETED"

    certs = job_data["certificates"]
    assert len(certs) == 3

    # Check recipient 1: Success
    assert certs[0]["recipient_name"] == "Good Recipient One"
    assert certs[0]["status"] == "GENERATED"
    assert certs[0]["download_url"] is not None
    download_1 = client.get(f"/certificates/{certs[0]['id']}")
    assert download_1.status_code == 200
    assert download_1.content.startswith(b"%PDF-")

    # Check recipient 2: Failed
    assert certs[1]["recipient_name"] == "FAIL_TRIGGER_TEST"
    assert certs[1]["status"] == "FAILED"
    assert "Simulated generator failure" in certs[1]["error_message"]
    # Downloading failed certificate must yield 400 Bad Request
    download_2 = client.get(f"/certificates/{certs[1]['id']}")
    assert download_2.status_code == 400
    assert "failed" in download_2.json()["detail"].lower()

    # Check recipient 3: Success despite recipient 2 failing earlier
    assert certs[2]["recipient_name"] == "Good Recipient Two"
    assert certs[2]["status"] == "GENERATED"
    assert certs[2]["download_url"] is not None
    download_3 = client.get(f"/certificates/{certs[2]['id']}")
    assert download_3.status_code == 200
    assert download_3.content.startswith(b"%PDF-")


def test_certificate_metadata_endpoint(client):
    """Test retrieving certificate metadata."""
    payload = {
        "course_name": "Data Science Foundations",
        "recipients": [{"name": "Elena Rostova", "email": "elena@example.com"}]
    }
    submit_res = client.post("/jobs", json=payload)
    job_id = submit_res.json()["job_id"]

    job_res = client.get(f"/jobs/{job_id}")
    cert_id = job_res.json()["certificates"][0]["id"]

    meta_res = client.get(f"/certificates/{cert_id}/metadata")
    assert meta_res.status_code == 200
    meta = meta_res.json()
    assert meta["id"] == cert_id
    assert meta["recipient_name"] == "Elena Rostova"
    assert meta["course_name"] == "Data Science Foundations"
    assert meta["status"] == "GENERATED"


def test_download_nonexistent_certificate(client):
    """Attempting to download a non-existent certificate returns HTTP 404."""
    response = client.get("/certificates/nonexistent-id-000")
    assert response.status_code == 404
