import json
import re
from pathlib import Path
from langchain_core.messages import SystemMessage, AIMessage, HumanMessage
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

FAST_GREETINGS = {
    "yo", "yo!", "hi", "hi!", "hey", "hey!", "hello", "hello!", "sup", "sup!",
    "good morning", "good afternoon", "good evening", "howdy", "wassup", "what's up", "whats up"
}

ARCHITECT_KEYWORDS = {
    "build a full", "create an entire", "scaffold project", "new architecture",
    "multi-agent system", "build an app from scratch", "architect a new"
}

async def supervisor_node(state: AibouState) -> dict:
    messages = state.get("messages", [])
    
    # Fast path: instant 0ms routing for the vast majority of user conversations & questions
    if messages:
        last_msg = messages[-1]
        if isinstance(last_msg, HumanMessage) and isinstance(last_msg.content, str):
            clean_input = last_msg.content.strip().lower()
            
            # Fast greeting
            if clean_input in FAST_GREETINGS or (len(clean_input) <= 4 and clean_input.isalpha()):
                print("[SUPERVISOR FAST-PATH] -> Specialist (greeting) [0ms]")
                return {
                    "current_agent": "Supervisor",
                    "next_route": "Specialist",
                    "specialist_domain": "greeting"
                }

            # If not explicitly asking to architect a massive new software project from scratch,
            # fast-path directly to Specialist (which has full tools, RAG, and domain expertise)!
            is_heavy_architecture = any(kw in clean_input for kw in ARCHITECT_KEYWORDS)
            if not is_heavy_architecture:
                print("[SUPERVISOR FAST-PATH] -> Specialist (general) [0ms]")
                return {
                    "current_agent": "Supervisor",
                    "next_route": "Specialist",
                    "specialist_domain": "general"
                }

    print("[SUPERVISOR LLM] Routing complex architecture request...")
    system_prompt = SystemMessage(content=SUPERVISOR_PROMPT)
    prompt_sequence = [system_prompt] + list(messages)
    
    try:
        response = await supervisor_llm.ainvoke(prompt_sequence)
        raw_output = response.content.strip()
    except Exception as e:
        print(f"[WARNING] Supervisor LLM call failed: {e}. Defaulting to Specialist.")
        return {
            "current_agent": "Supervisor",
            "next_route": "Specialist",
            "specialist_domain": "general"
        }
    
    raw_output = re.sub(r'<think>.*?</think>', '', raw_output, flags=re.DOTALL).strip()
    if raw_output.startswith("```json"):
        raw_output = raw_output[7:-3].strip()
    elif raw_output.startswith("```"):
        raw_output = raw_output[3:-3].strip()
        
    route = "Specialist"
    domain = "general"

    try:
        decision_data = json.loads(raw_output)
        route = decision_data.get("route", "Specialist")
        domain = decision_data.get("domain", "general").lower()
    except Exception:
        route = "Specialist"
        domain = "general"
    
    return {
        "current_agent": "Supervisor",
        "next_route": route,
        "specialist_domain": domain
    }