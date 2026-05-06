"""
evaluator.py — TenderShield AI
Matching engine that compares bidder data against tender rules.
"""

def evaluate_bidder(bidder: dict, rules: list) -> dict:
    """
    Core scoring engine:
    1. Mandatory rules: if any fail, status = Rejected.
    2. Optional rules: contribute to weighted total_score.
    3. Rules use semantic aliasing (e.g. 'has_pan_card' maps to 'pan_card').
    """
    rejection_reasons = []
    mandatory_failed  = False
    details           = []
    
    # Initialize category accumulators for weighted scoring
    category_results = {
        "financial": [],
        "technical": [],
        "certification": [],
        "experience": [],
        "legal": []
    }
    
    for rule in rules:
        field = str(rule.get("field", "")).lower()
        operator = rule.get("operator", "==")
        required_val = rule.get("value")
        is_mandatory = rule.get("mandatory", False)
        category = str(rule.get("category", "technical")).lower()
        
        # Synonym mapping for LLM extracted fields vs Frontend Form checkboxes
        alias_map = {
            "has_pan_card": "pan_card",
            "has_license": "trade_license",
            "has_registration": "gst_registered",
            "has_certificate": "has_iso_9001"
        }
        lookup_field = alias_map.get(field, field)
        actual_val = bidder.get(lookup_field)
        
        passed = False
        rule_score = 0.0

        # Comparison Logic
        try:
            if operator == ">=":
                if float(actual_val or 0) >= float(required_val or 0):
                    passed = True
                    # Dynamic scoring: bonus for exceeding requirements
                    ratio = float(actual_val or 0) / (float(required_val or 0) or 1.0)
                    rule_score = min(1.2, ratio) # Max 20% bonus per rule
            elif operator == "==":
                if str(actual_val or "").lower() == str(required_val or "").lower():
                    passed = True
                    rule_score = 1.0
            else:
                # Default to equality for unknown operators
                if str(actual_val or "").lower() == str(required_val or "").lower():
                    passed = True
                    rule_score = 1.0
        except (ValueError, TypeError):
            passed = False
            rule_score = 0.0
        
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
        
        category_results[category].append(rule_score)

    # ─── CALCULATE WEIGHTED SCORE ───
    def get_avg(cat):
        items = category_results.get(cat, [])
        if not items: return 0.85 # Baseline 85% for categories with no specific rules
        return sum(items) / len(items)

    # Govt formula: Financial (30%) + Experience (20%) + Technical (15%) + Cert (15%) + Legal (20%)
    score = (
        (get_avg("financial") * 30) +
        (get_avg("experience") * 20) +
        (get_avg("technical") * 15) +
        (get_avg("certification") * 15) +
        (get_avg("legal") * 20)
    )
    
    score = min(100.0, score)

    return {
        "name": bidder.get("name", "Unknown"),
        "status": "Rejected" if mandatory_failed else "Qualified",
        "score": round(score, 2),
        "rejection_reasons": rejection_reasons,
        "details": details,
        "flags": rejection_reasons,
        "explanation": f"Evaluation based on {len(rules)} extracted tender rules."
    }