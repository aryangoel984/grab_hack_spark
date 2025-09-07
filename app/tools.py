from langchain.tools import tool

@tool
def send_notification(message: str) -> str:
    """Sends a notification to a user or driver about a critical update."""
    print(f"--- 🛠️ TOOL ACTION: Sending Notification: '{message}' ---")
    return "Notification sent successfully."

@tool
def get_alternative_route(address: str) -> str:
    """Finds the fastest alternative route to a given address based on current traffic."""
    print(f"--- 🛠️ TOOL ACTION: Finding alternative route for '{address}' ---")
    return "Alternative route found: Take the service road. New ETA is 25 minutes."

@tool
def get_merchant_status(merchant_id: str) -> str:
    """Checks the current operational status of a merchant (e.g., kitchen prep time)."""
    print(f"--- 🛠️ TOOL ACTION: Checking status for merchant '{merchant_id}' ---")
    if merchant_id == "MERC-789":
        return "Status: OVERLOADED. Current prep time is 40 minutes."
    return "Status: NORMAL. Current prep time is 15 minutes."