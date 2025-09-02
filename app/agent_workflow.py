# app/agent_workflow.py
from typing import List, TypedDict, Literal, Annotated
import operator
from langchain_core.prompts import ChatPromptTemplate, PromptTemplate
from typing import List, TypedDict, Literal
from langchain_core.prompts import ChatPromptTemplate, PromptTemplate
from pydantic import BaseModel, Field
from langchain.agents import AgentExecutor, create_react_agent
from langgraph.graph import StateGraph, END

from .config import llm
from .tools import send_notification, get_alternative_route

# -- 1. DEFINE THE PLAN AND STATE --
# This plan includes the workflow_type for the planner's decision.
class Plan(BaseModel):
    """The concrete plan of action to resolve a disruption."""
    workflow_type: Literal["sequential", "parallel"] = Field(
        ..., description="The type of workflow to execute. Use 'parallel' for independent tasks."
    )
    steps: List[str] = Field(...,
        description="A list of tasks for the specialized agents. Each task must start with the agent's name, e.g., 'CommsAgent: ...' or 'TrafficAgent: ...'."
    )

# The state is updated to collect results from parallel runs.
class AgentState(TypedDict):
    disruption_scenario: str
    plan: Plan
    # This annotation is the fix
    task_results: Annotated[list, operator.add]
    current_task_index: int
    final_resolution: str

# -- 2. CREATE THE AGENTS (PLANNER & SPECIALISTS) --
planner_prompt = ChatPromptTemplate.from_template(
    """You are the CORE BRAIN, an expert logistics planner. Your job is to create a plan to resolve the following disruption.

    First, decide if the tasks can be run in parallel or must be run sequentially.
    - Use 'parallel' if the tasks are independent (e.g., finding a new route AND notifying a customer).
    - Use 'sequential' if one task depends on the result of another.

    Next, list the steps for your plan, assigning each to a specialist:
    - [CommsAgent] for communication tasks.
    - [TrafficAgent] for route or traffic-related tasks.

    Disruption Scenario: {disruption_scenario}
    """
)
planner_agent = planner_prompt | llm.with_structured_output(Plan)

# CommsAgent and its prompt
comms_tools = [send_notification]
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

# TrafficAgent and its prompt
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



# -- 3. DEFINE THE GRAPH NODES --
def planner_node(state: AgentState):
    print("--- 🧠 Planner Agent Running ---")
    plan = planner_agent.invoke({"disruption_scenario": state["disruption_scenario"]})
    return {"plan": plan, "task_results": []} # Initialize results list

# Specialist nodes now pull their own tasks from the plan
def comms_agent_node(state: AgentState):
    print("--- 🛠️ CommsAgent Running ---")
    task = next(s for s in state["plan"].steps if "CommsAgent" in s)
    result = comms_agent_executor.invoke({"input": task})
    return {"task_results": state['task_results'] + [("CommsAgent", result["output"])]}

def traffic_agent_node(state: AgentState):
    print("--- 🛠️ TrafficAgent Running ---")
    task = next(s for s in state["plan"].steps if "TrafficAgent" in s)
    result = traffic_agent_executor.invoke({"input": task})
    return {"task_results": state['task_results'] + [("TrafficAgent", result["output"])]}

# New node to aggregate results from parallel runs
def aggregator_node(state: AgentState):
    print("---  собиратель (Aggregator) Running ---")
    final_resolution = "\n".join([f"{agent}: {result}" for agent, result in state["task_results"]])
    return {"final_resolution": final_resolution}

# -- 4. DEFINE THE ROUTER --
def router(state: AgentState):
    print("--- ROUTING ---")
    if state["plan"].workflow_type == "parallel":
        # Fan out to all specialists, then join at the aggregator
        return ["comms_agent", "traffic_agent"]
    else:
        # For now, sequential flow is not fully implemented, so we end.
        # This can be built out later.
        print("Sequential workflow not fully implemented. Ending.")
        return END

# -- 5. ASSEMBLE THE WORKFLOW GRAPH --
workflow = StateGraph(AgentState)

workflow.add_node("planner", planner_node)
workflow.add_node("comms_agent", comms_agent_node)
workflow.add_node("traffic_agent", traffic_agent_node)
workflow.add_node("aggregator", aggregator_node)

workflow.set_entry_point("planner")

# After the planner, the router decides where to go
workflow.add_conditional_edges(
    "planner",
    router,
    {
        # For parallel, LangGraph will automatically route to the list of nodes
        # and then wait for them all to finish.
        "comms_agent": "comms_agent",
        "traffic_agent": "traffic_agent",
        END: END
    }
)

# After the parallel tasks are done, they all go to the aggregator
workflow.add_edge("comms_agent", "aggregator")
workflow.add_edge("traffic_agent", "aggregator")
workflow.add_edge("aggregator", END)

compiled_workflow = workflow.compile()