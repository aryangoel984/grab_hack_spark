import uvicorn
from fastapi import FastAPI
from pydantic import BaseModel
from typing import Optional
from .agent_workflow import compiled_workflow

# Pydantic models now match the rich data structure from the mock server.
class Customer(BaseModel):
    id: str
    name: str

class Merchant(BaseModel):
    id: str
    name: str
    status: Optional[str] = None

class DeliveryDetails(BaseModel):
    destination_address: str

class DisruptionRequest(BaseModel):
    order_id: str
    scenario_text: str
    customer: Customer
    merchant: Merchant
    driver: dict
    delivery_details: DeliveryDetails

app = FastAPI(title="Synapse Agent Core (Gemini)")

@app.post("/resolve")
async def resolve_disruption(request: DisruptionRequest):
    """Receives a rich disruption scenario and initiates the agent workflow."""
    
    # CRITICAL FIX: Pass the entire dictionary of request data into the workflow.
    inputs = {"request_data": request.dict()}
    
    final_state = {}
    async for event in compiled_workflow.astream(inputs):
        for key, value in event.items():
            print(f"--- Node '{key}' finished ---")
            final_state = value
            
    resolution = final_state.get("final_resolution", "Processing failed or no resolution found.")
    
    return {"resolution": resolution, "order_id": request.order_id}

