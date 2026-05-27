"""Inventory-related tools."""

from .registry import register_tool
from data import PRODUCTS, POLICIES


@register_tool
def check_inventory(sku: str, qty: int = 1) -> dict:
    """Check real-time stock level and warehouse location for a product SKU."""
    p = next((x for x in PRODUCTS if x["sku"] == sku), None)
    if not p:
        return {"error": f"SKU {sku} not found"}
    return {
        "sku": sku,
        "name": p["name"],
        "price": p["price"],
        "stock": p["stock"],
        "available": p["stock"] >= qty,
        "can_backorder": p["stock"] == 0,
        "warehouse": p["warehouse"],
        "weight_kg": p["weight_kg"],
    }


@register_tool
def search_policies(query: str) -> list[str]:
    """Search the e-commerce policy knowledge base for relevant rules."""
    kw = query.lower()
    results = [p for p in POLICIES if any(w in p.lower() for w in kw.split())][:2]
    return results or ["Apply standard fulfilment policy."]
