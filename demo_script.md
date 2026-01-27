# Demo Script for Galatiq Invoice Processing Agent

## Demo 1: Valid Low-Value Invoice
Run: `python main.py --invoice_path data/invoice_valid_low.pdf`
Expected: Extracts data, validates inventory, auto-approves (<$10k), mocks payment. Check run_logs.json.

## Demo 2: High-Value Invoice with Suspicious Patterns
Run: `python main.py --invoice_path data/invoice_high_suspicious.pdf`
Expected: Extracts, validates, VP reflects and rejects. Logs rejection.

## Demo 3: Invalid Inventory Mismatch
Run: `python main.py --invoice_path data/invoice_invalid_stock.pdf`
Expected: Loops for correction if extraction issue, else rejects on mismatch.

## Observability
After each run, inspect `run_logs.json` for step-by-step details.
