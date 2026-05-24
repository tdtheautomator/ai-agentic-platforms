"""
Calculate Affordability Tool

Calculates monthly repayment and debt-to-income ratio for a loan application.
"""

from tools.registry import register_tool


# Import CUSTOMERS from main module (will be injected at runtime)
def _get_customers():
    """Get customers list from main module."""
    from main import CUSTOMERS
    return CUSTOMERS


@register_tool
def calculate_affordability(customer_id: str, loan_amount: float, term_months: int) -> dict:
    """Calculate monthly repayment and debt-to-income ratio."""
    customers = _get_customers()
    c = next((x for x in customers if x["id"] == customer_id), None)
    if not c:
        return {"error": "Not found"}
    rate = 0.089  # 8.9% APR
    monthly_rate = rate / 12
    payment = loan_amount * (monthly_rate * (1 + monthly_rate)**term_months) / \
              ((1 + monthly_rate)**term_months - 1)
    dti = (payment / (c["income"] / 12)) * 100
    return {
        "monthly_payment": round(payment, 2),
        "total_repayable": round(payment * term_months, 2),
        "apr": f"{rate*100:.1f}%",
        "dti_ratio": round(dti, 1),
        "dti_pass": dti <= 43,
        "term_months": term_months,
    }
