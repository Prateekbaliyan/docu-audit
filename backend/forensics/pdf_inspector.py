import re
import fitz # PyMuPDF
from typing import List, Dict, Any


SUSPICIOUS_EDITORS = [
    "photoshop", "illustrator", "canva", "sejda", "acrobat preflight",
    "gimp", "inkscape", "coreldraw", "pdf24", "ilovepdf", "smallpdf",
    "foxit phantom", "pdf-xchange", "nitro pdf", "pdf fill", "phantompdf"
]


class PDFInspector:
    """
    PDF Structural, Metadata, Revision, and Font Baseline Forensic Engine.
    Deeply inspects PDF internals using PyMuPDF and direct PDF stream analysis.
    """

    def analyze_bytes(self, pdf_bytes: bytes) -> Dict[str, Any]:
        """
        Parses raw PDF bytes and runs all structural and font audit routines.
        """
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        
        # 1. Metadata Audit
        meta = doc.metadata or {}
        creation_date = meta.get("creationDate", "")
        mod_date = meta.get("modDate", "")
        producer = meta.get("producer", "")
        creator = meta.get("creator", "")

        editor_flags = []
        combined_software = f"{producer} {creator}".lower()

        for editor in SUSPICIOUS_EDITORS:
            if editor in combined_software:
                editor_flags.append(editor.capitalize())

        # Check date modification mismatch
        date_modified_after_created = False
        if creation_date and mod_date and mod_date != creation_date:
            date_modified_after_created = True

        # 2. XMP Metadata & History Parse
        xmp_metadata = ""
        xmp_history_entries = []
        try:
            xmp_metadata = doc.get_xml_metadata() or ""
            if xmp_metadata:
                history_matches = re.findall(r'<stEvt:softwareAgent>(.*?)</stEvt:softwareAgent>', xmp_metadata)
                for agent in history_matches:
                    xmp_history_entries.append(agent.strip())
                    agent_lower = agent.lower()
                    for editor in SUSPICIOUS_EDITORS:
                        if editor in agent_lower and editor.capitalize() not in editor_flags:
                            editor_flags.append(editor.capitalize())
        except Exception:
            pass

        # 3. Incremental Update / Revision Parser
        # Count '%%EOF' occurrences in the raw PDF stream
        eof_matches = re.findall(rb'%%EOF', pdf_bytes)
        revision_count = len(eof_matches)
        has_incremental_updates = revision_count > 1

        # 4. Embedded Font & Baseline Alignment Audit
        font_anomalies = []
        page_font_boxes = []

        for page_num in range(len(doc)):
            page = doc[page_num]
            rect = page.rect # page dimensions in points
            page_w, page_h = rect.width, rect.height

            # Extract text blocks as dictionaries
            text_page = page.get_text("dict")
            blocks = text_page.get("blocks", [])

            # Extract all spans with text, font, bbox, origin
            spans = []
            for b in blocks:
                if b.get("type") == 0: # text block
                    for line in b.get("lines", []):
                        for span in line.get("spans", []):
                            spans.append(span)

            # Analyze consecutive spans and numeric tokens
            for i in range(len(spans)):
                curr = spans[i]
                curr_text = curr.get("text", "").strip()
                curr_font = curr.get("font", "")
                curr_size = curr.get("size", 0.0)
                curr_bbox = curr.get("bbox", (0, 0, 0, 0)) # (x0, y0, x1, y1)
                curr_origin = curr.get("origin", (0, 0)) # (x, y) baseline

                # Filter numeric strings or currency tokens (exclude single punctuation/symbols)
                is_numeric = bool(re.search(r'\d', curr_text)) and len(curr_text) > 1

                if is_numeric and i > 0:
                    prev = spans[i - 1]
                    prev_text = prev.get("text", "").strip()
                    prev_font = prev.get("font", "")
                    prev_size = prev.get("size", 0.0)
                    prev_bbox = prev.get("bbox", (0, 0, 0, 0))
                    prev_origin = prev.get("origin", (0, 0))

                    # Calculate horizontal proximity (same line/table row)
                    is_same_row = abs(curr_origin[1] - prev_origin[1]) < 6.0
                    
                    if is_same_row and bool(re.search(r'\d', prev_text)):
                        # Font mismatch check within continuous numeric sequence or row
                        font_family_diff = (curr_font != prev_font)
                        size_diff = abs(curr_size - prev_size) > 1.2
                        baseline_jump = abs(curr_origin[1] - prev_origin[1])

                        # Only flag font family diff if it's within a continuous digit sequence (e.g. "1" "6" "00")
                        is_digit_splice = font_family_diff and (prev_text[-1].isdigit() and curr_text[0].isdigit())

                        if (is_digit_splice or baseline_jump > 3.0 or size_diff):
                            anomaly_info = {
                                "page": page_num + 1,
                                "text": curr_text,
                                "prev_text": prev_text,
                                "font": curr_font,
                                "prev_font": prev_font,
                                "size": curr_size,
                                "prev_size": prev_size,
                                "baseline_jump_pt": round(baseline_jump, 2),
                                "bbox_pt": curr_bbox,
                                # Bounding box in normalized percent (0..100) for frontend rendering
                                "bbox_pct": [
                                    round((curr_bbox[0] / page_w) * 100, 2),
                                    round((curr_bbox[1] / page_h) * 100, 2),
                                    round(((curr_bbox[2] - curr_bbox[0]) / page_w) * 100, 2),
                                    round(((curr_bbox[3] - curr_bbox[1]) / page_h) * 100, 2)
                                ],
                                "reason": f"Font/Baseline discrepancy: '{curr_text}' ({curr_font}) vs '{prev_text}' ({prev_font})"
                            }
                            font_anomalies.append(anomaly_info)

                            page_font_boxes.append({
                                "x_pct": anomaly_info["bbox_pct"][0],
                                "y_pct": anomaly_info["bbox_pct"][1],
                                "w_pct": anomaly_info["bbox_pct"][2],
                                "h_pct": anomaly_info["bbox_pct"][3],
                                "text": curr_text,
                                "reason": anomaly_info["reason"]
                            })

        doc.close()

        # Risk signals summary
        is_suspicious = bool(
            editor_flags or
            has_incremental_updates or
            (len(font_anomalies) > 0)
        )

        return {
            "metadata": {
                "creation_date": creation_date,
                "mod_date": mod_date,
                "producer": producer,
                "creator": creator,
                "date_modified_after_created": date_modified_after_created
            },
            "editor_flags": editor_flags,
            "xmp_history": xmp_history_entries,
            "revision_count": revision_count,
            "has_incremental_updates": has_incremental_updates,
            "font_anomalies": font_anomalies,
            "font_anomaly_count": len(font_anomalies),
            "font_anomaly_boxes": page_font_boxes,
            "is_suspicious": is_suspicious
        }
