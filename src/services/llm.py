# LEGACY / UNUSED: This service was used before the LangGraph swarm was introduced.
# generate_chat_response() is no longer called anywhere in the app.
# Kept for reference. Safe to delete in a future cleanup pass.
from openai import AsyncOpenAI
from pathlib import Path
import re
from src.core.config import settings
from src.models.memory import Message

chat_llm_client = AsyncOpenAI(
    base_url=f"{settings.LOCAL_LLM_URL}/v1",
    api_key="ollama",
)

PROMPT_PATH = Path(__file__).parent.parent / "prompts" / "core_aibou.md"
with open(PROMPT_PATH, "r", encoding="utf-8") as file:
    AIBOU_PROMPT = file.read()

# ADDED model_name parameter here
async def generate_chat_response(chat_history: list[Message], injected_context: str, model_name: str) -> str:
    """Builds the payload, strips <think> tags from history, and queries the LLM."""
    
    system_prompt = AIBOU_PROMPT
    if injected_context != "":
        system_prompt += f"\n\n--- RELEVANT CONTEXT FROM USER'S MEMORY ---\n{injected_context}"

    messages_payload = [
        {"role": "system", "content": system_prompt}
    ]

    for msg in chat_history:
        if msg.role == "assistant":
            clean_content = re.sub(r'<think>.*?</think>', '', msg.content, flags=re.DOTALL)
            clean_content = clean_content.replace("</think>", "").strip()
            messages_payload.append({"role": msg.role, "content": clean_content})
        else:
            messages_payload.append({"role": msg.role, "content": msg.content})

    response = await chat_llm_client.chat.completions.create(
        model=model_name,
        messages=messages_payload
    )

    return response.choices[0].message.content