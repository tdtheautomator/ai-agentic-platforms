"""Pricing-related tools."""

from .registry import register_tool
from data import CUSTOMERS, PRODUCTS, PROMOTIONS, WAREHOUSES


@register_tool
def apply_promotions(customer_id: str, subtotal: float, category: str) -> dict:
    """Find and apply the best available promotion for the customer and cart."""
    c = next((x for x in CUSTOMERS if x["id"] == customer_id), None)
    tier = c["tier"] if c else "bronze"
    best_promo = None
    best_saving = 0.0
    for p in PROMOTIONS:
        if p["tier_required"] and p["tier_required"] != tier:
            continue
        if subtotal < p["min_order"]:
            continue
        if p["applies_to"] not in ("all", category):
            continue
        saving = (subtotal * p["value"] / 100) if p["type"] == "percent" else p["value"]
        if saving > best_saving:
            best_saving = saving
            best_promo = p
    return {
        "promo_code": best_promo["code"] if best_promo else None,
        "discount_type": best_promo["type"] if best_promo else None,
        "saving": round(best_saving, 2),
        "final_subtotal": round(subtotal - best_saving, 2),
        "customer_tier": tier,
    }


@register_tool
def calculate_shipping(warehouse: str, address_postcode: str, weight_kg: float, subtotal: float) -> dict:
    """Calculate shipping cost and delivery estimate based on warehouse and order weight."""
    wh = WAREHOUSES.get(warehouse, WAREHOUSES["LDN-EAST"])
    free_threshold = 50.0
    base_cost = 0.0 if subtotal >= free_threshold else (3.99 if weight_kg < 2 else 5.99)
    express_cost = 6.99
    heavy_surcharge = 4.00 if weight_kg > 10 else 0.0
    return {
        "warehouse": warehouse,
        "warehouse_name": wh["name"],
        "standard_cost": round(base_cost + heavy_surcharge, 2),
        "express_cost": round(express_cost + heavy_surcharge, 2),
        "free_shipping": subtotal >= free_threshold,
        "estimated_days": 2 if wh["next_day_eligible"] else 3,
        "dispatch_cutoff": wh["dispatch_cutoff"],
        "capacity_pct": wh["capacity_pct"],
    }
