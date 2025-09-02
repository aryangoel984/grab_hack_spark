# app/tools.py
from langchain.tools import tool

@tool
def send_notification(message: str) -> str:
    """Sends a notification to a user or driver about a critical update."""
    print(f"--- 🛠️ TOOL ACTION: Sending Notification: '{message}' ---")
    # This would call a real API in a production system
    return "Notification sent successfully."
# app/tools.py

# ... (keep the existing send_notification tool) ...

@tool
def get_alternative_route(address: str) -> str:
    """
    Finds the fastest alternative route to a given address based on current traffic.
    Returns a string describing the new route and estimated time.
    """
    print(f"--- 🛠️ TOOL ACTION: Finding alternative route for '{address}' ---")
    # In a real app, this would call Google Maps API or a similar service.
    return "Alternative route found: Take the service road. New ETA is 25 minutes."