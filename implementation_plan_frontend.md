# Frontend Upgrades for TenderShield AI

You already have an amazing React dashboard built out in `Dashboard.jsx`! However, it is not yet connected to the new powerful features we just added to the backend. 

Here is my plan to upgrade your `Dashboard.jsx`:

## 1. Connect the `tender_id` State
Currently, your frontend doesn't track the `tender_id`. 
*   **Upgrade**: We will add a `tenderId` state variable. When you upload a tender, we will save the ID returned by the backend. We will then pass this ID to the `/leaderboard/` endpoint so the backend knows which tender to save the bidder results to.

## 2. Implement the "Upload Bidder" Feature (AI Extraction)
Right now, you have to manually type in all the bidder details (Turnover, Experience, PAN, etc.) in the "Bidder Evaluation" tab. 
*   **Upgrade**: We will add a new **"Upload Bidder Document (AI Parse)"** button next to the manual form. When you upload a bidder's PDF, it will hit our new `/upload-bidder/` backend endpoint, use Gemini to extract all their details, and automatically fill out the form for you!

## 3. Real-Time Audit Log
Your Leaderboard tab currently has a hardcoded "Audit Transparency Log" with fake times.
*   **Upgrade**: We will add a `useEffect` or a refresh button to fetch the real, tamper-proof audit log from our new `/audit/{tender_id}` backend endpoint, displaying exactly what actions the AI took and when.

## 4. UI/UX Polish (Glassmorphism & Animations)
*   **Upgrade**: I will enhance the existing inline styles in `Dashboard.jsx` to make the UI pop even more, adding deeper glassmorphism effects (backdrop-filter blurs) and smoother hover transitions to match the premium "web app" requirements.

---

## User Review Required

> [!IMPORTANT]
> Please review this frontend upgrade plan. 
> Do you approve of these changes to `Dashboard.jsx`? Once you approve, I will apply the code!
