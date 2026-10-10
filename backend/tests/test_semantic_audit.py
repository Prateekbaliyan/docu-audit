from backend.forensics.semantic_audit import SemanticAuditEngine


def test_gstin_checksum():
    engine = SemanticAuditEngine()
    # Valid GSTIN format & checksum
    valid_gstin = "22AAAAA0000A1ZC"
    invalid_gstin = "22AAAAA0000A1Z9"

    assert engine.validate_gstin(valid_gstin) is True
    assert engine.validate_gstin(invalid_gstin) is False


def test_ledger_arithmetic():
    engine = SemanticAuditEngine()
    
    clean_text = """
    ACME SERVICES
    Subtotal: $1,000.00
    Tax: $100.00
    Discount: $50.00
    Grand Total: $1,050.00
    """
    res_clean = engine.analyze_text(clean_text)
    assert res_clean["arithmetic_mismatch"] is False

    tampered_text = """
    ACME SERVICES
    Subtotal: $1,000.00
    Tax: $100.00
    Discount: $50.00
    Grand Total: $9,500.00
    """
    res_tampered = engine.analyze_text(tampered_text)
    assert res_tampered["arithmetic_mismatch"] is True
    assert res_tampered["discrepancy_amount"] > 0
