"""
Verify KYC Documents Tool

Checks KYC document status against the identity verification service.
"""

from tools.registry import register_tool


# Import CUSTOMERS from main module (will be injected at runtime)
def _get_customers():
    """Get customers list from main module."""
    from main import CUSTOMERS
    return CUSTOMERS


@register_tool
def verify_kyc_documents(customer_id: str) -> dict:
    """Check KYC document status against the identity verification service."""
    customers = _get_customers()
    c = next((x for x in customers if x["id"] == customer_id), None)
    if not c:
        return {"error": "Not found"}
    # HIGH risk customers have an expired address proof
    id_verified    = c["risk"] != "HIGH"
    address_valid  = c["risk"] != "HIGH"
    return {
        "customer_id": customer_id,
        "photo_id":      {"status": "verified", "expiry": "2027-08-14"},
        "proof_address": {"status": "verified" if address_valid else "expired",
                          "dated": "2024-11-01" if address_valid else "2022-03-15"},
        "kyc_pass": id_verified and address_valid,
        "biometric_match": id_verified,
    }
