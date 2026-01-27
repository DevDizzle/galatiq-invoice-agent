# Technical Specification: Galatiq Invoice Processing Agent

## 1. Project Overview
**Goal:** Build a local, multi-agent prototype to automate invoice processing (Ingestion → Validation → Approval → Payment).
**Core Engine:** xAI Grok (via `xai-sdk` or OpenAI-compatible endpoint).
**Architecture:** Cyclic Multi-Agent Graph (State Machine).
**Constraint:** No external APIs (local simulation only), Python stack.

---

## 2. System Architecture
The system uses a **Graph-based Orchestration** (recommended: `langgraph`) to manage state and self-correction loops.

### 2.1 Global State Schema
The agents share a single state object (dictionary or Pydantic model) containing:
* `invoice_file_path` (str): Path to the input PDF/Text file.
* `raw_text` (str): Text extracted from the document.
* `extracted_data` (dict): Structured data (Vendor, Amount, Items, Date) parsed by Grok.
* `validation_errors` (list[str]): List of inventory mismatches or data quality issues.
* `confidence_score` (float): Grok's self-assessed confidence in extraction.
* `approval_status` (enum): `PENDING`, `APPROVED`, `REJECTED`, `NEEDS_REVIEW`.
* `approval_reasoning` (str): The VP Agent's critique for the decision.
* `payment_status` (str): Result from the mock payment API.
* `logs` (list[dict]): Structured log of all agent actions for observability.

### 2.2 Agent Workflow (The Graph)
1.  **START** → **Ingestion Agent**
2.  **Ingestion Agent** → **Validation Agent**
3.  **Validation Agent**:
    * *If valid* → **Approval Agent**
    * *If invalid (data format)* → **Ingestion Agent** (Loop: Retry with feedback)
    * *If invalid (inventory mismatch)* → **End** (Log rejection)
4.  **Approval Agent**:
    * *If approved* → **Payment Agent**
    * *If rejected* → **End** (Log rejection)
5.  **Payment Agent** → **End**

---

## 3. Technology Stack Requirements
* **Language:** Python 3.10+
* **LLM Provider:** xAI API (Model: `grok-2-1212` or `grok-beta` for reasoning).
* **Orchestration:** `langgraph` (preferred for loops) or `crewai`.
* **PDF Parsing:** `pymupdf` (fitz) or `pdfplumber`.
* **Database:** `sqlite3` (standard library).
* **Environment:** Local execution only.

---

## 4. Agent Specifications

### 4.1 Ingestion Agent
**Role:** OCR/Text Extractor & Structurer.
**Input:** PDF File Path.
**Tools:** `read_file`, `parse_pdf`.
**LLM Instruction:**
* You are an expert data entry specialist.
* Extract `Vendor`, `Total Amount`, `Invoice Date`, and `Line Items` (Item Name, Quantity).
* **Self-Correction:** If previous extraction failed (present in State), analyze the error message and try a different parsing strategy or "look harder" at the specific text region.
* **Output:** JSON object adhering to the `Invoice` schema.

### 4.2 Validation Agent
**Role:** Inventory Manager & Rule Enforcer.
**Input:** Extracted `Invoice` JSON.
**Tools:** `query_inventory(item_name)`.
**LLM Instruction:**
* Iterate through every line item in the invoice.
* Call `query_inventory` for each item.
* **Logic:**
    * Check if item exists.
    * Check if `Quantity <= Stock`.
    * *Fuzzy Matching:* If item not found, reason if it's a typo (e.g., "GadgetX" vs "Gadget X") and retry query.
* **Output:** Update `validation_errors` list.

### 4.3 Approval Agent (The "VP")
**Role:** Financial Controller.
**Input:** Validated Invoice Data + Validation Results.
**LLM Instruction:**
* **Threshold Rule:** If Amount < $10,000, auto-approve (unless validation errors exist).
* **High Value Logic:** If Amount >= $10,000, perform a "Reflection" step:
    * Analyze the vendor reputation (simulate knowledge).
    * Check for suspicious patterns (e.g., "Due: yesterday", round numbers).
    * Draft a brief "internal monologue" weighing pros/cons.
* **Output:** `APPROVED` or `REJECTED` with a `reason`.

### 4.4 Payment Agent
**Role:** Transaction Processor.
**Input:** Approved Invoice.
**Tools:** `mock_payment(vendor, amount)`.
**Logic:**
* Only runs if `approval_status == APPROVED`.
* Calls the mock API.
* Logs the transaction ID or failure message.

---

## 5. Tool Definitions (Mock Interfaces)

### `tools.py` Specification
1.  **`query_inventory(item_name: str) -> int`**
    * Connect to the local SQLite DB (schema provided in prompt).
    * Return stock count or `-1` if item not found.
    * *Developer Note:* Ensure DB is re-initialized on every run to ensure consistent testing.

2.  **`mock_payment(vendor: str, amount: float) -> dict`**
    * Print: `"[MOCK PAY] Processing payment of ${amount} to {vendor}..."`
    * Return: `{"status": "success", "transaction_id": "..."}`.

---

## 6. Observability & Logging
* **Requirement:** Create a structured JSON log file (`run_logs.json`) appended after every execution.
* **Log Structure:**
    * `run_id`: UUID.
    * `timestamp`: ISO8601.
    * `steps`: Array of agent actions.
        * `agent`: Name (e.g., "ValidationAgent").
        * `input`: Summary of input.
        * `tool_calls`: List of tools used and their raw outputs.
        * `decision`: Final output of the agent.
    * `final_outcome`: Success/Failure.

---

## 7. Deliverables Structure
The project should be organized as follows for the final ZIP submission:

project_root/
├── agents.py           # Class/Function definitions for each Agent
├── tools.py            # SQLite setup, mock inventory, mock payment
├── state.py            # Pydantic models for Graph State & Schemas
├── main.py             # Entry point (CLI argument parsing, Graph execution)
├── utils.py            # PDF parsing, Logger setup
├── requirements.txt    # xai-sdk, langgraph, pymupdf
├── README.md           # Setup instructions
├── demo_script.md      # As requested by prompt
└── data/               # Folder for the 3 mock invoices

## 8. Implementation Roadmap (24h Sprint)
1.  **Hour 0-2 (Foundation):** Setup `tools.py` (SQLite) and `utils.py` (PDF text extraction). Verify `xai-sdk` connection.
2.  **Hour 2-6 (Core Agents):** Implement `Ingestion` and `Validation` agents using Grok. Test tool calling for inventory checks.
3.  **Hour 6-10 (Orchestration):** Wire up `langgraph`. Implement the retry loop for validation failures.
4.  **Hour 10-12 (Refinement):** Add the "VP" reflection logic for high-value invoices.
5.  **Hour 12-14 (Polish):** Implement JSON logging. Handle the "Messy" and "Invalid" edge cases robustly.
6.  **Hour 14+:** Write `demo_script.md` and prepare the CLI presentation.

---

## 9. xAI Specific Integration Notes
* **Client Initialization:**
    Use standard OpenAI-compatible initialization for broader library support if needed, or native SDK.
    `client = xai_sdk.Client(api_key=...)`
* **Model Selection:**
    Use `grok-beta` or `grok-2-1212` for the agents. These models have strong reasoning capabilities required for the "VP" persona.
* **System Prompts:**
    Grok responds well to clear persona definitions. Ensure every agent `system_message` starts with "You are [Role]..." and explicitly defines the output format (JSON preferred).