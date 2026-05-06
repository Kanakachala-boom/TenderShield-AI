"""
evaluator.py — TenderShield AI
Weighted bidder scoring engine with full explainability.
"""

# Category weights must sum to 1.0
CATEGORY_WEIGHTS = {
    "financial": 0.30,
    "experience": 0.30,
    "technical": 0.20,
    "certification": 0.10,
    "legal": 0.10,
}

def evaluate_bidder(bidder: dict, rules: list) -> dict:
    """
    Evaluates a bidder against extracted rules with categorized scoring.
    """
    details = []
    rejection_reasons = []
    mandatory_failed = False
    
    # ─── INITIALIZE CATEGORY TRACKING ───
    # This fixes the NameError by providing a place to store results
    category_results = {
        "financial": [],
        "technical": [],
        "certification": [],
        "experience": [],
        "legal": []
    }
    
    for rule in rules:
        field = rule.get("field")
        operator = rule.get("operator")
        required_val = rule.get("value")
        is_mandatory = rule.get("mandatory", False)
        category = rule.get("category", "technical").lower()
        
        actual_val = bidder.get(field)
        passed = False

        # Comparison Logic
        try:
            if operator == ">=":
                passed = float(actual_val or 0) >= float(required_val)
            elif operator == "==":
                passed = str(actual_val).lower() == str(required_val).lower()
        except (ValueError, TypeError):
            passed = False
        
        # Mandatory Blocking
        if is_mandatory and not passed:
            mandatory_failed = True
            rejection_reasons.append(f"LEGAL_NON_COMPLIANCE: Missing {field.upper()}")

        # Record result
        res_item = {"field": field, "passed": passed}
        details.append({**res_item, "actual": actual_val, "required": required_val})
        
        # Map unknown categories to 'technical' so they are not ignored
        if category not in category_results:
            category = "technical"
        
        category_results[category].append(passed)

    # ─── CALCULATE WEIGHTED SCORE ───
    def get_avg(cat):
        items = category_results.get(cat, [])
        if not items: return 1.0 # Default pass if no rules for category
        return sum(1 for x in items if x) / len(items)

    # Govt formula: Financial (30%) + Experience (20%) + Technical (15%) + Cert (15%) + Legal (20%)
    score = (
        (get_avg("financial") * 30) +
        (get_avg("experience") * 20) +
        (get_avg("technical") * 15) +
        (get_avg("certification") * 15) +
        (get_avg("legal") * 20)
    )

    return {
        "name": bidder.get("name"),
        "status": "Rejected" if mandatory_failed else "Qualified",
        "score": round(score, 2),
        "rejection_reasons": rejection_reasons,
        "details": details,
        "flags": rejection_reasons
    }