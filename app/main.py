# app/main.py
import uvicorn
from fastapi import FastAPI
from pydantic import BaseModel
from .agent_workflow import compiled_workflow

class DisruptionRequest(BaseModel):
    scenario: str

app = FastAPI(title="Synapse Agent Core (Gemini)")

@app.post("/resolve")
async def resolve_disruption(request: DisruptionRequest):
    """Receives a disruption scenario and returns the final resolution."""
    inputs = {"disruption_scenario": request.scenario, "current_task_index": 0}
    final_state = {}
    
    # We must iterate through all events to get the final state
    async for event in compiled_workflow.astream(inputs):
        for key, value in event.items():
            print(f"--- Node '{key}' finished ---")
            # This continuously updates with the latest state
            final_state = value 
            
    # After the loop, final_state holds the true final state
    resolution = final_state.get("final_resolution", "Processing failed or no resolution found.")
    
    return {"resolution": resolution}

# To run the app: uvicorn app.main:app --reload