from fastapi import FastAPI, Query
from pydantic import BaseModel
from typing import Optional

# Create the FastAPI application instance
app = FastAPI(title="Mock Grab Backend")

# --- Define Pydantic models for expected request bodies ---
# This ensures the client is sending the correct data format.
class NotificationPayload(BaseModel):
    title: str
    message: str
    type: str

class ReroutePayload(BaseModel):
    new_task_id: str
    reason: str

# --- Create the API endpoints that our client will call ---

@app.post("/v1/users/{user_id}/notifications")
def mock_notify_user(user_id: str, payload: NotificationPayload):
    """Mocks the endpoint for sending a notification."""
    print(f"✅ [Server] Received notification for user '{user_id}': '{payload.message}'")
    # Send back a success response
    return {"status": "success", "message_id": "mock_msg_12345"}

@app.post("/v1/drivers/{driver_id}/reroute")
def mock_reroute_driver(driver_id: str, payload: ReroutePayload):
    """Mocks the endpoint for rerouting a driver."""
    print(f"✅ [Server] Received reroute command for driver '{driver_id}' to task '{payload.new_task_id}'")
    # Send back a success response
    return {"status": "success", "reroute_confirmed": True}

@app.get("/v1/merchants/search")
def mock_search_merchants(
    cuisine: str, 
    max_wait_minutes: int, 
    limit: Optional[int] = 5
):
    """Mocks the endpoint for searching merchants."""
    print(f"✅ [Server] Received merchant search for '{cuisine}' with max wait '{max_wait_minutes}' mins.")
    # Send back a fake list of merchants
    return {
        "search_results": [
            {"name": f"Mock {cuisine} Place 1", "wait_time": 10},
            {"name": f"Mock {cuisine} Place 2", "wait_time": 12},
        ]
    }

@app.get("/")
def root():
    return {"message": "Mock Grab API is running. Hit the specific endpoints to test."}