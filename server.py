from fastapi import FastAPI, UploadFile, File, BackgroundTasks, HTTPException
from pydantic import BaseModel
import shutil
import os
import uuid
from typing import Dict, Optional
from dotenv import load_dotenv

# Load env vars
load_dotenv()

# Import core logic
# We assume server.py is in the root directory alongside main.py
from main import build_graph
from state import GlobalState
import utils
import tools

app = FastAPI()

# In-memory storage for prototype
# key: run_id, value: GlobalState
SESSIONS: Dict[str, GlobalState] = {}

class ProcessRequest(BaseModel):
    run_id: str

@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    run_id = str(uuid.uuid4())
    upload_dir = "data/uploads"
    os.makedirs(upload_dir, exist_ok=True)
    file_path = os.path.join(upload_dir, f"{run_id}_{file.filename}")
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    # Initialize state
    state = GlobalState(invoice_file_path=file_path, run_id=run_id)
    SESSIONS[run_id] = state
    
    return {"run_id": run_id, "filename": file.filename}

def run_agent_background(run_id: str):
    if run_id not in SESSIONS:
        return
    
    print(f"Starting background process for {run_id}")
    state = SESSIONS[run_id]
    tools.setup_db() # Ensure DB is ready
    graph = build_graph()
    
    try:
        final_state_dict = graph.invoke(state)
        # Update the stored state with the result
        # Note: graph.invoke returns a dict representing the state
        SESSIONS[run_id] = GlobalState(**final_state_dict)
        utils.save_logs(SESSIONS[run_id])
    except Exception as e:
        print(f"Error in background process: {e}")
        import traceback
        traceback.print_exc()
        # Fail gracefully
        SESSIONS[run_id].approval_reasoning = f"System Error: {str(e)}"
        SESSIONS[run_id].approval_status = "REJECTED"

@app.post("/process")
async def process_invoice(request: ProcessRequest, background_tasks: BackgroundTasks):
    run_id = request.run_id
    if run_id not in SESSIONS:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Start the agent execution in the background
    background_tasks.add_task(run_agent_background, run_id)
    
    return {"status": "Processing started", "run_id": run_id}

@app.get("/status/{run_id}")
async def get_status(run_id: str):
    if run_id not in SESSIONS:
        raise HTTPException(status_code=404, detail="Session not found")
    
    state = SESSIONS[run_id]
    return state.model_dump()
