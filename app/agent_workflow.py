import operator
from typing import List, TypedDict, Literal, Annotated

from langchain_core.prompts import ChatPromptTemplate, PromptTemplate
from pydantic import BaseModel, Field
from langchain.agents import AgentExecutor, create_react_agent
from langgraph.graph import StateGraph, END

from .config import llm
from .tools import send_notification, get_alternative_route, get_merchant_status

# -- 1. STATE & PLAN --
# This is the data structure that flows through the graph.
class Plan(BaseModel):
    """The concrete plan of action to resolve a disruption."""
    workflow_type: Literal["sequential", "parallel"] = Field(..., description="The type of workflow to execute.")
    steps: List[str] = Field(..., description="A list of specific, actionable tasks for the specialized agents.")

class AgentState(TypedDict):
    """Represents the state of our graph."""
    request_data: dict
    plan: Plan
    task_results: Annotated[list, operator.add] # Used to aggregate results
    current_task_index: int # Used to track progress in sequential workflows
    final_resolution: str

# -- 2. AGENT DEFINITIONS --
# The planner's job is to create a strategy based on the full data context.
planner_prompt = ChatPromptTemplate.from_template(
    """You are the CORE BRAIN, an expert logistics planner. Your job is to create a plan to resolve a disruption based on the rich data provided.

    **Your Process:**
    1.  Analyze the full `request_data` payload, paying close attention to the `scenario_text`, `customer`, `merchant`, and `delivery_details`.
    2.  Decide if the tasks can be run in **parallel** (if independent) or must be run **sequentially** (if one depends on another).
    3.  Create a list of specific, actionable steps. Use the actual IDs, names, and addresses from the data in your steps.

    **Example:** Instead of a generic step like "Notify the customer", create a specific step like "CommsAgent: Notify customer Alice (ID: CUST-123) about the delay."

    **Available Specialists:**
    - [CommsAgent]: For communication tasks.
    - [TrafficAgent]: For route or traffic tasks.
    - [MerchantAgent]: For checking merchant status.

    **Full Request Data:**
    ```json
    {request_data}
    ```
    """
)
planner_agent = planner_prompt | llm.with_structured_output(Plan)

# A single, reusable prompt for all our specialist "worker" agents.
react_prompt_template = """You are a specialist agent. You must use your tools to answer the question.

You have access to the following tools:
{tools}

Use the following format:
Question: the input question you must answer
Thought: you should always think about what to do
Action: the action to take, should be one of [{tool_names}]
Action Input: the input to the action
Observation: the result of the action
... (this Thought/Action/Action Input/Observation can repeat N times)
Thought: I now know the final answer
Final Answer: the final answer to the original input question

Begin!

Question: {input}
Thought:{agent_scratchpad}"""
react_prompt = PromptTemplate.from_template(react_prompt_template)

# Define the three specialist agents and their specific tools.
comms_tools = [send_notification]
comms_agent_executor = AgentExecutor(agent=create_react_agent(llm, comms_tools, react_prompt), tools=comms_tools, verbose=True, handle_parsing_errors=True)

traffic_tools = [get_alternative_route]
traffic_agent_executor = AgentExecutor(agent=create_react_agent(llm, traffic_tools, react_prompt), tools=traffic_tools, verbose=True, handle_parsing_errors=True)

merchant_tools = [get_merchant_status]
merchant_agent_executor = AgentExecutor(agent=create_react_agent(llm, merchant_tools, react_prompt), tools=merchant_tools, verbose=True, handle_parsing_errors=True)


# -- 3. GRAPH NODE FUNCTIONS --
def planner_node(state: AgentState):
    """The first node to run. It creates the plan."""
    print("--- 🧠 Planner Agent Running ---")
    plan = planner_agent.invoke({"request_data": state["request_data"]})
    return {"plan": plan, "task_results": [], "current_task_index": 0}

def comms_agent_node(state: AgentState):
    """Runs the communication agent on its assigned task."""
    task = next((s for s in state["plan"].steps if "CommsAgent" in s), None)
    if task is None: return {"task_results": []} # No task for this agent
    print(f"--- 🛠️ CommsAgent Running: {task} ---")
    result = comms_agent_executor.invoke({"input": task})
    return {"task_results": [("CommsAgent", result["output"])]}

def traffic_agent_node(state: AgentState):
    """Runs the traffic agent on its assigned task."""
    task = next((s for s in state["plan"].steps if "TrafficAgent" in s), None)
    if task is None: return {"task_results": []}
    print(f"--- 🛠️ TrafficAgent Running: {task} ---")
    result = traffic_agent_executor.invoke({"input": task})
    return {"task_results": [("TrafficAgent", result["output"])]}

def merchant_agent_node(state: AgentState):
    """Runs the merchant agent on its assigned task."""
    task = next((s for s in state["plan"].steps if "MerchantAgent" in s), None)
    if task is None: return {"task_results": []}
    print(f"--- 🛠️ MerchantAgent Running: {task} ---")
    result = merchant_agent_executor.invoke({"input": task})
    return {"task_results": [("MerchantAgent", result["output"])]}

def aggregator_node(state: AgentState):
    """The final node. It collects all results and creates a final response."""
    print("---  Aggregator Running ---")
    final_resolution = "\n".join([f"{agent}: {result}" for agent, result in state["task_results"]])
    return {"final_resolution": final_resolution}

# -- 4. THE INTELLIGENT ROUTER --
def router(state: AgentState):
    """This function inspects the plan and decides where to go next."""
    print("--- ROUTING ---")
    plan = state.get("plan")
    
    if not plan:
        return END

    if plan.workflow_type == "parallel":
        # For parallel, return a list of all agent nodes that have a task in the plan.
        tasks_to_run = []
        if any("CommsAgent" in step for step in plan.steps): tasks_to_run.append("comms_agent")
        if any("TrafficAgent" in step for step in plan.steps): tasks_to_run.append("traffic_agent")
        if any("MerchantAgent" in step for step in plan.steps): tasks_to_run.append("merchant_agent")
        return tasks_to_run

    elif plan.workflow_type == "sequential":
        # This part of the logic needs to be fully implemented in a future step
        print("--- Sequential workflow logic is a placeholder. Ending. ---")
        return END
            
    return END

# -- 5. GRAPH ASSEMBLY --
workflow = StateGraph(AgentState)

workflow.add_node("planner", planner_node)
workflow.add_node("comms_agent", comms_agent_node)
workflow.add_node("traffic_agent", traffic_agent_node)
workflow.add_node("merchant_agent", merchant_agent_node)
workflow.add_node("aggregator", aggregator_node)

workflow.set_entry_point("planner")

# After the planner, the router decides which specialist(s) to run.
workflow.add_conditional_edges("planner", router, {
    "comms_agent": "comms_agent",
    "traffic_agent": "traffic_agent",
    "merchant_agent": "merchant_agent",
    END: END
})

# After the parallel tasks run, they all proceed to the aggregator to join the results.
workflow.add_edge("comms_agent", "aggregator")
workflow.add_edge("traffic_agent", "aggregator")
workflow.add_edge("merchant_agent", "aggregator")

# After aggregation, the workflow is finished.
workflow.add_edge("aggregator", END)

compiled_workflow = workflow.compile()





