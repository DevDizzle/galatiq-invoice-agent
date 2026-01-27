# Galatiq Invoice Processing Agent

A local multi-agent prototype for automating invoice processing using xAI Grok.

## Setup
1. Install dependencies: `pip install -r requirements.txt`
2. Set API key: `export XAI_API_KEY=your_xai_api_key`
3. Run: `python main.py --invoice_path path/to/invoice.pdf`

## Structure
- agents.py: Agent definitions
- tools.py: Mock tools and DB setup
- state.py: State models
- main.py: Entry point
- utils.py: Utilities like PDF parsing
- data/: Mock invoices

## CI/CD
GitHub Actions enabled for linting, testing, and Docker build/push on releases.
