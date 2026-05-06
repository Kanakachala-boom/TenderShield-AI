"""
nlp_engine.py — TenderShield AI
Extracts structured eligibility rules from raw tender text.
"""
import re, json, os

def extract_rules(text: str) -> list:
    rules = []
    focused_text = _focus_eligibility(text)

    # Layer 1: Specialized Regex Extraction
    rules.extend(_regex_extraction(focused_text))

    # Layer 2: LLM API for Complex Clauses
    llm_rules = _llm_extraction(focused_text)
    for cr in llm_rules:
        # Avoid duplicates and messy fields
        if not any(r["field"].lower() == cr["field"].lower() for r in rules):
            # Final safety check on LLM values
            val = cr.get("value")
            if isinstance(val, (int, float)) or (isinstance(val, str) and not val.startswith(('[', '{'))):
                rules.append(cr)

    # Standardize and fill metadata
    for i, rule in enumerate(rules, 1):
        rule.setdefault("rule_id", f"R{i:02d}")
        rule.setdefault("confidence", 0.95)
        rule.setdefault("weight", _default_weight(rule.get("category", "financial")))
        rule.setdefault("mandatory", True)

    return _deduplicate(rules)

def _regex_extraction(text: str) -> list:
    rules = []
    t = text.lower()

    # 1. Mandatory Licenses (PAN/Trade)
    if "pan" in t:
        rules.append({"field": "pan_card", "operator": "==", "value": True, "category": "legal", "source_clause": "PAN Card Submission Mandatory"})
    
    if "license" in t or "trade" in t:
        rules.append({"field": "trade_license", "operator": "==", "value": True, "category": "legal", "source_clause": "Valid Trade License Required"})

    # 2. Annual Turnover (Enhanced detection)
    turnover_match = re.search(r'(?:turnover|revenue).{0,80}?(?:rs\.?|inr|₹)\s*([\d,\.]+)\s*(cr(?:ore)?|lakh)', t)
    if turnover_match:
        val = _to_inr(turnover_match.group(1), turnover_match.group(2))
        rules.append({
            "field": "turnover", "operator": ">=", "value": int(val),
            "unit": "INR", "category": "financial", "source_clause": f"Min Turnover Requirement: {turnover_match.group(0)}"
        })

    # 3. Technical Experience
    exp_match = re.search(r'(\d+)\s*(?:years|yrs).{0,20}experience', t)
    exp_val = int(exp_match.group(1)) if exp_match else 5
    rules.append({
        "field": "experience", "operator": ">=", "value": exp_val, 
        "unit": "years", "category": "experience", "source_clause": "Technical Qualification: Minimum Experience"
    })

    # 4. Project Value (Largest single work)
    proj_match = re.search(r'(?:single|largest|similar).{0,50}work.{0,50}?(?:rs\.?|inr|₹)\s*([\d,\.]+)\s*(cr(?:ore)?|lakh)', t)
    if proj_match:
        val = _to_inr(proj_match.group(1), proj_match.group(2))
        rules.append({
            "field": "project_value", "operator": ">=", "value": int(val),
            "unit": "INR", "category": "technical", "source_clause": f"Single Largest Project: {proj_match.group(0)}"
        })

    # 5. ISO & GST Certifications
    if re.search(r'\biso\s*9001\b', t):
        rules.append({"field": "has_iso_9001", "operator": "==", "value": True, "category": "certification", "source_clause": "ISO 9001:2015 Certification Required"})
    
    if re.search(r'\bgst\b|\bgstin\b', t):
        rules.append({"field": "gst_registered", "operator": "==", "value": True, "category": "legal", "source_clause": "GST Registration Proof Required"})

    # 6. Debarment Check
    if re.search(r'\bblacklist(?:ed)?\b|\bdebarr?ed?\b', t):
        rules.append({"field": "blacklisted", "operator": "==", "value": False, "category": "legal", "source_clause": "Bidder must not be blacklisted/debarred"})

    return rules


def _focus_eligibility(text: str) -> str:
    t_lower = text.lower()
    markers = ["eligibility criteria", "pre-qualification", "tender notice", "qualification"]
    for marker in markers:
        if marker in t_lower:
            return text[text.lower().index(marker):][:4000]
    return text[:4000]

def _to_inr(amount_str: str, unit: str) -> float:
    amount_str = amount_str.replace(",", "")
    try:
        val = float(amount_str)
        unit = unit.lower()
        if "cr" in unit: return val * 10_000_000
        if "lakh" in unit: return val * 100_000
        return val
    except: return 0.0


def _llm_extraction(text: str) -> list:
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key: return []
    
    try:
        from google import genai
        client = genai.Client(api_key=api_key)
        prompt = f"""Extract at least 5 to 6 mandatory eligibility criteria from this tender document.
        Focus on: 1. Turnover, 2. Technical Experience, 3. Largest Single Project, 4. Mandatory Licenses (GST/PAN), 5. ISO Certs, 6. EMD Amount.
        
        Format strictly as a JSON list of objects with keys: field, operator (>=, ==), value, unit, category, source_clause.
        IMPORTANT: 'value' MUST be a single number (e.g. 5000000) or True/False. NEVER use lists, dictionaries, or ranges.
        
        Text: {text[:4000]}
        """
        response = client.models.generate_content(model='gemini-2.5-flash', contents=prompt)
        res_text = response.text.replace('```json', '').replace('```', '').strip()
        raw_rules = json.loads(res_text)
        
        clean_rules = []
        for r in raw_rules:
            val = r.get("value")
            # Ensure high quality rules with simple numeric/bool values
            if isinstance(val, (int, float, bool)) or (isinstance(val, str) and not val.strip().startswith(('[', '{'))):
                # Clean field names for UI
                field = r.get("field", "").lower().replace("minimum_", "").replace("min_", "")
                r["field"] = field
                clean_rules.append(r)
        return clean_rules
    except: return []

def extract_bidder_info_llm(text: str) -> dict:
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key: return {"error": "Set GEMINI_API_KEY"}
    try:
        from google import genai
        client = genai.Client(api_key=api_key)
        prompt = f"""
        Extract bidder information from the following text: {text[:4000]}
        
        Return a JSON object with these EXACT keys:
        - name: (String)
        - turnover: (Number, e.g. 150000000)
        - experience: (Number, years)
        - pan_card: (Boolean, true if PAN mentioned/verified)
        - trade_license: (Boolean, true if license mentioned/valid)
        - gst_registered: (Boolean, true if GST mentioned/active)
        - has_iso_9001: (Boolean, true if ISO 9001 mentioned)
        - blacklisted: (Boolean, false unless explicitly mentioned as blacklisted)
        
        Return ONLY the JSON object.
        """
        response = client.models.generate_content(model='gemini-2.5-flash', contents=prompt)
        res_text = response.text.replace('```json', '').replace('```', '').strip()
        return json.loads(res_text)
    except: return {}

def _default_weight(cat):
    return {"financial": 0.3, "experience": 0.3, "technical": 0.2, "legal": 0.2}.get(cat, 0.1)

def _deduplicate(rules):
    seen = set()
    unique = []
    for r in rules:
        key = (r["field"].lower(), str(r["value"]))
        if key not in seen:
            unique.append(r)
            seen.add(key)
    return unique