# Demo Script for Galatiq Invoice Processing Agent

## Demo 1: Valid Low-Value Invoice
Run: `python3 main.py --invoice_path data/invoice_valid_low.txt`
Expected: Extracts data, validates inventory, auto-approves (<$10k), mocks payment. Check run_logs.json.

## Demo 2: High-Value Invoice with Suspicious Patterns
Run: `python3 main.py --invoice_path data/invoice_high_suspicious.txt`
Expected: Extracts, validates, VP reflects and rejects. Logs rejection.

## Demo 3: Invalid Inventory Mismatch
Run: `python3 main.py --invoice_path data/invoice_invalid_stock.txt`
Expected: Loops for correction if extraction issue, else rejects on mismatch.

## Observability
After each run, inspect `run_logs.json` for step-by-step details.
