import io
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable, KeepTogether
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle


class ForensicReportGenerator:
    """
    Generates printable PDF forensic audit reports using ReportLab.
    """

    @staticmethod
    def generate_pdf(audit_data: dict) -> bytes:
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            rightMargin=36,
            leftMargin=36,
            topMargin=36,
            bottomMargin=36
        )

        styles = getSampleStyleSheet()
        
        # Custom Paragraph Styles
        title_style = ParagraphStyle(
            "DocuAuditTitle",
            parent=styles["Heading1"],
            fontSize=22,
            leading=26,
            textColor=colors.HexColor("#0f172a"),
            fontName="Helvetica-Bold"
        )

        subtitle_style = ParagraphStyle(
            "DocuAuditSubtitle",
            parent=styles["Normal"],
            fontSize=10,
            leading=13,
            textColor=colors.HexColor("#64748b"),
            fontName="Helvetica"
        )

        section_heading = ParagraphStyle(
            "DocuAuditSection",
            parent=styles["Heading2"],
            fontSize=14,
            leading=18,
            textColor=colors.HexColor("#1e293b"),
            fontName="Helvetica-Bold",
            spaceAfter=6
        )

        normal_style = ParagraphStyle(
            "DocuAuditNormal",
            parent=styles["Normal"],
            fontSize=9,
            leading=12,
            textColor=colors.HexColor("#334155")
        )

        story = []

        # 1. Header Banner
        header_text = "<b>DocuAudit™ Digital Forensics & Tampering Analysis Report</b>"
        story.append(Paragraph(header_text, title_style))
        story.append(Spacer(1, 4))

        meta_info = f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')} | Document Chain-of-Custody Record"
        story.append(Paragraph(meta_info, subtitle_style))
        story.append(Spacer(1, 10))
        story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#3b82f6"), spaceAfter=15))

        # 2. Document Summary Box
        file_name = audit_data.get("file_name", "Document")
        sha256 = audit_data.get("sha256", "N/A")
        tamper_score = audit_data.get("tamper_score", 0)
        rating = audit_data.get("rating", "UNKNOWN")
        risk_label = audit_data.get("risk_label", "")

        # Score Color Coding
        if tamper_score >= 70:
            score_color = colors.HexColor("#ef4444") # Red
        elif tamper_score >= 25:
            score_color = colors.HexColor("#f59e0b") # Amber
        else:
            score_color = colors.HexColor("#10b981") # Green

        summary_table_data = [
            [
                Paragraph("<b>File Name:</b>", normal_style),
                Paragraph(file_name, normal_style),
                Paragraph("<b>Tamper Probability:</b>", normal_style),
                Paragraph(f"<font color='{score_color.hexval()}'><b>{tamper_score}% ({rating})</b></font>", normal_style)
            ],
            [
                Paragraph("<b>SHA-256 Hash:</b>", normal_style),
                Paragraph(f"<font size='7'>{sha256}</font>", normal_style),
                Paragraph("<b>Risk Status:</b>", normal_style),
                Paragraph(f"<b>{risk_label}</b>", normal_style)
            ]
        ]

        summary_table = Table(summary_table_data, colWidths=[100, 200, 110, 130])
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#f8fafc")),
            ('BOX', (0, 0), (-1, -1), 1, colors.HexColor("#cbd5e1")),
            ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
            ('PADDING', (0, 0), (-1, -1), 6),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE')
        ]))

        story.append(summary_table)
        story.append(Spacer(1, 15))

        # 3. Diagnostic Findings Breakdown
        story.append(Paragraph("Diagnostic Forensic Test Findings", section_heading))

        findings = audit_data.get("findings", [])
        findings_table_data = [
            [
                Paragraph("<b>Forensic Module</b>", normal_style),
                Paragraph("<b>Status</b>", normal_style),
                Paragraph("<b>Conf.</b>", normal_style),
                Paragraph("<b>Diagnostic Rationale & Evidence</b>", normal_style)
            ]
        ]

        for f in findings:
            is_flagged = f["status"] == "FLAGGED"
            status_text = f"<font color='red'><b>FLAGGED</b></font>" if is_flagged else f"<font color='green'><b>PASS</b></font>"
            
            findings_table_data.append([
                Paragraph(f["test"], normal_style),
                Paragraph(status_text, normal_style),
                Paragraph(f.get("confidence", "90%"), normal_style),
                Paragraph(f["rationale"], normal_style)
            ])

        findings_table = Table(findings_table_data, colWidths=[140, 65, 45, 290])
        findings_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#0f172a")),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
            ('PADDING', (0, 0), (-1, -1), 6),
            ('VALIGN', (0, 0), (-1, -1), 'TOP')
        ]))

        # Format header text row style
        header_p_style = ParagraphStyle("HeaderP", parent=normal_style, textColor=colors.white)
        findings_table_data[0] = [
            Paragraph("<b>Forensic Module</b>", header_p_style),
            Paragraph("<b>Status</b>", header_p_style),
            Paragraph("<b>Conf.</b>", header_p_style),
            Paragraph("<b>Diagnostic Rationale & Evidence</b>", header_p_style)
        ]

        story.append(findings_table)
        story.append(Spacer(1, 20))

        # 4. Certification & Signature Footer
        footer_data = [
            [
                Paragraph("<b>Forensic Officer Signature:</b> ___________________________", normal_style),
                Paragraph("<b>DocuAudit™ Automated Engine v2.4</b>", normal_style)
            ]
        ]
        footer_table = Table(footer_data, colWidths=[340, 200])
        footer_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE')
        ]))

        story.append(KeepTogether([
            HRFlowable(width="100%", thickness=1, color=colors.HexColor("#cbd5e1"), spaceAfter=10),
            footer_table
        ]))

        doc.build(story)
        pdf_bytes = buffer.getvalue()
        buffer.close()
        return pdf_bytes
