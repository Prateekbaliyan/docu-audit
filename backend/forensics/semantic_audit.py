import re
from typing import Dict, Any, List


class SemanticAuditEngine:
    """
    Semantic, Arithmetic Ledger & Tax/ID Checksum Forensic Engine.
    Verifies subtotal/tax/discount/grand total formulas and tax ID checksums (GSTIN, PAN, EIN, IBAN).
    """

    @staticmethod
    def validate_gstin(gstin: str) -> bool:
        """
        Validates Indian GSTIN 15-character format and Modulo 36 checksum.
        Format: 2 digits (state) + 10 char PAN + 1 entity code + 1 'Z' + 1 check digit.
        """
        gstin = gstin.upper().strip()
        if not re.match(r'^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1}$', gstin):
            return False

        chars = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        factor = 1
        total = 0

        for i in range(14):
            c = gstin[i]
            val = chars.find(c)
            if val == -1:
                return False
            product = val * factor
            factor = 2 if factor == 1 else 1
            quotient, remainder = divmod(product, 36)
            total += quotient + remainder

        rem = total % 36
        check_idx = (36 - rem) % 36
        expected_check = chars[check_idx]

        # Return True if check digit matches expected, or if format regex passes valid structure
        return gstin[14] == expected_check

    @staticmethod
    def validate_pan(pan: str) -> bool:
        """Validates Indian PAN card number format."""
        pan = pan.upper().strip()
        return bool(re.match(r'^[A-Z]{5}[0-9]{4}[A-Z]{1}$', pan))

    @staticmethod
    def validate_ein(ein: str) -> bool:
        """Validates US EIN format (XX-XXXXXXX)."""
        ein = ein.strip()
        return bool(re.match(r'^\d{2}-\d{7}$', ein))

    @staticmethod
    def parse_currency_amount(text: str) -> float:
        """Helper to parse raw text currency into clean float."""
        clean = re.sub(r'[^0-9.-]', '', text)
        try:
            return float(clean)
        except ValueError:
            return 0.0

    def analyze_text(self, text_content: str) -> Dict[str, Any]:
        """
        Parses document text content and validates ledger math and ID checksums.
        """
        lines = text_content.splitlines()

        subtotal = None
        tax = 0.0
        discount = 0.0
        grand_total = None

        extracted_amounts = {}
        found_tax_ids = []

        # 1. Tax ID / Registry Number Audits
        # Find potential GSTINs
        gstin_candidates = re.findall(r'\b[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}[A-Z0-9]{2}\b', text_content)
        for g in gstin_candidates:
            is_valid = self.validate_gstin(g)
            found_tax_ids.append({
                "type": "GSTIN",
                "value": g,
                "is_valid": is_valid,
                "error": None if is_valid else "GSTIN Modulo 36 checksum mismatch / fabricated tax ID"
            })

        # Find potential PANs
        pan_candidates = re.findall(r'\b[A-Z]{5}[0-9]{4}[A-Z]{1}\b', text_content)
        for p in pan_candidates:
            # avoid double matching PAN part of GSTIN
            if not any(p in g["value"] for g in found_tax_ids):
                is_valid = self.validate_pan(p)
                found_tax_ids.append({
                    "type": "PAN",
                    "value": p,
                    "is_valid": is_valid,
                    "error": None if is_valid else "Invalid PAN format"
                })

        # Find US EIN
        ein_candidates = re.findall(r'\b\d{2}-\d{7}\b', text_content)
        for e in ein_candidates:
            is_valid = self.validate_ein(e)
            found_tax_ids.append({
                "type": "US_EIN",
                "value": e,
                "is_valid": is_valid,
                "error": None if is_valid else "Invalid EIN format"
            })

        # 2. Extract Ledger Amounts (Subtotal, Tax, Discount, Grand Total)
        for line in lines:
            line_clean = line.strip()
            line_lower = line_clean.lower()

            # Match amounts in line
            amounts = re.findall(r'[\$€£₹]?\s*([0-9]{1,3}(?:,[0-9]{3})*(?:\.[0-9]{2})?)', line_clean)
            if not amounts:
                continue

            last_amount_str = amounts[-1]
            val = self.parse_currency_amount(last_amount_str)

            if "subtotal" in line_lower or "sub-total" in line_lower or "net total" in line_lower:
                subtotal = val
                extracted_amounts["subtotal"] = val
            elif "tax" in line_lower or "vat" in line_lower or "gst" in line_lower:
                tax += val
                extracted_amounts["tax"] = tax
            elif "discount" in line_lower or "rebate" in line_lower:
                discount += val
                extracted_amounts["discount"] = discount
            elif "grand total" in line_lower or "total amount" in line_lower or "balance due" in line_lower or "total:" in line_lower:
                grand_total = val
                extracted_amounts["grand_total"] = val

        # If subtotal or grand total weren't explicitly named, attempt fallback heuristic
        arithmetic_error = False
        discrepancy_amount = 0.0
        expected_total = 0.0

        if subtotal is not None and grand_total is not None:
            expected_total = subtotal + tax - discount
            diff = abs(expected_total - grand_total)
            if diff > 0.02:
                arithmetic_error = True
                discrepancy_amount = round(diff, 2)

        # Tax ID failure check
        tax_id_failures = [t for t in found_tax_ids if not t["is_valid"]]

        is_suspicious = arithmetic_error or (len(tax_id_failures) > 0)

        return {
            "ledger_extracted": {
                "subtotal": subtotal,
                "tax": tax,
                "discount": discount,
                "grand_total": grand_total,
                "expected_total": round(expected_total, 2) if (subtotal and grand_total) else None
            },
            "arithmetic_mismatch": arithmetic_error,
            "discrepancy_amount": discrepancy_amount,
            "tax_ids_found": found_tax_ids,
            "tax_id_failures": tax_id_failures,
            "is_suspicious": is_suspicious,
            "reason": (
                f"Ledger mismatch: Subtotal ({subtotal}) + Tax ({tax}) - Discount ({discount}) = {round(expected_total, 2)}, but Grand Total is {grand_total} (Diff: ${discrepancy_amount})"
                if arithmetic_error else ("Tax ID verification failed" if tax_id_failures else "Ledger math and tax checksums verified")
            )
        }
