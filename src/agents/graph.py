from langgraph.graph import StateGraph, START, END
from src.agents.state import AibouState

from src.agents.nodes.supervisor import supervisor_node
from src.agents.nodes.planner import planner_node
from src.agents.nodes.coder import coder_node
from src.agents.nodes.execution import execution_node
from src.agents.nodes.critic import critic_node
from src.agents.nodes.specialist import specialist_node


def supervisor_router(state: AibouState):
    messages = state.get("messages", [])
    if not messages:
        return END
        
    last_message = messages[-1].content.strip().upper()
    
    if any(tag in last_message for tag in ["PLAN", "ARCHITECT"]):
        return "Planner"
    elif any(tag in last_message for tag in ["COD"]):  # matches CODER, CODING, CODE
        return "Coder"
    elif any(tag in last_message for tag in ["MATH", "FINANCE", "CREATIVE", "REASONING", "CHAT", "SCIENCE"]):
        return "Specialist"
    else:
        return END

def critic_router(state: AibouState):
    messages = state.get("messages", [])
    last_message = messages[-1].content
    retry_count = state.get("retry_count", 0)
    
    if "PASS" in last_message:
        return "Supervisor"
    
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