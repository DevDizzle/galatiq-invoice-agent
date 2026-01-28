# Galatiq Invoice Processing Agent

A local, multi-agent system powered by **xAI Grok-3** that automates invoice processing:
Ingestion (OCR/LLM) → Validation (Mock Inventory) → Approval (VP Persona) → Payment.

## 🚀 Features
*   **Multi-Agent Architecture:** Built with `langgraph`.
*   **Intelligent Extraction:** Uses Grok-3 for robust data parsing.
*   **Stateful Validation:** Checks line items against a local SQLite inventory.
*   **Reflective Approval:** "VP Agent" scrutinizes high-value invoices (> $10k).
*   **Web UI:** Includes a Streamlit dashboard for easy demoing.

## 🛠️ Setup

1.  **Install Dependencies:**
    ```bash
    pip install -r requirements.txt
    pip install streamlit  # For the Web UI
    ```

2.  **Environment Variables:**
    Create a `.env` file in the root:
    ```
    XAI_API_KEY=your_grok_api_key
    ```

## 🏃‍♂️ Usage

### Option 1: Web UI (Recommended)
Run the interactive dashboard:
```bash
streamlit run streamlit_app.py
```
Open your browser to `http://localhost:8501`. You can upload invoices and see the agents in action.

### Option 2: CLI
Run the agent manually on specific files:
```bash
python3 main.py --invoice_path data/invoice_valid_low.txt
```

For detailed demo instructions and architecture, refer to `docs/demo_script.md`.

## 📂 Mock Data
Test files are provided in `data/`:
*   `invoice_valid_low.txt`: Standard invoice, should be **APPROVED**.
*   `invoice_high_suspicious.txt`: >$10k, odd patterns, should be **REJECTED** by VP.
*   `invoice_invalid_stock.txt`: Requests items not in stock, should fail **VALIDATION**.

## 📊 Logging
Execution logs are saved to `run_logs.json`.
