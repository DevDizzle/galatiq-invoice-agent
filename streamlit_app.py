import streamlit as st
import os
import time
import json
import pandas as pd
import sqlite3
import uuid
import asyncio
from dotenv import load_dotenv

# Import core logic directly
from main import build_graph
from state import GlobalState
import tools
import utils

# Load environment variables
load_dotenv()

# Set page config
st.set_page_config(
    page_title="Galatiq Invoice Agent",
    page_icon="🧾",
    layout="wide"
)

# Initialize session state
if "run_history" not in st.session_state:
    st.session_state.run_history = []

def process_invoice_direct(file_path: str) -> GlobalState:
    """Runs the agent workflow directly in-process."""
    # Ensure DB is ready
    tools.setup_db()
    
    # Initialize State
    run_id = str(uuid.uuid4())
    state = GlobalState(invoice_file_path=file_path, run_id=run_id)
    
    # Build Graph
    graph = build_graph()
    
    # Execute
    # Note: This blocks the UI thread. For a production app we'd use a queue,
    # but for a demo this guarantees "it just works".
    final_state_dict = graph.invoke(state)
    final_state = GlobalState(**final_state_dict)
    
    # Save logs
    utils.save_logs(final_state)
    return final_state

# --- UI Layout ---

st.title("🤖 Galatiq Invoice Processing Agent")
st.markdown("""
**Architecture:** Monolithic Agent (Streamlit + LangGraph)
1.  **Ingestion:** Grok-3
2.  **Validation:** Inventory Check
3.  **Approval:** VP Logic
""")

col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("Upload Invoice")
    uploaded_file = st.file_uploader("Choose an invoice file", type=["txt", "pdf"])
    
    if uploaded_file is not None:
        if st.button("Process Invoice", type="primary"):
            # Save uploaded file to a temporary location
            upload_dir = "data/uploads"
            os.makedirs(upload_dir, exist_ok=True)
            file_path = os.path.join(upload_dir, f"{uuid.uuid4()}_{uploaded_file.name}")
            
            with open(file_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            
            st.success(f"Uploaded: {uploaded_file.name}")
            
            with st.spinner("Agents are working... (Ingesting -> Validating -> Approving)"):
                try:
                    # Run the agent directly!
                    final_state = process_invoice_direct(file_path)
                    st.session_state.run_history.append(final_state)
                    
                    # --- Result Display ---
                    outcome = final_state.payment_status or final_state.approval_status
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
                        st.json(final_state.extracted_data.model_dump())
                    with c2:
                        st.caption("Validation Errors")
                        if final_state.validation_errors:
                            st.error(final_state.validation_errors)
                        else:
                            st.success("No validation errors")

                    # Approval Details
                    if final_state.approval_reasoning:
                        st.info(f"**VP Reasoning:** {final_state.approval_reasoning}")

                    # Agent Trace Logs
                    st.subheader("Agent Execution Log")
                    for step in final_state.logs:
                        with st.expander(f"{step.agent}: {step.input_summary}", expanded=True):
                            st.write(f"**Decision:** {step.decision}")
                            if step.tool_calls:
                                st.write("**Tool Calls:**")
                                st.json(step.tool_calls)
                                
                except Exception as e:
                    st.error(f"Workflow Failed: {e}")
                    import traceback
                    st.text(traceback.format_exc())

with col2:
    st.subheader("Session History")
    if st.button("Refresh Logs"):
        pass # Reruns script
        
    if not st.session_state.run_history:
        st.info("No runs this session.")
    
    for state in reversed(st.session_state.run_history):
        outcome = state.payment_status or state.approval_status
        color = "green" if outcome in ["APPROVED", "success"] else "red"
        
        with st.container(border=True):
            st.markdown(f":{color}[**{outcome.upper()}**] - {state.timestamp}")
            st.caption(f"Run ID: {state.run_id}")
            # Show summarized steps
            steps = [f"{log.agent}" for log in state.logs]
            st.code(" -> ".join(steps))

# Sidebar for Mock DB status
with st.sidebar:
    st.header("📦 Inventory Status")
    if os.path.exists("inventory.db"):
        conn = sqlite3.connect("inventory.db")
        df = pd.read_sql_query("SELECT * FROM inventory", conn)
        st.dataframe(df, hide_index=True)
        conn.close()
    else:
        st.warning("DB not initialized yet.")
