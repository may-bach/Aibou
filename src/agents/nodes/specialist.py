import re
from pathlib import Path
from langchain_core.messages import AIMessage, SystemMessage
from langchain_openai import ChatOpenAI
from src.agents.state import AibouState
from src.core.config import settings
from src.agents.tools import aibou_tools, web_search, calculate, get_current_time, read_local_file

PROMPT_PATH = Path(__file__).resolve().parent.parent.parent / "prompts" / "core_aibou.md"
if PROMPT_PATH.exists():
    with open(PROMPT_PATH, "r", encoding="utf-8") as file:
        CORE_AIBOU_PROMPT = file.read()
else:
    CORE_AIBOU_PROMPT = (
        "You are Aibou (相棒), a thoughtful, intelligent, and proactive AI companion. "
        "You communicate with clarity, warmth, and precision."
    )

TOOL_USAGE_PROMPT = """
--- LIVE TOOLS & REAL-TIME SEARCH ---
You have access to live tools:
1. `web_search`: Search the web for recent events, sports results/champions, news, real-time data, or external documentation.
   - CRITICAL: When the user asks about real-world facts, recent competitions, sports race/match winners, current year standings, or live news, ALWAYS call `web_search` to verify rather than relying on outdated static memory.
2. `calculate`: Use for precise mathematical calculations and formulas.
3. `get_current_time`: Check the exact current time, date, or day of the week.
4. `read_local_file`: Inspect files in the project workspace.

Synthesize tool results directly and cleanly into a natural, helpful response without repeating paragraphs or dumping raw JSON.
"""

async def specialist_node(state: AibouState) -> dict:
    domain = state.get("specialist_domain", "general").lower()
    
    # Domain to target model mapping
    if domain == "math":
        target_model = settings.MODEL_MATH
    elif domain == "finance":
        target_model = settings.MODEL_FINANCE
    elif domain == "creative":
        target_model = settings.MODEL_CREATIVE
    elif domain == "reasoning":
        target_model = settings.MODEL_REASONING
    elif domain == "science":
        target_model = settings.MODEL_SCIENCE
    elif domain == "coding":
        target_model = settings.MODEL_CODING
    else:
        target_model = settings.MODEL_CHAT

    print(f"[NODE: SPECIALIST] Invoking domain expert '{domain}' with model '{target_model}'...")

    # Dynamic temperature: lively and conversational for chat/general, precise for math/coding
    temp = 0.2 if domain in ("math", "coding") else 0.75

    llm = ChatOpenAI(
        model=target_model,
        base_url=f"{settings.LOCAL_LLM_URL}/v1",
        api_key=settings.LOCAL_LLM_API_KEY,
        streaming=True,
        temperature=temp
    )

    # For pure casual greetings / creative writing, don't bind tools.
    # For all questions, research, and general queries, bind all tools so real-time lookups work seamlessly!
    if domain in ("greeting", "casual_chat"):
        specialist_llm = llm
        system_instructions = CORE_AIBOU_PROMPT
    else:
        specialist_llm = llm.bind_tools(aibou_tools)
        system_instructions = f"{CORE_AIBOU_PROMPT}\n\n{TOOL_USAGE_PROMPT}"

    messages = list(state.get("messages") or [])
    
    # Clean assembly of prompt messages: avoid duplicate/nested system messages across loops
    non_system_messages = []
    recalled_context_parts = []

    for msg in messages:
        if isinstance(msg, SystemMessage):
            # Extract any RAG/history context without compounding system prompts
            content = msg.content
            if "RECALLED MEMORIES:" in content or "CONVERSATION HISTORY" in content:
                recalled_context_parts.append(content)
        else:
            non_system_messages.append(msg)

    final_system_text = system_instructions
    if recalled_context_parts:
        final_system_text += "\n\n---\n\n" + "\n\n".join(recalled_context_parts)

    prompt_messages = [SystemMessage(content=final_system_text)] + non_system_messages

    response = await specialist_llm.ainvoke(prompt_messages)
    
    # Clean thinking tags if present in the response content
    if isinstance(response.content, str) and "<think>" in response.content:
        clean_content = re.sub(r'<think>.*?</think>', '', response.content, flags=re.DOTALL).strip()
        response.content = clean_content

    return {
        "messages": [response],
        "current_agent": f"Specialist ({domain})"
    }