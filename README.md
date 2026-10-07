# Bulk Certificate Generator Backend

A high-performance, asynchronous REST API built with **FastAPI**, **SQLAlchemy**, **SQLite**, **Pydantic**, and **ReportLab** for bulk certificate generation.

---

## 📋 Overview & Core Features

* **Bulk Recipient Processing**: Submit single or batch certificate generation requests for multiple recipients at once.
* **Asynchronous Job & Status Tracking**: Jobs are queued and processed asynchronously in the background. Status transitions (`PENDING` ➔ `PROCESSING` ➔ `COMPLETED`) are queryable in real time.
* **Partial Failure Resilience (Individual Failure Handling)**: If a single recipient in a batch encounters an error (e.g., bad character data, rendering issue), that individual certificate is recorded as `FAILED` with an error message, while **all other valid certificates continue generating without interruption**.
* **Predefined Certificate Template**: Programmatically renders high-resolution landscape certificates featuring borders, typography, course titles, recipient names, verification IDs, and signature blocks using **ReportLab**.
* **Certificate Retrieval**: Direct PDF file streaming via `GET /certificates/{certificate_id}` with sanitized filenames and verification headers.
* **Input Validation**: Strict request schema validation via **Pydantic** (validates email syntax, disallows empty/blank recipient lists and names).
* **Comprehensive Automated Testing**: 100% passing test suite testing validation, job status tracking, PDF generation, partial failure resilience, and downloads.

---

## 🏗️ Architecture & Project Structure

```text
bulk-certificate-generator/
│
├── app/
│   ├── __init__.py
│   ├── main.py                     # FastAPI application setup, middleware, lifecycle
│   ├── database.py                 # SQLAlchemy engine, session factory, dependency
│   ├── models.py                   # GenerationJob and Certificate ORM models
│   ├── schemas.py                  # Pydantic validation and serialization models
│   ├── crud.py                     # DB transactions and background job execution logic
│   │
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── jobs.py                 # POST /jobs, GET /jobs/{job_id}
│   │   └── certificates.py         # GET /certificates/{certificate_id}
│   │
│   └── services/
│       ├── __init__.py
│       └── certificate_generator.py # ReportLab PDF rendering engine
│
├── templates/
│   └── certificate_template.pdf    # Sample certificate reference
│
├── generated_certificates/         # Local file storage for generated PDFs (grouped by job_id)
│   └── .gitkeep
│
├── tests/
│   ├── __init__.py
│   ├── conftest.py                 # Isolated test database fixture & TestClient
│   ├── test_jobs.py                # Job submission and status polling tests
│   ├── test_validation.py          # Input constraints and edge-case validation tests
│   └── test_certificates.py        # PDF generation, download, and partial failure tests
│
├── requirements.txt                # Project dependencies
├── .gitignore                      # Git ignore rules for SQLite, venv, and generated files
└── README.md                       # Documentation and design decisions
```

---

## 🚀 Getting Started

### 1. Prerequisites
* Python 3.10+ (tested on Python 3.13)
* `git`

### 2. Clone the Repository & Setup Virtual Environment
```bash
cd bulk-certificate-generator

# Create a virtual environment
python3 -m venv venv

# Activate virtual environment
# On macOS / Linux:
source venv/bin/activate
# On Windows:
# .\venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Run the API Server
```bash
uvicorn app.main:app --reload --port 8000
```

Once running, explore interactive API documentation:
* **Swagger UI**: [http://localhost:8000/docs](http://localhost:8000/docs)
* **ReDoc**: [http://localhost:8000/redoc](http://localhost:8000/redoc)

---

## 🧪 Running Automated Tests

Run the full test suite with `pytest`:

```bash
pytest -v
```

Expected output:
```text
tests/test_certificates.py::test_certificate_download_and_format PASSED
tests/test_certificates.py::test_individual_failure_does_not_block_others PASSED
tests/test_certificates.py::test_certificate_metadata_endpoint PASSED
tests/test_certificates.py::test_download_nonexistent_certificate PASSED
tests/test_jobs.py::test_create_and_process_job_successfully PASSED
tests/test_jobs.py::test_get_nonexistent_job PASSED
tests/test_jobs.py::test_health_check_endpoints PASSED
tests/test_validation.py::test_validation_empty_recipient_list PASSED
tests/test_validation.py::test_validation_blank_course_name PASSED
tests/test_validation.py::test_validation_blank_recipient_name PASSED
tests/test_validation.py::test_validation_invalid_email PASSED
tests/test_validation.py::test_validation_missing_required_fields PASSED
======================== 12 passed in 0.10s ========================
```

---

## 📡 API Reference & Usage Examples

### 1. Submit Bulk Certificate Job
**`POST /jobs`** (HTTP 202 Accepted)

#### Request:
```bash
curl -X POST http://localhost:8000/jobs \
  -H "Content-Type: application/json" \
  -d '{
    "course_name": "Full Stack Cloud Architecture",
    "issue_date": "October 2026",
    "recipients": [
      {
        "name": "Jane Doe",
        "email": "jane.doe@example.com"
      },
      {
        "name": "John Smith",
        "email": "john.smith@example.com"
      }
    ]
  }'
```

#### Response:
```json
{
  "job_id": "766a505b-80df-44ea-8316-f089698d89f8",
  "status": "PENDING",
  "total_records": 2,
  "message": "Bulk certificate job submitted successfully. Processing in background."
}
```

---

### 2. Check Job Status & Progress
**`GET /jobs/{job_id}`** (HTTP 200 OK)

#### Request:
```bash
curl http://localhost:8000/jobs/766a505b-80df-44ea-8316-f089698d89f8
```

#### Response:
```json
{
  "id": "766a505b-80df-44ea-8316-f089698d89f8",
  "status": "COMPLETED",
  "total_records": 2,
  "successful_records": 2,
  "failed_records": 0,
  "created_at": "2026-10-07T13:30:00.000000Z",
  "completed_at": "2026-10-07T13:30:01.000000Z",
  "certificates": [
    {
      "id": "c1380928-89c5-472e-b6a9-8588ef11e2f9",
      "job_id": "766a505b-80df-44ea-8316-f089698d89f8",
      "recipient_name": "Jane Doe",
      "recipient_email": "jane.doe@example.com",
      "course_name": "Full Stack Cloud Architecture",
      "issue_date": "October 2026",
      "status": "GENERATED",
      "certificate_file_path": "/path/to/generated_certificates/job_id/cert_id.pdf",
      "error_message": null,
      "download_url": "http://localhost:8000/certificates/c1380928-89c5-472e-b6a9-8588ef11e2f9",
      "created_at": "2026-10-07T13:30:00.000000Z"
    }
  ]
}
```

---

### 3. Download Certificate PDF
**`GET /certificates/{certificate_id}`** (HTTP 200 OK, Binary `application/pdf`)

#### Request:
```bash
curl -O -J http://localhost:8000/certificates/c1380928-89c5-472e-b6a9-8588ef11e2f9
```
* Returns the generated PDF file stream with `Content-Disposition: attachment; filename="Certificate_Jane_Doe_c1380928.pdf"`.
* If generation is still pending: returns HTTP 400.
* If generation failed: returns HTTP 400 with the specific error explanation.

---

### 4. Get Certificate Metadata
**`GET /certificates/{certificate_id}/metadata`** (HTTP 200 OK)

Inspect recipient information, creation timestamp, and file status without downloading the binary payload.

---

## 🛡️ Individual Failure Handling Explained

A critical requirement of the assignment is that:
> **One failed certificate must NOT stop or abort the remaining valid certificates.**

### Implementation Mechanism:
1. When a job is submitted, all recipients are pre-registered in the relational database with status `PENDING`.
2. The asynchronous worker iterates over each recipient wrapped in an isolated `try/except` block:
   ```python
   for cert in certificates:
       try:
           pdf_path = generate_certificate_pdf(...)
           cert.status = CertificateStatus.GENERATED
           cert.certificate_file_path = pdf_path
           job.successful_records += 1
       except Exception as exc:
           cert.status = CertificateStatus.FAILED
           cert.error_message = str(exc)
           job.failed_records += 1
       db.commit()  # Real-time state persistence
   ```
3. If an individual generation fails:
   - Only that certificate is flagged `FAILED` with the exact cause stored in `error_message`.
   - The loop continues uninterrupted for all remaining recipients.
   - The job's `failed_records` counter is incremented, and status transitions to `COMPLETED` once all recipients have been processed.

---

## 💡 Key Design Decisions & Trade-offs

1. **FastAPI vs Django/Flask**:
   * *Decision*: FastAPI offers native asynchronous concurrency, automated OpenAPI documentation generation, and high throughput.
   * *Trade-off*: Lacks an out-of-the-box admin panel like Django, but is significantly lighter and faster for API microservices.

2. **SQLite + SQLAlchemy ORM**:
   * *Decision*: Zero-setup file-based relational storage that works seamlessly on any machine without requiring external database servers (Docker/PostgreSQL). Uses SQLAlchemy 2.0 ORM with typed mapping.
   * *Trade-off*: SQLite handles single-writer concurrency. For enterprise scale (thousands of simultaneous writes), swapping the connection string to PostgreSQL requires zero code changes.

3. **FastAPI `BackgroundTasks` vs Celery + Redis**:
   * *Decision*: Built directly into FastAPI without needing Redis or RabbitMQ daemons running in the background. Easy to run and test locally.
   * *Trade-off*: Tasks run in-process. For multi-node distributed scaling, the architecture can be easily adapted to a distributed message broker (Celery / ARQ / SQS).

4. **ReportLab Canvas PDF Generation**:
   * *Decision*: Standard, battle-tested Python PDF engine. Produces crisp, vector-based PDF certificates with precise millimeter/point positioning, dynamic text measurement, and clean typography.
