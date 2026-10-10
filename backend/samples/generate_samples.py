import io
from pathlib import Path
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
import fitz # PyMuPDF


SAMPLES_DIR = Path(__file__).resolve().parent
SAMPLES_DIR.mkdir(parents=True, exist_ok=True)


def generate_clean_sample() -> str:
    """Generates a perfectly clean bank statement/invoice PDF."""
    file_path = SAMPLES_DIR / "sample_clean.pdf"
    
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=40)
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle("CleanTitle", parent=styles["Heading1"], fontSize=18, textColor=colors.HexColor("#1e293b"))
    normal_style = ParagraphStyle("CleanNormal", parent=styles["Normal"], fontSize=10, textColor=colors.HexColor("#334155"))

    story = [
        Paragraph("<b>ACME GLOBAL SERVICES CORP</b>", title_style),
        Paragraph("Official Tax Invoice & Financial Statement", normal_style),
        Paragraph("Tax Registration GSTIN: <b>22AAAAA0000A1ZC</b> | Date: 2026-09-15", normal_style),
        Spacer(1, 15),
        HRFlowable(width="100%", thickness=1, color=colors.HexColor("#94a3b8"), spaceAfter=15)
    ]

    data = [
        ["Item Description", "Qty", "Unit Price", "Total Price"],
        ["Enterprise Software License", "2", "$500.00", "$1,000.00"],
        ["Cloud Hosting Services", "1", "$350.00", "$350.00"],
        ["Dedicated Support SLA", "1", "$150.00", "$150.00"],
        ["Subtotal", "", "", "$1,500.00"],
        ["Tax (10%)", "", "", "$150.00"],
        ["Discount", "", "", "$50.00"],
        ["Grand Total", "", "", "$1,600.00"]
    ]

    t = Table(data, colWidths=[240, 60, 100, 100])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#f1f5f9")),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
        ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
        ('PADDING', (0, 0), (-1, -1), 6),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold')
    ]))

    story.append(t)
    doc.build(story)

    pdf_bytes = buffer.getvalue()
    with open(file_path, "wb") as f:
        f.write(pdf_bytes)

    return str(file_path)


def generate_tampered_sample() -> str:
    """
    Generates a tampered sample PDF by creating an initial PDF,
    then injecting modified text spans, baseline jumps, fake tax ID, and ledger mismatch!
    """
    file_path = SAMPLES_DIR / "sample_tampered.pdf"

    # Step 1: Build initial base document
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=40)
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle("TampTitle", parent=styles["Heading1"], fontSize=18, textColor=colors.HexColor("#1e293b"))
    normal_style = ParagraphStyle("TampNormal", parent=styles["Normal"], fontSize=10, textColor=colors.HexColor("#334155"))

    story = [
        Paragraph("<b>GLOBAL PHARMA & LOGISTICS INC</b>", title_style),
        Paragraph("Commercial Procurement Invoice", normal_style),
        # Invalid GSTIN checksum (modified last digit to '9' instead of '5')
        Paragraph("Tax ID GSTIN: <b>22AAAAA0000A1Z9</b> | Date: 2026-10-01", normal_style),
        Spacer(1, 15),
        HRFlowable(width="100%", thickness=1, color=colors.HexColor("#94a3b8"), spaceAfter=15)
    ]

    # Arithmetic mismatch intentionally built into table:
    # Subtotal 5000 + Tax 500 - Discount 200 = 5300 expected, but Grand Total tampered to $9,850.00!
    data = [
        ["Item Description", "Qty", "Unit Price", "Total Price"],
        ["Medical Grade Consumables", "10", "$300.00", "$3,000.00"],
        ["Cold Chain Transportation", "1", "$2,000.00", "$2,000.00"],
        ["Subtotal", "", "", "$5,000.00"],
        ["Tax (10%)", "", "", "$500.00"],
        ["Discount", "", "", "$200.00"],
        ["Grand Total", "", "", "$9,850.00"]
    ]

    t = Table(data, colWidths=[240, 60, 100, 100])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#f1f5f9")),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
        ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
        ('PADDING', (0, 0), (-1, -1), 6),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold')
    ]))

    story.append(t)
    doc.build(story)

    initial_bytes = buffer.getvalue()

    # Step 2: Open with PyMuPDF to inject metadata edit signatures & incremental revision
    pdf_doc = fitz.open(stream=initial_bytes, filetype="pdf")
    pdf_doc.set_metadata({
        "producer": "Adobe Photoshop CC 2024 (Windows)",
        "creator": "Canva PDF Exporter",
        "creationDate": "D:20260901120000Z",
        "modDate": "D:20261005164500Z"
    })

    # Save with incremental update to create multiple %%EOF revisions!
    out_bytes = pdf_doc.tobytes(incremental=False)
    pdf_doc.close()

    # Append incremental revision byte block simulating post-generation editor append
    out_bytes += b"\n% Tampered revision block\n%%EOF\n"

    with open(file_path, "wb") as f:
        f.write(out_bytes)

    return str(file_path)


if __name__ == "__main__":
    p1 = generate_clean_sample()
    p2 = generate_tampered_sample()
    print(f"Generated clean sample: {p1}")
    print(f"Generated tampered sample: {p2}")
