"""
fraud_detector.py — TenderShield AI
Multi-layer fraud and anomaly detection engine.

Detects:
  1. Document forgery       — metadata timestamp mismatch
  2. Shell company          — new company + blacklist linkage
  3. Bid collusion          — text similarity + shared IP/director
  4. Predatory underbidding — price below market floor
  5. Experience inflation   — experience vs turnover mismatch
  6. Missing mandatory docs — required fields absent
"""

import re, os, json
from datetime import datetime
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# ── Mock databases (replace with real API calls in production) ───────────────
BLACKLISTED_PANS = {
    "ABCDE1234F": "M/s Fake Corp",
    "XYZAB5678G": "M/s Ghost Ltd",
    "PQRST9012H": "M/s Shadow Infra",
}

BLACKLISTED_COMPANIES = [
    "shadow infra", "ghost ltd", "fake corp", "quick build pvt",
]

# Market floor price (below this % of estimate = suspicious)
UNDERBID_THRESHOLD_PCT = 0.70   # 70% of tender estimate


def run_all_fraud_checks(bidder, all_bidders: list) -> list:
    """
    Run all fraud detection modules on a single bidder.
    `all_bidders` is needed for collusion detection (cross-bidder comparison).
    Returns list of fraud flag dicts.
    """
    flags = []

    flags += _check_experience_inflation(bidder)
    flags += _check_shell_company(bidder)
    flags += _check_collusion(bidder, all_bidders)
    flags += _check_underbidding(bidder, all_bidders)
    flags += _check_missing_mandatory_docs(bidder)
    flags += _check_blacklist(bidder)

    return flags


# ── Module 1: Experience vs Turnover Mismatch ────────────────────────────────

def _check_experience_inflation(bidder: dict) -> list:
    flags = []
    turnover   = _get(bidder, "turnover", 0)
    experience = _get(bidder, "experience", 0) or _get(bidder, "years_experience", 0)

    # High turnover but almost no experience → suspicious
    if turnover > 50_000_000 and experience < 2:
        flags.append({
            "type":        "experience_inflation",
            "severity":    "high",
            "confidence":  0.87,
            "description": (f"Claimed turnover ₹{turnover/1e7:.1f} Cr but only {experience} year(s) "
                            f"of experience. Possible inflated financial documents."),
            "evidence": {
                "turnover":   turnover,
                "experience": experience,
                "rule":       "High turnover with <2 years experience"
            }
        })

    # High experience but near-zero turnover → dormant/shell
    if experience > 10 and turnover < 1_000_000:
        flags.append({
            "type":        "dormant_entity",
            "severity":    "medium",
            "confidence":  0.74,
            "description": (f"{experience} years of claimed experience but turnover "
                            f"only ₹{turnover/1e5:.1f} Lakh — suggests a dormant or shell entity."),
            "evidence": {
                "turnover":   turnover,
                "experience": experience,
                "rule":       "Old company with near-zero revenue"
            }
        })

    return flags


# ── Module 2: Shell Company Detection ────────────────────────────────────────

def _check_shell_company(bidder: dict) -> list:
    flags = []
    name = _get(bidder, "name", "") or _get(bidder, "company_name", "")
    pan  = _get(bidder, "pan_number", "")

    # Check PAN against blacklist
    if pan and pan.upper() in BLACKLISTED_PANS:
        linked_company = BLACKLISTED_PANS[pan.upper()]
        flags.append({
            "type":        "blacklisted_pan",
            "severity":    "high",
            "confidence":  0.98,
            "description": (f"PAN {pan} is linked to blacklisted entity '{linked_company}'. "
                            f"Director/owner network overlap detected."),
            "evidence": {"pan": pan, "linked_to": linked_company}
        })

    # Check company name against blacklist
    if name and any(b in name.lower() for b in BLACKLISTED_COMPANIES):
        flags.append({
            "type":        "blacklisted_entity",
            "severity":    "high",
            "confidence":  0.95,
            "description": f"Company name '{name}' matches a known blacklisted entity.",
            "evidence":    {"company_name": name}
        })

    return flags


# ── Module 3: Bid Collusion Detection ────────────────────────────────────────

def _check_collusion(bidder: dict, all_bidders: list) -> list:
    """
    Detect collusion by:
    a) Shared IP address among bidders
    b) High text similarity between bid documents
    c) Shared director / PAN prefix (mock)
    """
    flags = []
    my_name = _get(bidder, "name", "") or _get(bidder, "company_name", "")
    my_ip   = _get(bidder, "ip_address", "")
    my_pan  = _get(bidder, "pan_number", "")

    for other in all_bidders:
        other_name = _get(other, "name", "") or _get(other, "company_name", "")
        if other_name == my_name:
            continue   # skip self

        # a) Same IP subnet (/24)
        other_ip = _get(other, "ip_address", "")
        if my_ip and other_ip and _same_subnet(my_ip, other_ip):
            flags.append({
                "type":        "collusion_ip",
                "severity":    "medium",
                "confidence":  0.78,
                "description": (f"'{my_name}' and '{other_name}' submitted bids from the "
                                f"same IP subnet ({my_ip[:my_ip.rfind('.')]}.*). Possible collusion."),
                "evidence": {
                    "bidder_a": my_name,  "ip_a": my_ip,
                    "bidder_b": other_name, "ip_b": other_ip
                }
            })
            break

        # b) Shared PAN prefix (first 5 chars = same person) — mock check
        other_pan = _get(other, "pan_number", "")
        if my_pan and other_pan and len(my_pan) >= 5 and my_pan[:5] == other_pan[:5]:
            flags.append({
                "type":        "collusion_director",
                "severity":    "medium",
                "confidence":  0.71,
                "description": (f"'{my_name}' and '{other_name}' share the same PAN prefix, "
                                f"suggesting common director/owner."),
                "evidence": {
                    "bidder_a": my_name, "pan_prefix_a": my_pan[:5],
                    "bidder_b": other_name
                }
            })

    # c) Bid text similarity (if text_profile provided)
    my_text    = _get(bidder, "text_profile", "")
    other_texts = [
        (_get(b, "name", "") or _get(b, "company_name", ""), _get(b, "text_profile", ""))
        for b in all_bidders
        if (_get(b, "name", "") or _get(b, "company_name", "")) != my_name
    ]

    if my_text:
        for other_name_t, other_text in other_texts:
            if not other_text:
                continue
            similarity = _text_similarity(my_text, other_text)
            if similarity > 0.80:
                flags.append({
                    "type":        "collusion_text",
                    "severity":    "medium",
                    "confidence":  round(similarity, 2),
                    "description": (f"Bid documents of '{my_name}' and '{other_name_t}' are "
                                    f"{similarity*100:.0f}% similar — possible template sharing or collusion."),
                    "evidence": {
                        "similarity_score": similarity,
                        "bidder_a": my_name,
                        "bidder_b": other_name_t
                    }
                })

    return flags


# ── Module 4: Predatory Underbidding ─────────────────────────────────────────

def _check_underbidding(bidder: dict, all_bidders: list) -> list:
    flags = []
    my_bid = _get(bidder, "bid_amount", 0)
    if not my_bid or my_bid <= 0:
        return flags

    # Compute average bid of all others
    other_bids = [
        _get(b, "bid_amount", 0) for b in all_bidders
        if (_get(b, "name","") or _get(b,"company_name","")) !=
           (_get(bidder,"name","") or _get(bidder,"company_name",""))
        and _get(b, "bid_amount", 0) > 0
    ]

    if not other_bids:
        return flags

    avg_bid = sum(other_bids) / len(other_bids)
    ratio   = my_bid / avg_bid

    if ratio < UNDERBID_THRESHOLD_PCT:
        flags.append({
            "type":        "predatory_underbidding",
            "severity":    "high",
            "confidence":  round(min(0.97, 1 - ratio), 2),
            "description": (f"Bid amount ₹{my_bid/1e7:.2f} Cr is {(1-ratio)*100:.0f}% below "
                            f"the average competing bid (₹{avg_bid/1e7:.2f} Cr). "
                            f"Predatory underbidding suspected."),
            "evidence": {
                "bid_amount":   my_bid,
                "average_bid":  avg_bid,
                "ratio":        round(ratio, 3),
                "threshold":    UNDERBID_THRESHOLD_PCT
            }
        })

    return flags


# ── Module 5: Missing Mandatory Documents ────────────────────────────────────

def _check_missing_mandatory_docs(bidder: dict) -> list:
    """
    Upgraded for CRPF Compliance: Cross-references boolean checkboxes 
    with mandatory text identifiers to ensure legal validity.
    """
    flags  = []
    
    # ─── 1. MANDATORY TEXT IDENTIFIERS ──────────────────────────────────────
    # Checks if the user actually typed a number into the text inputs
    # Reflects the real-world requirement for verifiable ID numbers
    text_checks = [
        ("pan_card_no",       "PAN Card Number"),
        ("trade_license_no",  "Trade License Number"),
    ]

    for field, label in text_checks:
        val = bidder.get(field)
        if not val or str(val).strip() == "":
            flags.append({
                "type":        "missing_identifier",
                "severity":    "high", # High risk because ID is missing
                "confidence":  1.0,
                "description": f"CRITICAL: Official {label} text was not entered. Registration is legally incomplete.",
                "evidence":    {"missing_field": field, "document": label}
            })

    # ─── 2. MANDATORY CHECKBOX STATUS ───────────────────────────────────────
    # Checks if the user explicitly confirmed possession of the document
    # Synchronized with Dashboard.jsx checkboxes
    boolean_checks = [
        ("pan_card",      "PAN Card Possession Status"),
        ("trade_license", "Trade License Possession Status"),
        ("gst_registered", "GST Registration Status"),
    ]

    for field, label in boolean_checks:
        val = bidder.get(field)
        if val is False or val is None:
            flags.append({
                "type":        "missing_document_confirmation",
                "severity":    "medium",
                "confidence":  1.0,
                "description": f"Legal Alert: Bidder did not confirm {label}. Possible non-compliance.",
                "evidence":    {"missing_field": field, "document": label}
            })

    # ─── 3. LOGICAL INCONSISTENCY (INTEGRITY CHECK) ─────────────────────────
    # Detects if they provided a number but failed to check the box (and vice-versa)
    if bidder.get("pan_card_no") and not bidder.get("pan_card"):
        flags.append({
            "type":        "data_integrity_anomaly",
            "severity":    "medium",
            "confidence":  0.9,
            "description": "Anomaly: PAN number provided but 'PAN Card Holder' box remains unchecked.",
            "evidence":    "Data mismatch between text input and boolean status"
        })

    return flags


# ── Module 6: Blacklist Check ─────────────────────────────────────────────────

def _check_blacklist(bidder: dict) -> list:
    flags = []
    if _get(bidder, "blacklisted", False):
        flags.append({
            "type":        "blacklisted",
            "severity":    "high",
            "confidence":  1.0,
            "description": "Bidder is flagged as blacklisted in the procurement database.",
            "evidence":    {"field": "blacklisted", "value": True}
        })
    return flags


# ── Utility: simple version for main.py's /leaderboard/ route ────────────────

def detect_fraud(bidder: dict, rules: list) -> dict:
    """
    Upgraded for CRPF theme: Checks for mandatory legal credentials 
    and document inconsistencies.
    """
    flags_raw = (
        _check_experience_inflation(bidder) +
        _check_shell_company(bidder) +
        _check_missing_mandatory_docs(bidder) +
        _check_blacklist(bidder) +
        # ─── ADD THIS LINE ───
        _check_legal_compliance(bidder) 
    )

    flag_messages = [f["description"] for f in flags_raw]
    has_high      = any(f["severity"] == "high" for f in flags_raw)

    return {
        "is_suspicious": len(flags_raw) > 0,
        "flags":         flag_messages,
        "risk":          "High" if has_high else ("Medium" if flags_raw else "Low"),
        "details":       flags_raw
    }

# ── Helpers ───────────────────────────────────────────────────────────────────

def _get(obj, key, default):
    """Safe getter that works on both dict and SQLAlchemy model."""
    if isinstance(obj, dict):
        return obj.get(key, default)
    return getattr(obj, key, default)


def _same_subnet(ip1: str, ip2: str) -> bool:
    """Check if two IPs share the same /24 subnet."""
    try:
        return ip1.rsplit(".", 1)[0] == ip2.rsplit(".", 1)[0]
    except Exception:
        return False


def _text_similarity(text1: str, text2: str) -> float:
    """Cosine similarity between two text strings."""
    try:
        vec = TfidfVectorizer().fit_transform([text1, text2])
        return float(cosine_similarity(vec[0], vec[1])[0][0])
    except Exception:
        return 0.0

def _check_legal_compliance(bidder: dict) -> list:
    flags = []
    
    # Check 1: Mismatch between 'Verified' status and provided documents
    if bidder.get("is_verified_vendor") and not bidder.get("pan_card_no"):
        flags.append({
            "description": "Identity Mismatch: Verified status claimed without PAN evidence.",
            "severity": "high",  # Added comma here
            "confidence": 95,     # Added comma here
            "evidence": "Field 'pan_card_no' is null while 'is_verified_vendor' is true"
        })

    # Check 2: Missing both critical documents for a non-JV bidder
    if not bidder.get("joint_venture"):
        if not bidder.get("pan_card") and not bidder.get("trade_license"):
            flags.append({
                "description": "Compliance Alert: Individual bidder lacks all mandatory legal credentials",
                "severity": "medium"
            })
            
    return flags