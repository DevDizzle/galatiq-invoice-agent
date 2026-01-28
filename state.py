from pydantic import BaseModel, Field
from typing import List, Dict, Literal
import uuid
from datetime import datetime


class InvoiceItem(BaseModel):
    item_name: str = ""
    quantity: int = 0


class ExtractedData(BaseModel):
    vendor: str = ""
    amount: float = 0.0
    date: str = ""  # ISO date
    items: List[InvoiceItem] = Field(default_factory=list)


class LogEntry(BaseModel):
    agent: str
    input_summary: str
    tool_calls: List[Dict]
    decision: str


class GlobalState(BaseModel):
    invoice_file_path: str = ""
    raw_text: str = ""
    extracted_data: ExtractedData = Field(default_factory=ExtractedData)
    validation_errors: List[str] = Field(default_factory=list)
    confidence_score: float = 0.0
    approval_status: Literal["PENDING", "APPROVED", "REJECTED",
                             "NEEDS_REVIEW"] = "PENDING"
    approval_reasoning: str = ""
    payment_status: str = ""
    logs: List[LogEntry] = Field(default_factory=list)
    retry_count: int = 0
    run_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: str = Field(default_factory=lambda:
                           datetime.utcnow().isoformat())
