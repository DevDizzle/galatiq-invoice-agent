import fitz  # pymupdf
import json
import os
from state import GlobalState, LogEntry

def parse_pdf(file_path: str) -> str:
    doc = fitz.open(file_path)
    text = ""
    for page in doc:
        text += page.get_text()
    doc.close()
    return text

def log_action(state: GlobalState, agent: str, input_summary: str, tool_calls: List[Dict], decision: str):
    state.logs.append(LogEntry(agent=agent, input_summary=input_summary, tool_calls=tool_calls, decision=decision))

def save_logs(state: GlobalState):
    log_data = {
        "run_id": state.run_id,
        "timestamp": state.timestamp,
        "steps": [log.dict() for log in state.logs],
        "final_outcome": state.payment_status or state.approval_status
    }
    with open('run_logs.json', 'a') as f:
        json.dump(log_data, f)
        f.write('\n')
