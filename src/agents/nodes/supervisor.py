from pathlib import Path
from langchain_core.messages import SystemMessage, AIMessage
from langchain_openai import ChatOpenAI
from src.agents.state import AibouState
from src.core.config import settings

supervisor_llm = ChatOpenAI(
    model=settings.MODEL_ARCHITECT,
    base_url=f"{settings.LOCAL_LLM_URL}/v1",
    api_key="ollama",
    temperature=0.0
)

SUPERVISOR_PROMPT_PATH = Path(__file__).resolve().parent.parent.parent / "prompts" / "node_prompts" / "supervisor.md"
with open(SUPERVISOR_PROMPT_PATH, "r", encoding="utf-8") as file:
    SUPERVISOR_PROMPT = file.read()

async def supervisor_node(state: AibouState) -> dict:
    print("[NODE] Supervisor is routing...")
    
    messages = state.get("messages", [])
    
    system_prompt = SystemMessage(content=SUPERVISOR_PROMPT)
    prompt_sequence = [system_prompt] + list(messages)
    
    response = await supervisor_llm.ainvoke(prompt_sequence)
    decision = response.content.strip().upper()
    
    return {
        "current_agent": "Supervisor",
        "messages": [AIMessage(content=f"Routing to: {decision}")]
    }