# import os
# import json
# import google.generativeai as genai
# from pydantic import BaseModel, Field, ValidationError
# from typing import List, Dict, Any, Callable
# from dotenv import load_dotenv

# # Load environment variables from .env file
# load_dotenv()

# # --- 1. Define the Structured Output (The Plan) ---
# # (This section is unchanged)
# class ToolCall(BaseModel):
#     tool_name: str = Field(..., description="The exact name of the tool to be called.")
#     parameters: Dict[str, Any] = Field({}, description="The parameters to pass to the tool.")
#     reasoning: str = Field(..., description="A brief explanation of why this tool was chosen.")

# class Plan(BaseModel):
#     thought: str = Field(..., description="A high-level summary of the plan and reasoning.")
#     workflow_type: str = Field(..., description="Either 'sequential' or 'parallel'.", enum=["sequential", "parallel"])
#     steps: List[ToolCall] = Field(..., description="The sequence of tool calls to execute.")

# # --- 2. Create the Core Brain Class (Modified for Gemini) ---
# # (This section is unchanged)
# class CoreBrain:
#     def __init__(self):
#         api_key = os.getenv("GOOGLE_API_KEY")
#         if not api_key:
#             raise ValueError("GOOGLE_API_KEY environment variable not found.")
#         genai.configure(api_key=api_key)
#         self.model = genai.GenerativeModel(
#             'gemini-1.5-pro-latest',
#             generation_config={"response_mime_type": "application/json"}
#         )
#         print("✅ Gemini client configured successfully.")

#     def create_plan(self, scenario: str) -> Plan:
#         prompt = f"""
#         You are the 'Planning Agent' for Synapse, an AI-powered last-mile coordinator for Grab.
#         Your primary role is to analyze a disruption scenario and generate a structured, step-by-step action plan in JSON format.
        
#         You have access to the following tools:
#         - notify_customer(message: str, user_id: str): Informs the customer of a situation.
#         - reroute_driver(driver_id: str, new_task_id: str): Assigns a driver to a short, nearby delivery.
#         - get_nearby_merchants(cuisine_type: str, max_wait_time: int): Finds similar restaurants with shorter wait times.
#         - initiate_mediation_flow(case_id: str, user_id: str, driver_id: str): Starts a real-time resolution process.
        
#         Based on the following scenario, you must create a plan. Respond ONLY with a valid JSON object that conforms to the schema.

#         Scenario:
#         "{scenario}"
        
#         JSON Schema:
#         {json.dumps(Plan.model_json_schema(), indent=2)}
#         """
#         try:
#             print("🧠 Core Brain is thinking with Gemini...")
#             response = self.model.generate_content(prompt)
#             response_json = json.loads(response.text)
#             print("✅ Gemini generated a raw plan.")
#             validated_plan = Plan(**response_json)
#             print("✅ Plan validated successfully.")
#             return validated_plan
#         except (ValidationError, Exception) as e:
#             print(f"❌ An error occurred during plan creation: {e}")
#             return None

# # --- 3. NEW: Define the Tools and the Executor ---

# # These are the actual functions our agents can use.
# # For now, they just print messages to show they're working.
# def notify_customer(message: str, user_id: str):
#     print(f"📣 NOTIFYING USER '{user_id}': '{message}'")
#     return f"Successfully notified {user_id}."

# def reroute_driver(driver_id: str, new_task_id: str):
#     print(f"🚗 REROUTING DRIVER '{driver_id}' to new task '{new_task_id}'.")
#     return f"Driver {driver_id} successfully rerouted."

# def get_nearby_merchants(cuisine_type: str, max_wait_time: int):
#     print(f"🍔 SEARCHING for '{cuisine_type}' with max wait of {max_wait_time} mins.")
#     # In a real app, this would query a database or API.
#     return f"Found 3 nearby '{cuisine_type}' restaurants."

# # The Tool Registry maps the string name of a tool to its actual function.
# tool_registry: Dict[str, Callable] = {
#     "notify_customer": notify_customer,
#     "reroute_driver": reroute_driver,
#     "get_nearby_merchants": get_nearby_merchants,
# }

# class Executor:
#     """Executes a plan by calling tools from the registry."""
#     def __init__(self, registry: Dict[str, Callable]):
#         self.registry = registry

#     def execute_plan(self, plan: Plan):
#         if not plan:
#             print("Cannot execute an empty plan.")
#             return

#         print("\n--- 🚀 EXECUTING PLAN ---")
#         print(f"Workflow Type: {plan.workflow_type}")
        
#         if plan.workflow_type == "sequential":
#             for step in plan.steps:
#                 tool_name = step.tool_name
#                 params = step.parameters
                
#                 print(f"\n▶️ Running Step: {tool_name} with params: {params}")
                
#                 if tool_name in self.registry:
#                     tool_function = self.registry[tool_name]
#                     try:
#                         # Call the actual function with the provided parameters
#                         result = tool_function(**params)
#                         print(f"✅ Result: {result}")
#                     except TypeError as e:
#                         print(f"❌ Error: Incorrect parameters for tool '{tool_name}'. Details: {e}")
#                 else:
#                     print(f"❌ Error: Tool '{tool_name}' not found in registry.")
        
#         # We will implement the 'parallel' workflow in a future step
#         elif plan.workflow_type == "parallel":
#             print("🌀 Parallel execution not yet implemented. Running sequentially for now.")
#             # (Add parallel logic here later)

#         print("\n--- ✅ PLAN EXECUTION COMPLETE ---")


# # --- 4. NEW: Updated Main Execution Block ---

# if __name__ == "__main__":
#     # 1. Instantiate the brain
#     brain = CoreBrain()
    
#     # 2. Define the scenario
#     disruption_scenario = """
#     An order was placed for user 'user_123' at 'Burger Palace'.
#     However, the get_merchant_status() tool detected a 40-minute kitchen prep time.
#     The assigned driver is 'driver_456'.
#     Proactively notify the user and suggest searching for other burger joints with less than a 15-minute wait.
#     """
    
#     # 3. Generate the plan
#     generated_plan = brain.create_plan(disruption_scenario)
    
#     # 4. Instantiate the executor with the tool registry
#     executor = Executor(tool_registry)
    
#     # 5. Execute the plan
#     executor.execute_plan(generated_plan)
import os
import json
import requests
import google.generativeai as genai
from pydantic import BaseModel, Field, ValidationError
from typing import List, Dict, Any, Callable
from dotenv import load_dotenv

# --- 1. SETUP: LOAD ENVIRONMENT VARIABLES ---
load_dotenv()
GRAB_API_BASE_URL = os.getenv("GRAB_API_BASE_URL")
GRAB_API_SECRET_KEY = os.getenv("GRAB_API_SECRET_KEY")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

# --- 2. DATA MODELS: DEFINE THE STRUCTURE OF A "PLAN" ---
class ToolCall(BaseModel):
    """A single tool call to be executed by a specialized agent."""
    tool_name: str = Field(..., description="The exact name of the tool to be called.")
    parameters: Dict[str, Any] = Field({}, description="The parameters to pass to the tool.")
    reasoning: str = Field(..., description="A brief explanation of why this tool was chosen.")

class Plan(BaseModel):
    """The complete, step-by-step plan generated by the Core Brain."""
    thought: str = Field(..., description="A high-level summary of the plan and reasoning.")
    workflow_type: str = Field(..., description="Either 'sequential' or 'parallel'.", enum=["sequential", "parallel"])
    steps: List[ToolCall] = Field(..., description="The sequence of tool calls to execute.")

# --- 3. THE PLANNER: CORE BRAIN CLASS ---
class CoreBrain:
    """The central LLM orchestrator that creates plans using Gemini."""
    def __init__(self):
        if not GOOGLE_API_KEY:
            raise ValueError("GOOGLE_API_KEY environment variable not found.")
        genai.configure(api_key=GOOGLE_API_KEY)
        self.model = genai.GenerativeModel(
            'gemini-1.5-pro-latest',
            generation_config={"response_mime_type": "application/json"}
        )
        print("✅ Gemini client configured successfully.")

    def create_plan(self, scenario: str) -> Plan:
        """Takes a natural language scenario and returns a structured plan."""
        prompt = f"""
        You are the 'Planning Agent' for Synapse, an AI-powered last-mile coordinator for Grab.
        Your role is to analyze a disruption scenario and generate a structured action plan in JSON format.
        
        Available Tools:
        - notify_customer(message: str, user_id: str)
        - reroute_driver(driver_id: str, new_task_id: str)
        - get_nearby_merchants(cuisine_type: str, max_wait_time: int)
        
        Based on the scenario below, create a plan. Respond ONLY with a valid JSON object conforming to the schema.

        Scenario:
        "{scenario}"
        
        JSON Schema:
        {json.dumps(Plan.model_json_schema(), indent=2)}
        """
        try:
            print("🧠 Core Brain is thinking with Gemini...")
            response = self.model.generate_content(prompt)
            response_json = json.loads(response.text)
            print("✅ Gemini generated a raw plan.")
            validated_plan = Plan(**response_json)
            print("✅ Plan validated successfully.")
            return validated_plan
        except (ValidationError, Exception) as e:
            print(f"❌ An error occurred during plan creation: {e}")
            return None

# --- 4. THE TOOLS: FUNCTIONS THAT INTERACT WITH THE (MOCK) BACKEND ---
API_HEADERS = {
    "Authorization": f"Bearer {GRAB_API_SECRET_KEY}",
    "Content-Type": "application/json"
}

def notify_customer(message: str, user_id: str):
    """Sends a notification to a user via the API."""
    endpoint = f"{GRAB_API_BASE_URL}/users/{user_id}/notifications"
    payload = {"title": "An update on your order", "message": message, "type": "push_notification"}
    print(f"📣 NOTIFYING USER '{user_id}' via API: POST {endpoint}")
    try:
        response = requests.post(endpoint, headers=API_HEADERS, json=payload)
        response.raise_for_status()
        data = response.json()
        return f"API call successful. Server responded with: {data}"
    except requests.exceptions.RequestException as e:
        return f"API call failed. Error: {e}"

def reroute_driver(driver_id: str, new_task_id: str):
    """Reroutes a driver to a new task via the API."""
    endpoint = f"{GRAB_API_BASE_URL}/drivers/{driver_id}/reroute"
    payload = {"new_task_id": new_task_id, "reason": "Optimizing route due to merchant delay."}
    print(f"🚗 REROUTING DRIVER '{driver_id}' via API: POST {endpoint}")
    try:
        response = requests.post(endpoint, headers=API_HEADERS, json=payload)
        response.raise_for_status()
        data = response.json()
        return f"API call successful. Server responded with: {data}"
    except requests.exceptions.RequestException as e:
        return f"API call failed. Error: {e}"

def get_nearby_merchants(cuisine_type: str, max_wait_time: int):
    """Finds nearby merchants using a GET request to the API."""
    endpoint = f"{GRAB_API_BASE_URL}/merchants/search"
    params = {"cuisine": cuisine_type, "max_wait_minutes": max_wait_time, "limit": 5}
    print(f"🍔 SEARCHING for merchants via API: GET {endpoint}")
    try:
        response = requests.get(endpoint, headers=API_HEADERS, params=params)
        response.raise_for_status()
        data = response.json()
        return f"API call successful. Server responded with: {data}"
    except requests.exceptions.RequestException as e:
        return f"API call failed. Error: {e}"

# --- 5. THE REGISTRY: MAPPING TOOL NAMES TO FUNCTIONS ---
tool_registry: Dict[str, Callable] = {
    "notify_customer": notify_customer,
    "reroute_driver": reroute_driver,
    "get_nearby_merchants": get_nearby_merchants,
}

# --- 6. THE EXECUTOR: RUNS THE PLAN ---
class Executor:
    """Executes a plan by calling tools from the registry."""
    def __init__(self, registry: Dict[str, Callable]):
        self.registry = registry

    def execute_plan(self, plan: Plan):
        if not plan:
            print("Cannot execute an empty or invalid plan.")
            return
        print("\n--- 🚀 EXECUTING PLAN ---")
        for step in plan.steps:
            tool_name = step.tool_name
            params = step.parameters
            print(f"\n▶️ Running Step: {tool_name} with params: {params}")
            if tool_name in self.registry:
                tool_function = self.registry[tool_name]
                try:
                    result = tool_function(**params)
                    print(f"✅ Result: {result}")
                except TypeError as e:
                    print(f"❌ Error: Incorrect parameters for tool '{tool_name}'. Details: {e}")
            else:
                print(f"❌ Error: Tool '{tool_name}' not found in registry.")
        print("\n--- ✅ PLAN EXECUTION COMPLETE ---")

# --- 7. MAIN: ORCHESTRATES THE ENTIRE FLOW ---
if __name__ == "__main__":
    brain = CoreBrain()
    disruption_scenario = """
    An order for user 'user_775' at 'The Pizza Shop' is delayed.
    The kitchen reports a 35-minute prep time. The assigned driver is 'driver_901'.
    Proactively notify the user about the delay and search for other pizza places with under a 20-minute wait.
    """
    generated_plan = brain.create_plan(disruption_scenario)
    executor = Executor(tool_registry)
    executor.execute_plan(generated_plan)