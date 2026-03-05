from pathlib import Path
from langchain_core.messages import AIMessage, SystemMessage
from langchain_openai import ChatOpenAI
from src.agents.state import AibouState
from src.core.config import settings

critic_llm = ChatOpenAI(
    model=settings.MODEL_ARCHITECT,
    base_url=f"{settings.LOCAL_LLM_URL}/v1",
    api_key=settings.LOCAL_LLM_API_KEY,
    temperature=0.1
)

CRITIC_PROMPT_PATH = Path(__file__).resolve().parent.parent.parent / "prompts" / "node_prompts" / "critic.md"
with open(CRITIC_PROMPT_PATH, "r", encoding="utf-8") as file:
    CRITIC_PROMPT = file.read()

async def critic_node(state: AibouState) -> dict:
    print("[NODE] Critic is reviewing the execution output...")
    
    execution_output = state.get("execution_output", "")
    
    system_prompt = SystemMessage(content=CRITIC_PROMPT)
    user_prompt = AIMessage(content=f"Terminal Output:\n{execution_output}")
    
    response = await critic_llm.ainvoke([system_prompt, user_prompt])
    
    return {
        "messages": [AIMessage(content=f"Critic Review:\n{response.content}")],
        "current_agent": "Critic"
    }