import time
import pytest


def test_create_and_process_job_successfully(client):
    """
    Test submitting a valid bulk job with multiple recipients:
    - Verifies 202 Accepted status code
    - Verifies background processing completes
    - Checks that total_records, successful_records, and statuses update correctly.
    """
    payload = {
        "course_name": "Machine Learning Specialization",
        "issue_date": "October 2026",
        "recipients": [
            {"name": "Alice Johnson", "email": "alice@example.com"},
            {"name": "Bob Martin", "email": "bob@example.com"},
            {"name": "Charlie Brown", "email": "charlie@example.com"}
        ]
    }

    # Step 1: Submit Job
    response = client.post("/jobs", json=payload)
    assert response.status_code == 202
    data = response.json()
    assert "job_id" in data
    assert data["total_records"] == 3
    job_id = data["job_id"]

    # Step 2: Poll status (FastAPI TestClient processes background tasks before returning)
    get_res = client.get(f"/jobs/{job_id}")
    assert get_res.status_code == 200
    job_detail = get_res.json()

    assert job_detail["id"] == job_id
    assert job_detail["status"] == "COMPLETED"
    assert job_detail["total_records"] == 3
    assert job_detail["successful_records"] == 3
    assert job_detail["failed_records"] == 0
    assert len(job_detail["certificates"]) == 3

    for cert in job_detail["certificates"]:
        assert cert["status"] == "GENERATED"
        assert cert["download_url"] is not None
        assert cert["download_url"].endswith(cert["id"])


def test_get_nonexistent_job(client):
    """Querying a non-existent job ID should return HTTP 404."""
    response = client.get("/jobs/00000000-0000-0000-0000-000000000000")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_health_check_endpoints(client):
    """Test root and health check endpoints."""
    res_root = client.get("/")
    assert res_root.status_code == 200
    assert res_root.json()["status"] == "online"

    res_health = client.get("/health")
    assert res_health.status_code == 200
    assert res_health.json()["status"] == "healthy"
