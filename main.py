import argparse
from dotenv import load_dotenv
load_dotenv()  # noqa: E402

from langgraph.graph import StateGraph, END  # noqa: E402
from state import GlobalState  # noqa: E402
import tools  # noqa: E402
import utils  # noqa: E402
import agents  # noqa: E402


def build_graph():
    graph = StateGraph(GlobalState)

    graph.add_node("ingestion", agents.ingestion_agent)
    graph.add_node("validation", agents.validation_agent)
    graph.add_node("approval", agents.approval_agent)
    graph.add_node("payment", agents.payment_agent)

    graph.set_entry_point("ingestion")
    graph.add_edge("ingestion", "validation")

    def validation_router(state: GlobalState):
        error_text = "".join(state.validation_errors).lower()
        if state.validation_errors and "data format" in error_text:
            return "ingestion"
        elif state.validation_errors:
            return END
        return "approval"

    graph.add_conditional_edges("validation", validation_router,
                                {"ingestion": "ingestion",
                                 "approval": "approval", END: END})

    def approval_router(state: GlobalState):
        return "payment" if state.approval_status == "APPROVED" else END

    graph.add_conditional_edges("approval", approval_router,
                                {"payment": "payment", END: END})
    graph.add_edge("payment", END)

    return graph.compile()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--invoice_path", required=True)
    args = parser.parse_args()

    tools.setup_db()  # Re-init DB
    state = GlobalState(invoice_file_path=args.invoice_path)
    graph = build_graph()
    print("Starting graph execution...")
    try:
        final_state_dict = graph.invoke(state)
        final_state = GlobalState(**final_state_dict)
        utils.save_logs(final_state)
        outcome = final_state.payment_status or final_state.approval_status
        print(f"Final status: {outcome}")
    except Exception as e:
        print(f"Graph execution failed: {e}")
        import traceback
        traceback.print_exc()
