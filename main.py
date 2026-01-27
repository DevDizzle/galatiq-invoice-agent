import argparse
from langgraph.graph import StateGraph, END
from state import GlobalState
import tools
import utils
import agents

def build_graph():
    graph = StateGraph(GlobalState)
    
    graph.add_node("ingestion", agents.ingestion_agent)
    graph.add_node("validation", agents.validation_agent)
    graph.add_node("approval", agents.approval_agent)
    graph.add_node("payment", agents.payment_agent)
    
    graph.set_entry_point("ingestion")
    graph.add_edge("ingestion", "validation")
    
    def validation_router(state: GlobalState):
        if state.validation_errors and "data format" in "".join(state.validation_errors):  # Assume format error check
            return "ingestion"
        elif state.validation_errors:
            return END
        return "approval"
    
    graph.add_conditional_edges("validation", validation_router, {"ingestion": "ingestion", "approval": "approval", END: END})
    
    graph.add_edge("approval", "payment" if state.approval_status == "APPROVED" else END)  # Dynamic, but simplify
    graph.add_edge("payment", END)
    
    return graph.compile()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--invoice_path", required=True)
    args = parser.parse_args()
    
    tools.setup_db()  # Re-init DB
    state = GlobalState(invoice_file_path=args.invoice_path)
    graph = build_graph()
    final_state = graph.invoke(state)
    utils.save_logs(final_state)
    print(f"Final status: {final_state.payment_status or final_state.approval_status}")
