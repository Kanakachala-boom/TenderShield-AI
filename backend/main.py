from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from ocr_engine import extract_text_from_pdf
from nlp_engine import extract_rules
from evaluator import evaluate_bidder
from fraud_detector import detect_fraud
import shutil, os, json
import database

app = FastAPI(title="TenderShield AI", version="1.0.0")

# Enable CORS for React frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
ALLOWED_TYPES = ["application/pdf", "image/jpeg", "image/png", "application/octet-stream"]


@app.get("/")
def home():
    return {"message": "TenderShield AI Running 🚀", "version": "1.0.0"}


# ── Upload Tender: Extracts rules using OCR and NLP ────────────────
@app.post("/upload-tender/")
async def upload_tender(file: UploadFile = File(...)):
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(status_code=400, detail=f"Unsupported file type: {file.content_type}")

    safe_name = file.filename.replace(" ", "_")
    file_path = os.path.join(UPLOAD_FOLDER, safe_name)

    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # OCR Phase
        text  = extract_text_from_pdf(file_path)
        # NLP Rule Structuring Phase[cite: 3, 4]
        rules = extract_rules(text)

        # Database Integration (Upgrade #1)
        tender_id = database.save_tender(file.filename, json.dumps(rules))
        database.log_action(tender_id, "TENDER_UPLOADED", f"Extracted {len(rules)} rules via OCR/NLP.")

        return {
            "tender_id":    tender_id,
            "filename":     file.filename,
            "text_preview": text[:1500] + ("..." if len(text) > 1500 else ""), # Matches UI preview size
            "rules":        rules,
            "rules_count":  len(rules)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── Single Bidder Evaluation ──────────────────────────────────────────────────
@app.post("/evaluate-bidder/")
def evaluate(data: dict):
    bidder = data.get("bidder", {})
    rules  = data.get("rules",  [])
    if not bidder:
        raise HTTPException(status_code=400, detail="No bidder data provided")
    return evaluate_bidder(bidder, rules)


# ── Leaderboard: Ranks bidders and detects anomalies[cite: 3, 4] ───────────────
@app.post("/leaderboard/")
def leaderboard(data: dict):
    bidders = data.get("bidders", [])
    rules   = data.get("rules",   [])
    tender_id = data.get("tender_id")
    if not bidders:
        raise HTTPException(status_code=400, detail="No bidders provided")

    results = []
    for bidder in bidders:
        # Core Matching Engine
        result = evaluate_bidder(bidder, rules)
        # Risk & Anomaly Scoring Engine[cite: 4]
        fraud  = detect_fraud(bidder, rules)

        # Mapping status for React frontend 'statusColor' and 'statusBg'[cite: 3]
        status_map = {"eligible": "Qualified", "rejected": "Rejected", "review": "Review"}
        display_status = status_map.get(result["status"], result["status"].title())

        # Risk logic aligns with Frontend 'riskColor'[cite: 3]
        has_high = any(f.get("severity") == "high" for f in fraud.get("details", []))
        risk = "High" if (fraud.get("is_suspicious") and has_high) else \
               "Medium" if fraud.get("is_suspicious") else "Low"

        # Penalize score based on risk
        final_score = result.get("total_score", result.get("score", 0))
        if risk == "High":
            display_status = "Rejected"
            final_score = max(0, final_score - 50)
        elif risk == "Medium":
            final_score = max(0, final_score - 20)

        results.append({
            "name":       bidder.get("name", "Unknown"),
            "score":      round(final_score, 1),
            "experience": bidder.get("experience", 0),
            "status":     display_status,
            "details":    result.get("details", []),
            "risk":       risk,
            "flags":      fraud.get("flags", []),
            "confidence": min(95, int(result.get("score", 0))),
            "explanation": result.get("explanation", "")
        })

    # Ranking logic for the Leaderboard Tab[cite: 3]
    results.sort(
        key=lambda x: (x["status"] == "Qualified", x["score"], x["experience"]),
        reverse=True
    )

    # Database Integration (Upgrade #1)
    if tender_id:
        for res in results:
            database.save_bidder_result(tender_id, res)
        database.log_action(tender_id, "LEADERBOARD_GENERATED", f"Evaluated and ranked {len(bidders)} bidders.")

    return results


# ── Audit Trail API (Upgrade #2) ──────────────────────────────────────────────
@app.get("/audit/{tender_id}")
def get_audit_trail(tender_id: int):
    logs = database.get_audit_log(tender_id)
    if not logs:
        raise HTTPException(status_code=404, detail="No audit logs found for this tender.")
    return {"tender_id": tender_id, "audit_log": logs}


# ── Project History APIs (Phase 3) ────────────────────────────────────────────
@app.get("/tenders/")
def get_all_tenders():
    return database.get_all_tenders()

@app.get("/tenders/{tender_id}/bidders")
def get_bidders_for_tender(tender_id: int):
    return database.get_bidders_for_tender(tender_id)


# ── Bidder Document Parsing (Upgrade #4) ──────────────────────────────────────
@app.post("/upload-bidder/")
async def upload_bidder(file: UploadFile = File(...)):
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(status_code=400, detail=f"Unsupported file type: {file.content_type}")

    safe_name = file.filename.replace(" ", "_")
    file_path = os.path.join(UPLOAD_FOLDER, f"bidder_{safe_name}")

    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # 1. OCR the Bidder Document
        text = extract_text_from_pdf(file_path)
        
        # 2. Extract Bidder JSON using LLM (Upgrade #4)
        from nlp_engine import extract_bidder_info_llm
        bidder_data = extract_bidder_info_llm(text)
        
        # Ensure minimum fields
        if not bidder_data.get("name"):
            bidder_data["name"] = file.filename.split(".")[0]
        
        bidder_data["text_profile"] = text[:1000] # Save sample text for collusion detection

        return {
            "message": "Bidder document parsed successfully.",
            "bidder_data": bidder_data
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))