from pathlib import Path
from langchain_core.messages import SystemMessage, AIMessage
from langchain_openai import ChatOpenAI
from src.agents.state import AibouState
from src.core.config import settings

supervisor_llm = ChatOpenAI(
    model=settings.MODEL_ARCHITECT,
    base_url=f"{settings.LOCAL_LLM_URL}/v1",
    api_key=settings.LOCAL_LLM_API_KEY,
    temperature=0.0
)

SUPERVISOR_PROMPT_PATH = Path(__file__).resolve().parent.parent.parent / "prompts" / "node_prompts" / "supervisor.md"
with open(SUPERVISOR_PROMPT_PATH, "r", encoding="utf-8") as file:
    SUPERVISOR_PROMPT = file.read()

import json

async def supervisor_node(state: AibouState) -> dict:
    print("[NODE] Supervisor is routing...")
    
    messages = state.get("messages", [])
    
    system_prompt = SystemMessage(content=SUPERVISOR_PROMPT)
    prompt_sequence = [system_prompt] + list(messages)
    
    # We enforce JSON output formatting via LangChain/OpenAI if supported,
    # but since local LLMs might be quirky, we just ask for JSON in the prompt and parse it.
    response = await supervisor_llm.ainvoke(prompt_sequence)
    raw_output = response.content.strip()
    
    # Strip potential markdown codeblock formatting if the LLM adds it anyway
    if raw_output.startswith("```json"):
        raw_output = raw_output[7:-3].strip()
    elif raw_output.startswith("```"):
        raw_output = raw_output[3:-3].strip()
        
    try:
        decision_data = json.loads(raw_output)
        route = decision_data.get("route", "FINISH")
    except Exception as e:
        print(f"[WARNING] Supervisor produced invalid JSON: {raw_output}. Defaulting to FINISH. Error: {e}")
        route = "FINISH"
    
    print(f"       -> Decided route: {route}")
    return {
        "current_agent": "Supervisor",
        "next_route": route
    }