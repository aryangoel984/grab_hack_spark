# app/agent_workflow.py
from typing import List, TypedDict, Literal
from langchain_core.prompts import ChatPromptTemplate, PromptTemplate
from pydantic import BaseModel, Field
from langchain.agents import AgentExecutor, create_react_agent
from langgraph.graph import StateGraph, END
from .tools import send_notification, get_alternative_route 


from .config import llm  # Import the initialized Gemini model
from .tools import send_notification

# -- 1. Define the Plan and State --
class Plan(BaseModel):
    """The concrete plan of action to resolve a disruption."""
    steps: List[str] = Field(..., 
        description="A list of tasks for the specialized agents. Each task must start with the agent's name, e.g., 'CommsAgent: ...' or 'TrafficAgent: ...'."
    )

class AgentState(TypedDict):
    disruption_scenario: str
    plan: Plan
    current_task_index: int
    task_result: str

# -- 2. Create the Planning Agent (The Brain) --
# Corrected planner_prompt
planner_prompt = ChatPromptTemplate.from_template(
    """You are the CORE BRAIN, an expert logistics planner. Your job is to create a simple, step-by-step plan to resolve the following disruption.

    Assign each step to a specialist:
    - [CommsAgent] for communication tasks.
    - [TrafficAgent] for route or traffic-related tasks.
    
    Disruption Scenario: {disruption_scenario}
    """
)
planner_agent = planner_prompt | llm.with_structured_output(Plan)

# -- 3. Create the Specialized Agent (The Hands) --
comms_tools = [send_notification]
# Corrected comms_prompt
# This new prompt has all the required variables for a ReAct agent.
comms_prompt = PromptTemplate.from_template(
    """
You are the CommsAgent, a communications specialist. Answer the following questions as best you can. You have access to the following tools:

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
Thought:{agent_scratchpad}
"""
)
comms_agent_runnable = create_react_agent(llm, comms_tools, comms_prompt)
comms_agent_executor = AgentExecutor(agent=comms_agent_runnable, tools=comms_tools, verbose=True, handle_parsing_errors=True)
traffic_tools = [get_alternative_route]
traffic_prompt = PromptTemplate.from_template(
    """
You are the TrafficAgent, a traffic analysis expert. Answer the following questions as best you can. You have access to the following tools:

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
Thought:{agent_scratchpad}
"""
)
traffic_agent_runnable = create_react_agent(llm, traffic_tools, traffic_prompt)
traffic_agent_executor = AgentExecutor(agent=traffic_agent_runnable, tools=traffic_tools, verbose=True, handle_parsing_errors=True)

# -- 4. Define the Graph Nodes --
def planner_node(state: AgentState):
    print("--- 🧠 Planner Agent Running ---")
    plan = planner_agent.invoke({"disruption_scenario": state["disruption_scenario"]})
    return {"plan": plan, "current_task_index": 0}

def specialist_node(state: AgentState):
    print(f"--- 🛠️ Specialist Agent Running Task #{state['current_task_index']} ---")
    current_task = state["plan"].steps[state["current_task_index"]]
    
    # This routing logic now sends the task to the correct agent
    if "CommsAgent" in current_task:
        result = comms_agent_executor.invoke({"input": current_task})
    elif "TrafficAgent" in current_task:
        result = traffic_agent_executor.invoke({"input": current_task})
    else:
        result = {"output": f"Error: No agent found for task '{current_task}'."}
        
    return {"task_result": result["output"], "current_task_index": state["current_task_index"] + 1}
def router(state: AgentState):
    if state["current_task_index"] >= len(state["plan"].steps):
        return END
    return "specialist"

# -- 5. Assemble the Workflow Graph --
workflow = StateGraph(AgentState)
workflow.add_node("planner", planner_node)
workflow.add_node("specialist", specialist_node)

workflow.set_entry_point("planner")
workflow.add_edge("planner", "specialist")
workflow.add_conditional_edges("specialist", router, {END: END, "specialist": "specialist"})

compiled_workflow = workflow.compile()