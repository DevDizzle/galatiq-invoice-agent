import streamlit as st
import os
import time
import requests
import json
import pandas as pd
import sqlite3

# API Configuration
API_URL = os.getenv("API_URL", "http://localhost:8000")

# Set page config
st.set_page_config(
    page_title="Galatiq Invoice Agent",
    page_icon="🧾",
    layout="wide"
)

# Initialize session state
if "logs" not in st.session_state:
    st.session_state.logs = []

# --- UI Layout ---

st.title("🤖 Galatiq Invoice Processing Agent")
st.markdown(f"""
**Architecture:** Streamlit Frontend ↔ FastAPI Backend (`{API_URL}`)
1.  **Ingestion:** Grok-3 (Server-side)
2.  **Validation:** Inventory Check
3.  **Approval:** VP Logic
""")

col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("Upload Invoice")
    uploaded_file = st.file_uploader("Choose an invoice file",
                                     type=["txt", "pdf"])

    if uploaded_file is not None:
        if st.button("Process Invoice", type="primary"):
            with st.spinner("Uploading to Backend..."):
                try:
                    # 1. Upload
                    files = {"file": (uploaded_file.name,
                                      uploaded_file.getvalue(),
                                      uploaded_file.type)}
                    resp = requests.post(f"{API_URL}/upload", files=files)
                    resp.raise_for_status()
                    data = resp.json()
                    run_id = data["run_id"]
                    st.success(f"Uploaded! Session ID: `{run_id}`")

                    # 2. Trigger Process
                    resp = requests.post(f"{API_URL}/process",
                                         json={"run_id": run_id})
                    resp.raise_for_status()

                    # 3. Poll for Completion
                    status_placeholder = st.empty()
                    progress_bar = st.progress(0)

                    completed = False
                    final_state = {}

                    while not completed:
                        status_resp = requests.get(
                            f"{API_URL}/status/{run_id}")
                        status_resp.raise_for_status()
                        current_state = status_resp.json()

                        outcome = (current_state.get("payment_status") or
                                   current_state.get("approval_status"))
                        logs = current_state.get("logs", [])

                        # Update status
                        last_log = (logs[-1]["agent"] if logs
                                    else "Initializing...")
                        status_placeholder.info(f"Agent Action: {last_log}")
                        progress_bar.progress(min(len(logs) * 25, 100))

                        if outcome not in ["PENDING", ""]:
                            completed = True
                            final_state = current_state
                            progress_bar.progress(100)
                        else:
                            time.sleep(2)

                    # --- Result Display ---
                    outcome = (final_state.get("payment_status") or
                               final_state.get("approval_status"))
                    if outcome in ["APPROVED", "success"]:
                        st.balloons()
                        st.success(f"### Final Status: {outcome.upper()}")
                    else:
                        st.error(f"### Final Status: {outcome.upper()}")

                    # Display Details
                    st.divider()
                    st.subheader("Extraction & Validation")
                    c1, c2 = st.columns(2)
                    with c1:
                        st.caption("Extracted Data")
                        st.json(final_state.get("extracted_data"))
                    with c2:
                        st.caption("Validation Errors")
                        errors = final_state.get("validation_errors")
                        if errors:
                            st.error(errors)
                        else:
                            st.success("No validation errors")

                    # Approval Details
                    reasoning = final_state.get("approval_reasoning")
                    if reasoning:
                        st.info(f"**VP Reasoning:** {reasoning}")

                    # Agent Trace Logs
                    st.subheader("Agent Execution Log")
                    for step in final_state.get("logs", []):
                        with st.expander(f"{step['agent']}: "
                                         f"{step['input_summary']}",
                                         expanded=True):
                            st.write(f"**Decision:** {step['decision']}")
                            if step.get('tool_calls'):
                                st.write("**Tool Calls:**")
                                st.json(step['tool_calls'])

                except requests.exceptions.ConnectionError:
                    st.error("❌ Could not connect to Backend API. "
                             "Is `server.py` running?")
                except Exception as e:
                    st.error(f"Error: {e}")

with col2:
    st.subheader("Historical Run Logs")
    if st.button("Refresh Logs"):
        pass

    log_file = "run_logs.json"
    if os.path.exists(log_file):
        with open(log_file, "r") as f:
            lines = f.readlines()
            # Show last 5 logs, newest first
            for line in reversed(lines[-5:]):
                try:
                    log_entry = json.loads(line)
                    outcome = log_entry.get("final_outcome", "UNKNOWN")
                    color = ("green" if outcome in ["APPROVED", "success"]
                             else "red")

                    with st.container(border=True):
                        ts = log_entry.get('timestamp')
                        st.markdown(f":{color}[**{outcome.upper()}**] - {ts}")
                        st.caption(f"Run ID: {log_entry.get('run_id')}")
                        st.json(log_entry.get("steps"), expanded=False)
                except Exception:
                    pass
    else:
        st.write("No logs found yet.")

# Sidebar for Mock DB status (Direct DB read for prototype simplicity)
with st.sidebar:
    st.header("📦 Inventory Status")
    if os.path.exists("inventory.db"):
        conn = sqlite3.connect("inventory.db")
        df = pd.read_sql_query("SELECT * FROM inventory", conn)
        st.dataframe(df, hide_index=True)
        conn.close()
    else:
        st.warning("DB not initialized yet.")
