# Demo Video Script 🎬
*Use this script to record a flawless 2-minute video walkthrough of TenderShield AI. We recommend using a screen recorder like OBS Studio, Loom, or the built-in Windows screen recorder (Win + Alt + R).*

### Preparation Before You Hit Record:
1. Make sure your Python backend is running (`python main.py`).
2. Make sure your React frontend is running (`npm start`) and open in your browser on full screen.
3. Have your sample tender document ready in a folder.

---

### [0:00 - 0:15] Introduction & Secure Login
**Visual:** Show the `TenderShield AI - CRPF Gateway` login screen.
**Audio Script:**
> "Welcome to TenderShield AI. When dealing with government procurement, security is paramount. Our platform begins with a secure, authenticated gateway designed specifically for authorized officers. I'll log in now to access the dashboard."
**Action:** Type in `officer` / `crpf` and click Login.

### [0:15 - 0:45] Document AI & Uploading
**Visual:** You are now on the Document AI tab.
**Audio Script:**
> "Here is our main evaluation workspace. The biggest challenge in procurement is the sheer volume of heterogeneous documents—scanned certificates, typed PDFs, and tables. Our OCR and NLP pipeline handles all of this automatically. Let me upload a tender document."
**Action:** Click the upload box and select a sample tender PDF. Wait for the UI to update to the "Active Tender Document" persistent state.
**Audio Script:**
> "The system has now extracted and structured the eligibility criteria from the dense legal text."

### [0:45 - 1:20] Explainability & No Silent Disqualifications
**Visual:** Switch to the Evaluation tab and point out the results (or run an evaluation if you have dummy bidder documents).
**Audio Script:**
> "Here is where TenderShield shines. We designed this to be an *assistant*, not a black box. Notice that we don't just output 'Pass' or 'Fail'. For every single bidder, the AI generates a detailed rationale. It tells the officer exactly which document it read and what value it found."
**Action:** Hover your mouse over the "Need Manual Review" status or the rationale text.
**Audio Script:**
> "Crucially, if the OCR cannot read a blurry image, or the legal language is ambiguous, the system will *never* silently disqualify a bidder. It flags them as 'Need Manual Review', explicitly telling the human officer why it needs their eyes."

### [1:20 - 1:50] Total Auditability (Project Archives)
**Visual:** Click on the "Project Archives" tab in the top navigation.
**Audio Script:**
> "Finally, government procurement requires total auditability. Every evaluation we just ran was hashed for tamper-proofing and permanently logged into our relational database. Here in the Project Archives, an auditor can view a complete history of past tenders, see exactly who won, and trace the decision back to the exact officer who was logged in."

### [1:50 - 2:00] Conclusion
**Visual:** Click on one of the historical evaluations to show the beautiful glowing L1 Winner card.
**Audio Script:**
> "TenderShield AI brings trust, speed, and absolute transparency to government procurement. Thank you."
**Action:** Stop Recording.
