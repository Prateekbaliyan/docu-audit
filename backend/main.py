import io
import csv
import base64
from pathlib import Path
from typing import Optional, List
from PIL import Image
import fitz # PyMuPDF
from fastapi import FastAPI, File, UploadFile, HTTPException, Query, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response, JSONResponse, FileResponse
from pydantic import BaseModel

from backend.config import SAMPLES_DIR, ELA_QUALITY_1, ELA_SCALE_DEFAULT
from backend.forensics.ela import ErrorLevelAnalysis
from backend.forensics.noise_analysis import NoiseAnalysisEngine
from backend.forensics.pdf_inspector import PDFInspector
from backend.forensics.cmfd import CopyMoveForgeryDetector
from backend.forensics.semantic_audit import SemanticAuditEngine
from backend.forensics.exif_inspector import EXIFInspector
from backend.forensics.pdf_signature import PDFSignatureValidator
from backend.forensics.aggregator import ForensicAggregator
from backend.forensics.report import ForensicReportGenerator
from backend.samples.generate_samples import generate_clean_sample, generate_tampered_sample


app = FastAPI(
    title="DocuAudit Forensics API",
    description="Digital Document Forensics, EXIF, Signature, and Tampering Detection API",
    version="2.5.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup_event():
    clean_path = SAMPLES_DIR / "sample_clean.pdf"
    tampered_path = SAMPLES_DIR / "sample_tampered.pdf"
    if not clean_path.exists():
        generate_clean_sample()
    if not tampered_path.exists():
        generate_tampered_sample()


def convert_pdf_page_to_pil(doc: fitz.Document, page_num: int = 0, dpi: int = 150) -> Image.Image:
    """Renders a PDF page to a PIL Image at specified DPI."""
    page = doc[page_num]
    zoom = dpi / 72.0
    mat = fitz.Matrix(zoom, zoom)
    pix = page.get_pixmap(matrix=mat, alpha=False)
    img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
    return img


@app.get("/")
def read_root():
    return {
        "status": "online",
        "service": "DocuAudit Enterprise Forensic Engine",
        "version": "2.5.0"
    }


async def process_single_audit(file_bytes: bytes, filename: str, page_index: int = 0) -> dict:
    """Core internal auditor function for single and batch document processing."""
    filename_lower = filename.lower()
    pil_image: Optional[Image.Image] = None
    pdf_res = {}
    exif_res = {}
    sig_res = {}
    extracted_text = ""
    total_pages = 1
    is_pdf = False

    if filename_lower.endswith(".pdf") or file_bytes.startswith(b"%PDF"):
        is_pdf = True
        try:
            doc = fitz.open(stream=file_bytes, filetype="pdf")
            total_pages = len(doc)
            if page_index >= total_pages:
                page_index = 0

            # PDF Inspector & Digital Signature Validator
            pdf_inspector = PDFInspector()
            pdf_res = pdf_inspector.analyze_bytes(file_bytes)
            pdf_res["is_pdf"] = True

            sig_validator = PDFSignatureValidator()
            sig_res = sig_validator.analyze_bytes(file_bytes)

            pil_image = convert_pdf_page_to_pil(doc, page_index, dpi=150)

            text_lines = []
            for page in doc:
                text_lines.append(page.get_text("text"))
            extracted_text = "\n".join(text_lines)

            doc.close()
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Failed to parse PDF file: {str(e)}")
    else:
        # Image file (PNG, JPG, TIFF)
        try:
            pil_image = Image.open(io.BytesIO(file_bytes)).convert("RGB")
            pdf_res = {
                "is_pdf": False,
                "metadata": {},
                "editor_flags": [],
                "xmp_history": [],
                "revision_count": 1,
                "has_incremental_updates": False,
                "font_anomalies": [],
                "font_anomaly_count": 0,
                "font_anomaly_boxes": [],
                "is_suspicious": False
            }

            # EXIF Metadata Inspector
            exif_inspector = EXIFInspector()
            exif_res = exif_inspector.analyze_image(pil_image)

            try:
                import pytesseract
                extracted_text = pytesseract.image_to_string(pil_image)
            except Exception:
                extracted_text = ""
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Failed to load image file: {str(e)}")

    if pil_image is None:
        raise HTTPException(status_code=400, detail="Could not render document page for inspection.")

    buffer_orig = io.BytesIO()
    pil_image.save(buffer_orig, format="PNG")
    orig_b64 = base64.b64encode(buffer_orig.getvalue()).decode("utf-8")

    # Forensic Vision Engines
    ela_engine = ErrorLevelAnalysis(quality=ELA_QUALITY_1, scale=ELA_SCALE_DEFAULT)
    ela_res = ela_engine.analyze(pil_image)

    noise_engine = NoiseAnalysisEngine()
    noise_res = noise_engine.analyze(pil_image)

    cmfd_engine = CopyMoveForgeryDetector()
    cmfd_res = cmfd_engine.analyze(pil_image)

    semantic_engine = SemanticAuditEngine()
    semantic_res = semantic_engine.analyze_text(extracted_text)

    # Scoped vector PDF calibration
    if pdf_res and pdf_res.get("is_pdf") and not pdf_res.get("is_suspicious"):
        cmfd_res["cluster_count"] = 0
        cmfd_res["vector_count"] = 0
        cmfd_res["is_suspicious"] = False
        noise_res["anomaly_boxes"] = []
        noise_res["anomaly_count"] = 0
        noise_res["is_suspicious"] = False

    aggregator = ForensicAggregator()
    audit_summary = aggregator.aggregate(
        file_bytes=file_bytes,
        file_name=filename,
        ela_res=ela_res,
        noise_res=noise_res,
        pdf_res=pdf_res,
        cmfd_res=cmfd_res,
        semantic_res=semantic_res,
        exif_res=exif_res,
        sig_res=sig_res
    )

    return {
        "summary": audit_summary,
        "document": {
            "file_name": filename,
            "total_pages": total_pages,
            "current_page": page_index + 1,
            "original_image_b64": f"data:image/png;base64,{orig_b64}"
        },
        "layers": {
            "ela": ela_res,
            "noise": noise_res,
            "pdf_structure": pdf_res,
            "cmfd": cmfd_res,
            "semantic": semantic_res,
            "exif": exif_res,
            "signatures": sig_res
        }
    }


@app.post("/api/audit")
async def audit_document(
    file: UploadFile = File(...),
    page_index: int = Query(0, ge=0)
):
    """Main single-document forensic audit endpoint."""
    file_bytes = await file.read()
    filename = file.filename or "uploaded_document.pdf"
    if not file_bytes:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    return await process_single_audit(file_bytes, filename, page_index)


@app.post("/api/audit/batch")
async def audit_batch_documents(files: List[UploadFile] = File(...)):
    """Batch bulk document audit endpoint for processing multiple files simultaneously."""
    if not files:
        raise HTTPException(status_code=400, detail="No files provided in batch upload.")

    results = []
    for file in files:
        file_bytes = await file.read()
        filename = file.filename or "uploaded_document.pdf"
        try:
            res = await process_single_audit(file_bytes, filename, page_index=0)
            results.append(res)
        except Exception as e:
            results.append({
                "summary": {
                    "file_name": filename,
                    "sha256": "N/A",
                    "tamper_score": 0,
                    "rating": "ERROR",
                    "risk_label": f"Processing Error: {str(e)}",
                    "findings": [],
                    "flagged_count": 0,
                    "passed_count": 0
                }
            })

    return {"batch_count": len(results), "results": results}


class ExportRequest(BaseModel):
    summary: dict


@app.post("/api/export/pdf")
async def export_pdf_report(payload: ExportRequest):
    """Generates downloadable PDF Forensic Audit Report."""
    try:
        pdf_bytes = ForensicReportGenerator.generate_pdf(payload.summary)
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename=DocuAudit_Report_{payload.summary.get('file_name', 'Doc')}.pdf"
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate PDF report: {str(e)}")


class BatchCsvRequest(BaseModel):
    summaries: List[dict]


@app.post("/api/export/batch-csv")
async def export_batch_csv(payload: BatchCsvRequest):
    """Generates downloadable CSV Batch Audit Summary."""
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["File Name", "SHA-256 Hash", "Tamper Score (%)", "Risk Rating", "Risk Label", "Flagged Tests", "Passed Tests"])

    for s in payload.summaries:
        writer.writerow([
            s.get("file_name", ""),
            s.get("sha256", ""),
            s.get("tamper_score", 0),
            s.get("rating", ""),
            s.get("risk_label", ""),
            s.get("flagged_count", 0),
            s.get("passed_count", 0)
        ])

    csv_bytes = output.getvalue().encode("utf-8")
    return Response(
        content=csv_bytes,
        media_type="text/csv",
        headers={
            "Content-Disposition": "attachment; filename=DocuAudit_Batch_Summary.csv"
        }
    )


@app.get("/api/samples/{sample_type}")
async def get_sample_audit(sample_type: str):
    """Returns audit results for sample clean or tampered documents."""
    if sample_type == "clean":
        file_path = SAMPLES_DIR / "sample_clean.pdf"
        if not file_path.exists():
            generate_clean_sample()
    elif sample_type == "tampered":
        file_path = SAMPLES_DIR / "sample_tampered.pdf"
        if not file_path.exists():
            generate_tampered_sample()
    else:
        raise HTTPException(status_code=404, detail="Unknown sample type. Use 'clean' or 'tampered'.")

    with open(file_path, "rb") as f:
        file_bytes = f.read()

    filename = "Sample_Clean_Invoice.pdf" if sample_type == "clean" else "Tampered_Invoice_Modified_Amount.pdf"
    return await process_single_audit(file_bytes, filename, page_index=0)
