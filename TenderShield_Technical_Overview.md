# TenderShield AI: Technical System Overview
**Secure, AI-Driven Government Procurement & Audit Transparency**

## 1. System Architecture
TenderShield AI is built on a modern, asynchronous stack designed for high-stakes government procurement environments.
*   **Backend**: FastAPI (Python 3.10+) for high-performance, concurrent request handling.
*   **Frontend**: React.js with a premium, responsive dashboard interface.
*   **Intelligence**: Gemini 2.5 Flash LLM for complex legal text parsing.
*   **OCR Engine**: Tesseract OCR for digitizing legacy scanned PDF tenders.
*   **Database**: SQLite with a multi-table relational schema for tamper-evident audit logs.

## 2. The AI Pipeline
The core value of TenderShield is its three-stage intelligent pipeline:
1.  **Extraction (OCR)**: Scanned PDFs are converted into high-fidelity text blocks using localized Tesseract processing.
2.  **Structuring (NLP)**: The Gemini engine extracts mandatory eligibility criteria (Turnover, Experience, Certifications) into a JSON Rule Schema.
3.  **Validation (Matching Engine)**: A specialized Python logic engine compares bidder credentials against extracted rules in real-time.

## 3. Fraud & Collusion Detection Engine
TenderShield goes beyond simple evaluation by implementing a proactive Security Layer:
*   **Collusion Flags**: Detects if multiple bidders share identical addresses or suspicious document metadata.
*   **Turnover Verification**: Compares reported turnover against historical trends and flags inflation.
*   **Blacklist Integration**: Automatically cross-references bidders against a centralized debarment database.
*   **Risk Scoring**: Assigns a Low/Medium/High risk rating to every bidder based on document integrity.

## 4. Audit & Compliance
To ensure 100% transparency for government auditors, the system maintains:
*   **Action Logs**: Every click, upload, and evaluation is logged with a timestamp and actor ID.
*   **Project Archives**: Persistent storage of every tender ever evaluated, including the exact rules used at the time of decision.
*   **Transparency Reports**: Automated summaries of evaluation decisions that can be exported for official review.

---
**TenderShield AI: Bringing 100% Integrity to Public Procurement.**
