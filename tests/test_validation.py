import pytest


def test_validation_empty_recipient_list(client):
    """Submitting a job with an empty recipient list must be rejected with HTTP 422."""
    payload = {
        "course_name": "Full Stack Engineering",
        "recipients": []
    }
    response = client.post("/jobs", json=payload)
    assert response.status_code == 422
    data = response.json()
    assert "detail" in data


def test_validation_blank_course_name(client):
    """Submitting a job with a blank course name must be rejected with HTTP 422."""
    payload = {
        "course_name": "   ",
        "recipients": [
            {"name": "Alice Smith", "email": "alice@example.com"}
        ]
    }
    response = client.post("/jobs", json=payload)
    assert response.status_code == 422


def test_validation_blank_recipient_name(client):
    """Submitting a recipient with an empty or whitespace name must be rejected."""
    payload = {
        "course_name": "Cloud Computing",
        "recipients": [
            {"name": "   ", "email": "valid@example.com"}
        ]
    }
    response = client.post("/jobs", json=payload)
    assert response.status_code == 422


def test_validation_invalid_email(client):
    """Submitting a recipient with a malformed email must be rejected."""
    payload = {
        "course_name": "DevOps Foundations",
        "recipients": [
            {"name": "Bob Jones", "email": "not-an-email-address"}
        ]
    }
    response = client.post("/jobs", json=payload)
    assert response.status_code == 422


def test_validation_missing_required_fields(client):
    """Submitting an empty JSON payload must return HTTP 422."""
    response = client.post("/jobs", json={})
    assert response.status_code == 422
