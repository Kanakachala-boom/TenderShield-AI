# TenderShield AI 🛡️
**AI-Based Tender Evaluation and Eligibility Analysis for Government Procurement**

TenderShield AI is a secure, explainable, and fully-auditable government procurement dashboard. It uses a combination of modern OCR and LLM natural language processing to automatically extract tender criteria, evaluate heterogeneous bidder documents, and present human-readable verdicts without ever relying on "black box" silent disqualifications.

## 🚀 Features
* **Secure CRPF Gateway:** Authenticated access portal for government officers.
* **Smart Document AI:** Ingests complex PDFs, scanned images, and tables using an advanced OCR/Vision pipeline.
* **Explainable Verdicts:** Provides a detailed rationale for every evaluation, explicitly highlighting exactly *why* a document passed or failed.
* **Human-in-the-Loop:** Automatically flags ambiguous cases as **"Need Manual Review"** rather than rejecting them.
* **Auditability Engine:** All evaluations, confidence scores, and rationales are hashed and stored permanently in a secure SQLite database (viewable in the *Project Archives* tab).

---

## 🛠️ Instructions to Run the Solution Locally

### Prerequisites
* Python 3.9+
* Node.js (v16+)
* npm

### Step 1: Clone or Extract the Source Code
Extract the `TenderShield-AI_SourceCode.zip` file into a local directory.

### Step 2: Start the Python Backend
1. Open a terminal and navigate to the root directory.
2. Create and activate a virtual environment (optional but recommended).
3. Install the required Python dependencies:
   ```bash
   pip install fastapi uvicorn pypdf2 ... (add your specific requirements here)
   ```
4. Start the backend server:
   ```bash
   cd backend
   python main.py
   # OR
   uvicorn main:app --reload --port 8000
   ```
   *The backend should now be running on `http://localhost:8000`*

### Step 3: Start the React Frontend
1. Open a **new** terminal window and navigate to the frontend directory:
   ```bash
   cd frontend/app
   ```
2. Install the Node modules:
   ```bash
   npm install
   ```
3. Start the React development server:
   ```bash
   npm start
   ```
   *The dashboard will automatically open in your browser at `http://localhost:3000`*

### Step 4: Accessing the Dashboard
1. On the login screen, enter the authorized credentials:
   * **Username:** `officer`
   * **Password:** `crpf`
2. You can now upload Tenders, run Evaluations, and view the Project Archives!

---
*Built for the Theme 3 Hackathon Challenge*
