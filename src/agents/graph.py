from langgraph.graph import StateGraph, START, END
from src.agents.state import AibouState

from src.agents.nodes.supervisor import supervisor_node
from src.agents.nodes.planner import planner_node
from src.agents.nodes.coder import coder_node
from src.agents.nodes.execution import execution_node
from src.agents.nodes.critic import critic_node
from src.agents.nodes.specialist import specialist_node


def supervisor_router(state: AibouState):
    route = state.get("next_route", "FINISH")
    if route == "FINISH":
        return END
    
    # Fallback validation just in case the LLM outputs a totally invalid route
    valid_routes = ["Planner", "Coder", "Specialist"]
    if route in valid_routes:
        return route
    return END

def critic_router(state: AibouState):
    messages = state.get("messages", [])
    if not messages:
        return END
        
    last_message = messages[-1].content.upper()
    retry_count = state.get("retry_count", 0)
    
    if "PASS" in last_message:
        print("\n[CRITIC] Code passed! Ending execution.\n")
        return END
    
    if retry_count >= 3:
        print(f"\n[KILL SWITCH ACTIVATED] Maximum retries ({retry_count}) reached.\n")
        return END 
    
    print(f"\n[LOOPING] Bug found. Routing back to Coder. (Attempt {retry_count}/3)\n")
    return "Coder"

workflow = StateGraph(AibouState)

workflow.add_node("Supervisor", supervisor_node)
workflow.add_node("Planner", planner_node)
workflow.add_node("Coder", coder_node)
workflow.add_node("Executor", execution_node)
workflow.add_node("Critic", critic_node)
workflow.add_node("Specialist", specialist_node)

workflow.add_edge(START, "Supervisor")

workflow.add_conditional_edges("Supervisor", supervisor_router)

workflow.add_edge("Specialist", END)

workflow.add_edge("Planner", "Coder")
workflow.add_edge("Coder", "Executor")
workflow.add_edge("Executor", "Critic")
workflow.add_conditional_edges("Critic", critic_router)

aibou_swarm = workflow.compile()