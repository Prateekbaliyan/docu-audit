# DocuAudit™ — Production-Grade Digital Document Forensics & Tampering Detection System

**DocuAudit** is an enterprise-grade digital document forensics and tampering detection web application. It performs automated multi-spectral vision analysis, structural PDF stream inspection, Error Level Analysis (ELA), Noise Print residual extraction, Copy-Move Forgery Detection (CMFD), and semantic ledger arithmetic verification on receipts, bank statements, invoices, and certificates.

---

## 🌟 Key Features & Forensic Modules

### 1. Error Level Analysis (ELA) & Compression Forensics (`ela.py`)
- Re-saves input document image / rasterized PDF pages at controlled JPEG quality levels (e.g. 95% and 90%).
- Measures absolute pixel-wise error: $\Delta I = |I_{\text{orig}} - I_{\text{resaved}}|$.
- Amplifies error signals by adaptive scaling factor ($15\times$) normalized to $[0, 255]$.
- Computes sliding window ($16 \times 16$) variance spikes and kurtosis to highlight foreign spliced patches.
- Generates base64 JET colormap heatmap overlay.

### 2. High-Pass Noise Residual & DCT Grid Misalignment (`noise_analysis.py`)
- **Noise Print Subtraction:** Applies median filter smoothing ($R = I - \text{Filter}(I)$) to isolate high-frequency scanner/sensor noise.
- Flags localized patches whose noise variance deviates by $> 2.5\sigma$ from the document noise floor (detecting cross-scanner splicing).
- **DCT 8x8 Grid Misalignment:** Measures harmonic gradient boundary shifts to catch cropped copy-paste regions pasted out of JPEG 8x8 block grid alignment.

### 3. PDF Structural, Metadata & Revision Diffing (`pdf_inspector.py`)
- **Metadata Audit:** Inspects `CreationDate`, `ModDate`, `Producer`, and `Creator`. Flags date anomalies and visual editor signatures (`Photoshop`, `Illustrator`, `Canva`, `Sejda`, `Acrobat Preflight`, `GIMP`, `PDF24`, etc.).
- **XMP History Parse:** Extracts `xmpMM:History` software agent trails.
- **Incremental Update / Revision Counter:** Scans raw byte streams for `%%EOF` markers to count post-generation save generations (detecting post-signature edits).
- **Embedded Font & Baseline Sanity:** Inspects text spans for single-digit or numeric table row font family switches, font subset tag mismatches, and vertical baseline alignment jumps $> 3.0\text{ pt}$.

### 4. Copy-Move Forgery Detection (CMFD) (`cmfd.py`)
- Extracts keypoint descriptors using OpenCV ORB.
- Performs FLANN / BFMatcher with KNN ($k=10$) and spatial distance filtering ($> 40\text{ px}$).
- Groups shift vectors $(\Delta x, \Delta y)$ using DBSCAN clustering to expose cloned visual elements (duplicated signatures, stamps, or copied numbers).
- Draws arrowed vector overlay lines connecting source and cloned target regions.

### 5. Semantic, Arithmetic & Tax Checksum Verification (`semantic_audit.py`)
- Parses line items, subtotal, tax/VAT, discount, and grand total.
- Flags ledger arithmetic mismatches if:
  $$\vert \text{Subtotal} + \text{Tax} - \text{Discount} - \text{Grand Total} \vert > 0.02$$
- Validates Indian GSTIN (Modulo 36 Luhn algorithm), PAN regex, US EIN, and IBAN formats.

### 6. Calibrated Risk Aggregator & PDF Report Generator (`aggregator.py`, `report.py`)
- Computes normalized **Tamper Probability Score** ($0\text{--}100\%$) and categorical ratings:
  - `CLEAN` ($0\text{--}24\%$)
  - `SUSPICIOUS` ($25\text{--}69\%$)
  - `CRITICAL_TAMPERED` ($70\text{--}100\%$)
- Calculates SHA-256 cryptographic hash badge for chain-of-custody verification.
- Generates downloadable forensic summary PDF report via `reportlab` and structured JSON evidence payloads.

### 7. Dual-Pane Synchronized Inspection Viewer (Frontend)
- Dual-pane canvas view with synchronized zoom and pan (mouse drag, wheel zoom, reset).
- Left Pane: Pristine Original Document.
- Right Pane: Forensic Layer Overlay with mode toggles (`[Normal]`, `[ELA Heatmap]`, `[Noise Print]`, `[Font & Baseline]`, `[Copy-Move Vectors]`).
- Interactive threshold/opacity slider.

---

## 🛠 Project Architecture

```text
Docu-audit/
├── backend/
│   ├── main.py                  # FastAPI Server & API Endpoints
│   ├── config.py                # Forensic threshold configuration
│   ├── forensics/               # Standalone typed forensic engines
│   │   ├── ela.py
│   │   ├── noise_analysis.py
│   │   ├── pdf_inspector.py
│   │   ├── cmfd.py
│   │   ├── semantic_audit.py
│   │   ├── aggregator.py
│   │   └── report.py
│   ├── samples/                 # Pre-generated sample documents
│   │   ├── sample_clean.pdf
│   │   ├── sample_tampered.pdf
│   │   └── generate_samples.py
│   └── tests/                   # Pytest test suite
│       ├── test_ela.py
│       ├── test_pdf_inspector.py
│       └── test_semantic_audit.py
├── frontend/
│   ├── src/
│   │   ├── app/
│   │   │   ├── page.tsx          # Main Dashboard
│   │   │   └── layout.tsx
│   │   ├── components/
│   │   │   ├── DualPaneViewer.tsx
│   │   │   ├── RiskGauge.tsx
│   │   │   ├── AnomalyChecklist.tsx
│   │   │   └── UploadZone.tsx
│   │   └── hooks/
│   │       └── useSynchronizedZoomPan.ts
└── README.md
```

---

## 🚀 Quick Start Guide

### 1. Backend Server Setup

```bash
# Navigate to project root
cd Docu-audit

# Activate virtual environment (Windows)
.\venv\Scripts\activate

# Run Pytest suite
python -m pytest backend/tests

# Launch FastAPI backend server on http://localhost:8000
uvicorn backend.main:app --host 127.0.0.1 --port 8000
```

### 2. Frontend Application Setup

```bash
# Navigate to frontend directory
cd Docu-audit/frontend

# Launch Next.js dev server on http://localhost:3000
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) in your browser.
