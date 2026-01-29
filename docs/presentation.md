# Galatiq Invoice Agent - Live Demo Script

## 1. Introduction (1 min)
*   **The Problem:** Acme Corp losing $2M/yr on manual processing. Slow (5 days), Error-prone (30%).
*   **The Solution:** An Agentic AI System powered by **xAI Grok 4.1 Fast Reasoning**.
*   **Key Features:**
    *   **Autonomous:** Ingestion -> Validation -> Approval -> Payment.
    *   **Self-Correcting:** Retries on parse failures.
    *   **Smart:** "VP Persona" catches high-value fraud/errors.
    *   **Production-Ready:** Structured JSON logging, specific error handling.

## 2. Technical Architecture (2 min)
*   **Core Engine:** `LangGraph` for stateful multi-agent orchestration.
*   **Brain:** `Grok 4.1 Fast Reasoning` (via xAI API) for reasoning and extraction.
*   **Tools:**
    *   `PyMuPDF`: PDF Text Extraction.
    *   `SQLite`: Mock Inventory DB (Local).
    *   `Mock Payment`: Simulation function.
*   **Deployment (Bonus):**
    *   **CLI:** Standard local execution (Spec compliant).
    *   **Cloud:** Deployed Monolithic Container (Streamlit) on Google Cloud Run for stability.

## 3. Live Demo (5 min)

### Scenario A: The "Happy Path" (Efficiency)
*   **Input:** `invoice_valid_low.txt` (< $10k).
*   **Action:**
    1.  Agent Extracts: Vendor "TechSupplies", Items "GadgetX", "WidgetY".
    2.  Agent Validates: Stock exists.
    3.  Agent Approves: Amount < $10k (Auto-approval rule).
    4.  **Result:** Payment Processed immediately.

### Scenario B: The "VP Review" (Fraud Prevention)
*   **Input:** `INVOICE #999` (High value $15k, Suspicious).
*   **Action:**
    1.  Agent Extracts: $15,000 amount.
    2.  **VP Agent Triggered:** "Amount > $10k, let me think..."
    3.  **Reflection:** "Vendor 'Unknown LLC'? Due date in future? Round number?"
    4.  **Result:** **REJECTED**. Reasoning logged.

### Scenario C: The "Inventory Mismatch" (Data Integrity)
*   **Input:** `xfinity_bill.pdf` (Real-world PDF).
*   **Action:**
    1.  Agent Ingests: Extracts "My Xfinity Plan", "Internet".
    2.  Agent Validates: Queries DB.
    3.  **Result:** **REJECTED** (Items not in mock DB). Logs specific missing items.

## 4. Business Impact (1 min)
*   **Speed:** 5 days -> 10 seconds.
*   **Accuracy:** LLM reasoning + DB validation cuts error rate.
*   **Cost:** Significant reduction in manual labor overhead.

## 5. Q&A
*   *Open for questions on Architecture, Grok prompting, or Future roadmap (e.g., adding OCR).*
