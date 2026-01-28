import os
import sqlite3
import difflib
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from state import GlobalState, ExtractedData
from tools import query_inventory, mock_payment
import utils

# Initialize ChatOpenAI for xAI (Grok)
llm = ChatOpenAI(
    api_key=os.getenv("XAI_API_KEY"),
    base_url="https://api.x.ai/v1",
    model="grok-3"
)


def ingestion_agent(state: GlobalState) -> GlobalState:
    print("-> Entering Ingestion Agent")

    # Check retries
    if state.retry_count > 3:
        error_msg = "Max retries exceeded for ingestion."
        print(f"!!! {error_msg}")
        state.validation_errors = [error_msg]
        utils.log_action(state, "IngestionAgent", "Retry limit hit", [],
                         error_msg)
        return state

    state.retry_count += 1

    if not state.raw_text:
        state.raw_text = utils.parse_pdf(state.invoice_file_path)

    prompt = ChatPromptTemplate.from_template(
        """You are an expert data entry specialist.
        Extract from text: {text}
        If previous error: {error}
        Output JSON: {{"vendor": str, "amount": float, "date": str,
        "items": [{{"item_name": str, "quantity": int}}]}}
        Confidence: 0.0-1.0"""
    )
    error = state.validation_errors[-1] if state.validation_errors else ""
    chain = prompt | llm | JsonOutputParser()
    try:
        response = chain.invoke({"text": state.raw_text, "error": error})
        state.extracted_data = ExtractedData(**response)
        state.confidence_score = response.get("confidence", 0.8)
        state.validation_errors = []  # Clear errors on success
        utils.log_action(state, "IngestionAgent",
                         f"Processed {state.invoice_file_path}", [],
                         "Extracted data")
    except Exception as e:
        print(f"!!! Ingestion Agent Failed: {e}")
        state.validation_errors = ["Data format error: " + str(e)]
        utils.log_action(state, "IngestionAgent",
                         f"Failed processing {state.invoice_file_path}", [],
                         str(e))
    return state


def validation_agent(state: GlobalState) -> GlobalState:
    print("-> Entering Validation Agent")
    errors = []
    tool_calls = []
    # If ingestion failed, skip validation logic but return state
    # so router can send back to ingestion
    if state.validation_errors:
        return state

    for item in state.extracted_data.items:
        stock = query_inventory(item.item_name)
        tool_calls.append({"tool": "query_inventory",
                           "input": item.item_name, "output": stock})
        if stock == -1:
            # Fuzzy match
            conn = sqlite3.connect('inventory.db')
            c = conn.cursor()
            c.execute("SELECT item_name FROM inventory")
            all_items = [row[0] for row in c.fetchall()]
            conn.close()
            matches = difflib.get_close_matches(item.item_name, all_items,
                                                n=1, cutoff=0.8)
            if matches:
                stock = query_inventory(matches[0])
                tool_calls.append({"tool": "fuzzy_query",
                                   "input": matches[0], "output": stock})

        if stock == -1 or item.quantity > stock:
            msg = 'Not found' if stock == -1 else 'Insufficient stock'
            errors.append(f"Item {item.item_name}: {msg}")

    state.validation_errors = errors
    if errors:
        state.approval_status = "REJECTED"
        state.approval_reasoning = f"Validation failed: {errors}"

    utils.log_action(state, "ValidationAgent", "Validated items",
                     tool_calls, "Errors: " + str(errors))
    return state


def approval_agent(state: GlobalState) -> GlobalState:
    print("-> Entering Approval Agent")
    if state.validation_errors:
        state.approval_status = "REJECTED"
        state.approval_reasoning = "Validation errors present"
        return state

    prompt = ChatPromptTemplate.from_template(
        """You are a Financial Controller VP.
        Invoice: Vendor {vendor}, Amount {amount}, Date {date}
        If amount < 10000, approve unless issues.
        If >=10000, reflect: vendor rep (simulate), suspicious
        (due yesterday? round nums?)
        Output JSON: {{"status": "APPROVED" or "REJECTED", "reasoning": str}}
        """
    )
    chain = prompt | llm | JsonOutputParser()
    response = chain.invoke(state.extracted_data.model_dump())

    state.approval_status = response["status"]
    state.approval_reasoning = response["reasoning"]
    utils.log_action(state, "ApprovalAgent", "Reviewed invoice", [],
                     f"Status: {state.approval_status}")
    return state


def payment_agent(state: GlobalState) -> GlobalState:
    print("-> Entering Payment Agent")
    if state.approval_status == "APPROVED":
        result = mock_payment(state.extracted_data.vendor,
                              state.extracted_data.amount)
        state.payment_status = result["status"]
        utils.log_action(state, "PaymentAgent", "Processed payment",
                         [{"tool": "mock_payment", "output": result}],
                         "Success")
    return state