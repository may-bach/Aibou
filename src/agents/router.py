from openai import AsyncOpenAI
from pathlib import Path
import re
from src.core.config import settings

router_client = AsyncOpenAI(
    base_url=f"{settings.LOCAL_LLM_URL}/v1",
    api_key="ollama",
)

ROUTER_PROMPT_PATH = Path(__file__).parent.parent / "prompts" / "router.md"
with open(ROUTER_PROMPT_PATH, "r", encoding="utf-8") as file:
    ROUTER_PROMPT = file.read()

async def route_prompt(user_text: str) -> str:
    """Analyzes the prompt and returns the specific model string from the registry."""
    try:
        response = await router_client.chat.completions.create(
            model=settings.MODEL_CHAT,
            messages=[
                {"role": "system", "content": ROUTER_PROMPT},
                {"role": "user", "content": user_text}
            ],
            temperature=0.0,
        )
        
        decision = response.choices[0].message.content
        decision = re.sub(r'<think>.*?</think>', '', decision, flags=re.DOTALL).strip().upper()
        
        if "REASONING" in decision:
            return settings.MODEL_REASONING
        elif "CODING" in decision:
            return settings.MODEL_CODING
        elif "CREATIVE" in decision:
            return settings.MODEL_CREATIVE
        elif "MATH" in decision:
            return settings.MODEL_MATH
        elif "FINANCE" in decision:
            return settings.MODEL_FINANCE
        elif "SCIENCE" in decision:
            return settings.MODEL_SCIENCE
        else:
            return settings.MODEL_CHAT  #default
            
    except Exception as e:
        print(f"\n[ROUTER ERROR] Routing failed, falling back to Chat model: {e}\n")
        return settings.MODEL_CHAT