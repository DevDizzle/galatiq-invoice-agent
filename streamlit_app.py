import streamlit as st
import os
import time
import json
import pandas as pd
import sqlite3
import uuid
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
1.  **Ingestion:** Grok 4.1 Fast (Reasoning & OCR)
2.  **Validation:** Inventory Check (SQLite)
3.  **Approval:** VP Persona Logic
""")

col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("Upload Invoice")
    uploaded_file = st.file_uploader("Choose an invoice file",
                                     type=["txt", "pdf"])

    if uploaded_file is not None:
        if st.button("Process Invoice", type="primary"):
            # Save uploaded file to a temporary location
            upload_dir = "data/uploads"
            os.makedirs(upload_dir, exist_ok=True)
            file_path = os.path.join(upload_dir,
                                     f"{uuid.uuid4()}_{uploaded_file.name}")

            with open(file_path, "wb") as f:
                f.write(uploaded_file.getbuffer())

            st.toast(f"Uploaded: {uploaded_file.name}")

            with st.spinner("Agents are working..."):
                try:
                    # Run the agent directly!
                    final_state = process_invoice_direct(file_path)
                    st.session_state.run_history.append(final_state)

                    # --- Result Display ---
                    outcome = (final_state.payment_status or
                               final_state.approval_status)

                    # Status Banner
                    if outcome in ["APPROVED", "success"]:
                        st.balloons()
                        st.success(f"### ✅ Approved: {outcome.upper()}")
                    else:
                        st.error(f"### ❌ Rejected: {outcome.upper()}")

                    # Layout with Tabs
                    tab1, tab2, tab3 = st.tabs(["📊 Executive Summary",
                                                "🧾 Invoice Data",
                                                "🛠️ System Trace"])

                    with tab1:
                        st.markdown("#### Decision Reasoning")
                        if final_state.approval_reasoning:
                            st.info(final_state.approval_reasoning,
                                    icon="🤔")
                        elif not final_state.validation_errors:
                            st.success("Automatic Approval (< $10k Threshold)",
                                       icon="🤖")

                        if final_state.validation_errors:
                            st.markdown("#### ⚠️ Blocking Issues")
                            for err in final_state.validation_errors:
                                st.warning(err, icon="🚫")

                    with tab2:
                        # Metrics Row
                        c1, c2, c3 = st.columns(3)
                        data = final_state.extracted_data
                        c1.metric("Vendor", data.vendor)
                        c2.metric("Amount", f"${data.amount:,.2f}")
                        c3.metric("Date", data.date)

                        # Line Items Table
                        st.markdown("#### Extracted Line Items")
                        if data.items:
                            # Convert list of Pydantic objects to dicts
                            items_data = [item.model_dump()
                                          for item in data.items]
                            df_items = pd.DataFrame(items_data)
                            st.dataframe(df_items, use_container_width=True,
                                         hide_index=True)
                        else:
                            st.caption("No line items found.")

                    with tab3:
                        st.markdown("#### Agent Execution Log")
                        for step in final_state.logs:
                            with st.expander(
                                f"{step.agent}: {step.input_summary}",
                                expanded=False
                            ):
                                st.markdown(f"**Decision:** `{step.decision}`")
                                if step.tool_calls:
                                    st.markdown("**Tool Calls:**")
                                    st.json(step.tool_calls)

                except Exception as e:
                    st.error(f"Workflow Failed: {e}")
                    import traceback
                    st.text(traceback.format_exc())

with col2:
    st.subheader("Session History")
    if st.button("Refresh Logs"):
        pass  # Reruns script

    if not st.session_state.run_history:
        st.info("No runs this session.")

    for state in reversed(st.session_state.run_history):
        outcome = state.payment_status or state.approval_status
        color = "green" if outcome in ["APPROVED", "success"] else "red"
        icon = "✅" if outcome in ["APPROVED", "success"] else "❌"

        with st.container(border=True):
            st.markdown(f"**{icon} {outcome.upper()}**")
            st.caption(f"{state.timestamp}")
            st.caption(f"ID: `{state.run_id}`")
            # Show summarized steps
            steps = [f"{log.agent}" for log in state.logs]
            st.text(" → ".join(steps))

# Sidebar for Mock DB status
with st.sidebar:
    st.header("📦 Mock Inventory")
    if os.path.exists("inventory.db"):
        conn = sqlite3.connect("inventory.db")
        df = pd.read_sql_query("SELECT * FROM inventory", conn)
        st.dataframe(df, hide_index=True, use_container_width=True)
        conn.close()
    else:
        st.warning("DB not initialized yet.")
