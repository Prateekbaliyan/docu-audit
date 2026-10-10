from backend.samples.generate_samples import generate_clean_sample, generate_tampered_sample
from backend.forensics.pdf_inspector import PDFInspector


def test_pdf_inspector_clean():
    clean_path = generate_clean_sample()
    with open(clean_path, "rb") as f:
        pdf_bytes = f.read()

    inspector = PDFInspector()
    res = inspector.analyze_bytes(pdf_bytes)

    assert "metadata" in res
    assert res["has_incremental_updates"] is False
    assert len(res["editor_flags"]) == 0


def test_pdf_inspector_tampered():
    tampered_path = generate_tampered_sample()
    with open(tampered_path, "rb") as f:
        pdf_bytes = f.read()

    inspector = PDFInspector()
    res = inspector.analyze_bytes(pdf_bytes)

    assert "metadata" in res
    assert len(res["editor_flags"]) > 0 or res["has_incremental_updates"] is True
