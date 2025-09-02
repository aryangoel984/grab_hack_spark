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
    inputs = {"disruption_scenario": request.scenario}
    final_state = None
    async for event in compiled_workflow.astream(inputs):
        for key, value in event.items():
            print(f"--- Node '{key}' finished ---")
            final_state = value
            
    return {"resolution": f"Workflow finished. Final result: {final_state.get('task_result', 'N/A')}"}

# To run the app: uvicorn app.main:app --reload