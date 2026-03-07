from langchain_core.messages import AIMessage
from langchain_openai import ChatOpenAI
from src.agents.state import AibouState
from src.core.config import settings

async def specialist_node(state: AibouState) -> dict:
    messages = state.get("messages") or []
    current_agent_tag = messages[-1].content.strip().upper() if messages else "CHAT"

    if current_agent_tag == "MATH":
        target_model = settings.MODEL_MATH
    elif current_agent_tag == "FINANCE":
        target_model = settings.MODEL_FINANCE
    elif current_agent_tag == "CREATIVE":
        target_model = settings.MODEL_CREATIVE
    elif current_agent_tag == "REASONING":
        target_model = settings.MODEL_REASONING
    elif current_agent_tag == "SCIENCE":
        target_model = settings.MODEL_SCIENCE
    else:
        target_model = settings.MODEL_CHAT
        
    print(f"[NODE] Specialist Node spinning up {target_model}...")

    specialist_llm = ChatOpenAI(
        model=target_model,
        base_url=f"{settings.LOCAL_LLM_URL}/v1",
        api_key=settings.LOCAL_LLM_API_KEY,
        timeout=120
    )
    
    response = await specialist_llm.ainvoke(messages)
    
    return {
        "messages": [AIMessage(content=response.content)],
        "current_agent": current_agent_tag
    }