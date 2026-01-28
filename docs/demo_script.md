# Demo Script for Galatiq Invoice Processing Agent

## 1. System Architecture
**Pattern:** Client-Server / Agentic Workflow
**Components:**
*   **Frontend (Streamlit):** User Interface for uploading invoices and viewing real-time progress.
*   **Backend (FastAPI):** Hosts the Agentic Logic (LangGraph + Grok-3). Handles state and background processing.
*   **Database:** SQLite (Mock Inventory) + In-Memory Session State.

```mermaid
graph LR
    User[User] -->|Uploads PDF| Frontend(Streamlit)
    Frontend -->|POST /process| Backend(FastAPI)
    Backend -->|Orchestrates| Graph(LangGraph)
    Graph -->|Reasoning| Grok[xAI Grok-3]
    Graph -->|Validation| DB[(Mock Inventory)]
    Graph -->|Payment| PayAPI[Mock Payment]
```

## 2. Deployment
**Google Cloud Run (Production Mode):**
*   **Frontend:** `https://galatiq-frontend-2lshkth7qq-uc.a.run.app`
*   **Backend:** `https://galatiq-backend-2lshkth7qq-uc.a.run.app`

**Local Execution (Spec Compliant):**
*   Run `python3 main.py --invoice_path <file>` for a CLI-only experience.

## 3. Demo Scenarios

### Demo 1: Valid Low-Value Invoice (The Happy Path)
*   **Input:** `data/invoice_valid_low.txt`
*   **Expected:** Extracts data -> Validates Stock -> Auto-Approves (<$10k) -> Mocks Payment.
*   **Result:** `APPROVED` & `Paid`.

### Demo 2: High-Value Suspicious Invoice (The VP Persona)
*   **Input:** `data/invoice_high_suspicious.txt`
*   **Scenario:** Amount $15,000 (> $10k rule). Vendor "Unknown LLC". Future Date.
*   **Expected:** Ingestion OK -> Validation OK (if item exists) -> **Approval Agent Rejects**.
*   **VP Logic:** "Suspicious vendor, round numbers, bad date." -> **REJECTED**.

### Demo 3: Inventory Mismatch (Self-Correction/Failure)
*   **Input:** `data/invoice_invalid_stock.txt` (or `xfinity_bill.pdf` for real-world test)
*   **Scenario:** Requesting items not in DB (e.g., "ThingZ" or random PDF items).
*   **Expected:** Ingestion OK -> Validation **FAILS** (Item not found).
*   **Result:** **REJECTED** with specific error list.

## 4. Observability
*   All runs are logged to `run_logs.json` in structured JSON format.
*   The Streamlit UI parses these logs to show a step-by-step agent trace.

