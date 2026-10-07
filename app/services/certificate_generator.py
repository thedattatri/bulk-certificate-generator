import os
from datetime import datetime
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, landscape
from reportlab.pdfgen import canvas

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUTPUT_DIR = os.path.join(BASE_DIR, "generated_certificates")


def generate_certificate_pdf(
    certificate_id: str,
    job_id: str,
    recipient_name: str,
    course_name: str,
    issue_date: str,
    output_dir: str = OUTPUT_DIR
) -> str:
    """
    Generates an elegant, high-resolution PDF certificate for a recipient using ReportLab.
    
    Args:
        certificate_id: Unique UUID of the certificate
        job_id: ID of the parent generation job
        recipient_name: Name printed on the certificate
        course_name: Title of the completed course
        issue_date: Date string displayed on the certificate
        output_dir: Root directory for storing generated certificates
        
    Returns:
        Absolute file path of the generated PDF certificate.
        
    Raises:
        ValueError: If recipient_name is invalid or triggers a deliberate failure test.
        Exception: If PDF generation fails.
    """
    # Defensive check: if name contains trigger for testing failure handling or invalid chars
    if recipient_name.strip() == "FAIL_TRIGGER_TEST":
        raise ValueError("Simulated generator failure for testing individual failure handling.")

    job_output_dir = os.path.join(output_dir, job_id)
    os.makedirs(job_output_dir, exist_ok=True)

    file_path = os.path.join(job_output_dir, f"{certificate_id}.pdf")

    # Dimensions: Landscape Letter (792 x 612 pt)
    page_width, page_height = landscape(letter)

    c = canvas.Canvas(file_path, pagesize=landscape(letter))
    c.setTitle(f"Certificate - {recipient_name}")

    # Color Palette
    primary_color = colors.HexColor("#0f172a")     # Deep Slate / Navy
    accent_gold = colors.HexColor("#b45309")       # Rich Warm Gold
    secondary_text = colors.HexColor("#475569")    # Slate Muted
    border_color = colors.HexColor("#1e293b")      # Dark border
    inner_bg = colors.HexColor("#fdfdfb")          # Subtle cream white

    # 1. Background Fill
    c.setFillColor(inner_bg)
    c.rect(0, 0, page_width, page_height, fill=1, stroke=0)

    # 2. Outer Decorative Border
    c.setStrokeColor(border_color)
    c.setLineWidth(4)
    c.rect(20, 20, page_width - 40, page_height - 40, fill=0, stroke=1)

    # 3. Inner Gold Border
    c.setStrokeColor(accent_gold)
    c.setLineWidth(1.5)
    c.rect(28, 28, page_width - 56, page_height - 56, fill=0, stroke=1)

    # 4. Corner Ornaments (Classic L-brackets)
    corner_size = 18
    c.setStrokeColor(accent_gold)
    c.setLineWidth(2)
    # Top-Left
    c.line(34, page_height - 34, 34 + corner_size, page_height - 34)
    c.line(34, page_height - 34, 34, page_height - 34 - corner_size)
    # Top-Right
    c.line(page_width - 34, page_height - 34, page_width - 34 - corner_size, page_height - 34)
    c.line(page_width - 34, page_height - 34, page_width - 34, page_height - 34 - corner_size)
    # Bottom-Left
    c.line(34, 34, 34 + corner_size, 34)
    c.line(34, 34, 34, 34 + corner_size)
    # Bottom-Right
    c.line(page_width - 34, 34, page_width - 34 - corner_size, 34)
    c.line(page_width - 34, 34, page_width - 34, 34 + corner_size)

    # 5. Header / Organization Brand
    c.setFillColor(accent_gold)
    c.setFont("Helvetica-Bold", 12)
    c.drawCentredString(page_width / 2, page_height - 75, "GLOBAL RECOGNITION OF ACADEMIC EXCELLENCE")

    # 6. Main Certificate Title
    c.setFillColor(primary_color)
    c.setFont("Helvetica-Bold", 34)
    c.drawCentredString(page_width / 2, page_height - 130, "CERTIFICATE OF COMPLETION")

    # 7. Subheading
    c.setFillColor(secondary_text)
    c.setFont("Helvetica-Oblique", 14)
    c.drawCentredString(page_width / 2, page_height - 180, "This certificate is proudly awarded to")

    # 8. Recipient Name (Prominent Centered)
    c.setFillColor(primary_color)
    c.setFont("Helvetica-Bold", 30)
    c.drawCentredString(page_width / 2, page_height - 235, recipient_name)

    # Decorative underline beneath recipient name
    name_width = min(c.stringWidth(recipient_name, "Helvetica-Bold", 30) + 40, 480)
    c.setStrokeColor(accent_gold)
    c.setLineWidth(1.5)
    c.line(
        (page_width / 2) - (name_width / 2),
        page_height - 248,
        (page_width / 2) + (name_width / 2),
        page_height - 248
    )

    # 9. Course Completion Statement
    c.setFillColor(secondary_text)
    c.setFont("Helvetica", 14)
    c.drawCentredString(
        page_width / 2,
        page_height - 285,
        "for successfully fulfilling all curriculum requirements and standards in"
    )

    # 10. Course Title
    c.setFillColor(accent_gold)
    c.setFont("Helvetica-Bold", 20)
    c.drawCentredString(page_width / 2, page_height - 325, course_name)

    # 11. Footer Elements: Verification ID, Date, Signatures
    # Verification ID
    c.setFillColor(secondary_text)
    c.setFont("Helvetica", 9)
    c.drawString(60, 95, f"Certificate ID: {certificate_id}")
    c.drawString(60, 80, f"Issued Date: {issue_date}")
    c.drawString(60, 65, "Status: Authenticated & Verified")

    # Instructor / Authority Signature Line
    c.setStrokeColor(secondary_text)
    c.setLineWidth(1)
    c.line(page_width - 260, 95, page_width - 60, 95)
    c.setFont("Helvetica-Bold", 10)
    c.setFillColor(primary_color)
    c.drawCentredString(page_width - 160, 78, "Director of Certification")
    c.setFont("Helvetica-Oblique", 9)
    c.setFillColor(secondary_text)
    c.drawCentredString(page_width - 160, 65, "Authorized Signatory")

    # Save PDF
    c.showPage()
    c.save()

    return file_path
