# app/main.py
import uvicorn
from fastapi import FastAPI
from pydantic import BaseModel
from .agent_workflow import compiled_workflow
from .memory_handler import update_rag_memory

class DisruptionRequest(BaseModel):
    scenario: str

app = FastAPI(title="Synapse Agent Core (Gemini)")

@app.post("/resolve")
async def resolve_disruption(request: DisruptionRequest):
    """Receives a disruption scenario and returns the final resolution."""
    inputs = {"disruption_scenario": request.scenario, "current_task_index": 0}
    final_state = {}
    
    async for event in compiled_workflow.astream(inputs):
        for key, value in event.items():
            print(f"--- Node '{key}' finished ---")
            final_state = value
            
    resolution = final_state.get("final_resolution", "Processing failed.")
    
    # If the workflow was successful, save the plan to memory
    if "failed" not in resolution.lower():
        successful_plan = final_state.get("plan")
        if successful_plan:
            # Convert the Pydantic model to a string for saving
            plan_str = f"Workflow: {successful_plan.workflow_type}, Steps: {successful_plan.steps}"
            update_rag_memory(plan_str, request.scenario)
            
    return {"resolution": resolution}
