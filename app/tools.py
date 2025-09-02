# app/tools.py
from langchain.tools import tool

@tool
def send_notification(message: str) -> str:
    """Sends a notification to a user or driver about a critical update."""
    print(f"--- 🛠️ TOOL ACTION: Sending Notification: '{message}' ---")
    # This would call a real API in a production system
    return "Notification sent successfully."