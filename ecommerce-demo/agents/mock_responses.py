"""Mock responses for agents."""

from data import WAREHOUSES


def get_mock_response(agent_id: str, ctx: dict) -> str:
    """
    Generate mock response for an agent.
    
    Args:
        agent_id: Agent ID
        ctx: Context data
        
    Returns:
        Mock response text
    """
    name = ctx.get("customer_name", "the customer")
    tier = ctx.get("tier", "bronze")
    fraud = ctx.get("fraud_requires_review", False)
    total = ctx.get("order_total", 0)
    wh = ctx.get("warehouse", "LDN-EAST")
    saving = ctx.get("saving", 0)
    final = ctx.get("final_total", total)
    avail = ctx.get("all_available", True)

    if agent_id == "validation":
        if fraud:
            return (
                f"Order from {name} requires manual review before processing. "
                f"Fraud screening flagged {ctx.get('fraud_flags', 1)} signal(s): {ctx.get('fraud_flag_detail', 'unusual order pattern')}."
            )
        if not avail:
            return (
                f"Order validation failed: one or more items are out of stock. "
                f"Customer {name} has been notified; back-order option offered for eligible SKUs."
            )
        return (
            f"Order from {name} ({tier} tier) passes all validation checks. "
            f"All {ctx.get('item_count', 1)} item(s) are in stock and the shipping address is verified."
        )

    if agent_id == "fulfilment":
        wh_name = WAREHOUSES.get(wh, {}).get("name", wh)
        cap = WAREHOUSES.get(wh, {}).get("capacity_pct", 70)
        return (
            f"Order assigned to {wh_name} ({wh}) at {cap}% capacity — optimal warehouse for this order. "
            f"Picking scheduled within {'2 hours' if tier == 'gold' else '6 hours'}; dispatch cutoff {WAREHOUSES.get(wh, {}).get('dispatch_cutoff', '17:00')}."
        )

    if agent_id == "pricing":
        promo = ctx.get("promo_code", "SAVE10")
        return (
            f"Promotion {promo} applied: £{saving:.2f} discount on £{total:.2f} subtotal. "
            f"Final order total including shipping: £{final:.2f}."
        )

    if agent_id == "dispatch":
        if fraud:
            return (
                "HOLD FOR REVIEW: Fraud screening raised flags that require a human agent to verify. "
                "Order is paused; customer will receive an email requesting identity confirmation."
            )
        if not avail:
            return (
                "CANCELLED: Order cannot be fulfilled due to stock unavailability. "
                "Customer notified with full refund and alternative product suggestions."
            )
        return (
            f"CONFIRMED: Order for {name} dispatched from {WAREHOUSES.get(wh, {}).get('name', wh)}. "
            f"Tracking number generated; estimated delivery {WAREHOUSES.get(wh, {}).get('estimated_days', 2) if False else '2-3'} business days."
        )

    return f"[{agent_id}] Processing complete for order {ctx.get('order_id', 'N/A')}."
