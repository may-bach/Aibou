from pathlib import Path
from langchain_core.messages import AIMessage, SystemMessage
from langchain_openai import ChatOpenAI
from src.agents.state import AibouState
from src.core.config import settings

planner_llm = ChatOpenAI(
    model=settings.MODEL_ARCHITECT,
    base_url=f"{settings.LOCAL_LLM_URL}/v1",
    api_key="ollama",
    temperature=0.3
)

PLANNER_PROMPT_PATH = Path(__file__).resolve().parent.parent.parent / "prompts" / "node_prompts" / "planner.md"
with open(PLANNER_PROMPT_PATH, "r", encoding="utf-8") as file:
    PLANNER_PROMPT = file.read()

async def planner_node(state: AibouState) -> dict:
    print("[NODE] Planner is drafting the architecture checklist...")
    
    messages = state.get("messages", [])
    
    system_prompt = SystemMessage(content=PLANNER_PROMPT)
    prompt_sequence = [system_prompt] + list(messages)
    
    response = await planner_llm.ainvoke(prompt_sequence)
    
    return {
        "messages": [AIMessage(content=f"Project Plan:\n{response.content}")],
        "current_agent": "Planner"
    }