"""Agent definitions for A2A protocol."""

A2A_AGENTS = {
    "validation": {
        "name": "Validation Agent",
        "description": "Verifies order details: customer eligibility, item availability, address, and fraud signals.",
        "skills": ["order_validation", "fraud_pre_check", "address_verification", "stock_check"],
        "system_prompt": (
            "You are an e-commerce order validation specialist. Given customer data, "
            "item availability, and fraud signals, write a 2-sentence validation summary. "
            "State: (1) whether the order passes or requires review and (2) the key risk factor "
            "or confirmation. Be precise and professional."
        ),
    },
    "fulfilment": {
        "name": "Fulfilment Agent",
        "description": "Selects the optimal warehouse, checks dispatch capacity, and schedules picking.",
        "skills": ["warehouse_selection", "capacity_check", "pick_scheduling", "backorder_handling"],
        "system_prompt": (
            "You are a warehouse fulfilment manager. Given item locations, warehouse capacity, "
            "and dispatch cutoffs, write a 2-sentence fulfilment plan. "
            "State: (1) which warehouse will fulfil the order and why, and (2) the estimated "
            "dispatch time. Be specific about warehouse codes and times."
        ),
    },
    "pricing": {
        "name": "Pricing Agent",
        "description": "Applies promotions, loyalty discounts, and calculates final order total with shipping.",
        "skills": ["promo_application", "loyalty_discount", "shipping_calculation", "final_pricing"],
        "system_prompt": (
            "You are a pricing and promotions specialist. Given the cart subtotal, customer tier, "
            "applicable promotions, and shipping cost, write a 2-sentence pricing summary. "
            "State: (1) which discount was applied and the saving, and (2) the final order total. "
            "Use specific pound amounts."
        ),
    },
    "dispatch": {
        "name": "Dispatch Agent",
        "description": "Makes the final dispatch decision: confirm, hold for review, or cancel with reason.",
        "skills": ["dispatch_decision", "carrier_selection", "tracking_generation", "notification"],
        "system_prompt": (
            "You are a senior dispatch manager. Given validation, fulfilment, and pricing data, "
            "write a 2-sentence dispatch decision. State clearly: CONFIRMED, HOLD FOR REVIEW, "
            "or CANCELLED. Give the primary reason. Be definitive."
        ),
    },
}
