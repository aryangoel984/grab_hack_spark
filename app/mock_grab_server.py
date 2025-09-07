import requests
import time
import json

RESOLVE_ENDPOINT = "http://127.0.0.1:8000/resolve"

# Scenarios now contain all the specific details the agents will need.
scenarios = [
    {
        "order_id": "GF-789",
        "scenario_text": "Major traffic jam on the main bridge.",
        "customer": {"id": "CUST-123", "name": "Alice"},
        "merchant": {"id": "MERC-456", "name": "The Coffee Shop"},
        "driver": {"id": "DRV-789"},
        "delivery_details": {"destination_address": "123 Maple St"}
    },
    {
        "order_id": "GF-555",
        "scenario_text": "The kitchen is overloaded and has a 40-minute prep time.",
        "customer": {"id": "CUST-456", "name": "Bob"},
        "merchant": {"id": "MERC-789", "name": "Pizza Palace", "status": "OVERLOADED"},
        "driver": {"id": "DRV-012"},
        "delivery_details": {"destination_address": "456 Oak Ave"}
    },
    {
        "order_id": "GF-111",
        "scenario_text": "First, find the fastest route for an urgent delivery. Once you have the new ETA, then inform the customer.",
        "customer": {"id": "CUST-789", "name": "Charlie"},
        "merchant": {"id": "MERC-321", "name": "SG Noodles"},
        "driver": {"id": "DRV-456"},
        "delivery_details": {"destination_address": "789 Pine Ln"}
    }
]

def run_simulation():
    print("--- 🚀 Mock GrabFood Server Started ---")
    for scenario in scenarios:
        try:
            print(f"\n--- Sending new disruption for Order {scenario['order_id']} ---")
            print(f"Scenario: {scenario['scenario_text']}")
            
            response = requests.post(RESOLVE_ENDPOINT, data=json.dumps(scenario))
            response.raise_for_status()
            
            print("--- ✅ Resolution Received ---")
            print(response.json())

        except requests.exceptions.RequestException as e:
            print(f"--- ❌ Error connecting to Synapse App: {e} ---")
            print("Is the uvicorn server running?")

        print("\n--- 🕒 Waiting for next event... ---")
        time.sleep(15)

if __name__ == "__main__":
    run_simulation()
