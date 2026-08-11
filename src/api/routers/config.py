from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from langchain_openai import ChatOpenAI
from src.core.config import settings
import httpx

router = APIRouter(prefix="/config", tags=["Configuration"])

class ProviderSettings(BaseModel):
    use_local_llm: bool
    api_key: str | None = None
    cloud_model: str = "moonshotai/kimi-k3"
    local_model: str = "qwen2.5:14b"

class TestKeyRequest(BaseModel):
    api_key: str
    model: str = "moonshotai/kimi-k3"

@router.get("/settings")
async def get_settings():
    return {
        "use_local_llm": settings.USE_LOCAL_LLM,
        "has_api_key": bool(settings.OPENROUTER_API_KEY),
        "api_key_masked": f"...{settings.OPENROUTER_API_KEY[-4:]}" if len(settings.OPENROUTER_API_KEY) > 6 else "",
        "active_chat_model": settings.MODEL_CHAT,
        "local_llm_url": settings.LOCAL_LLM_URL,
    }

@router.get("/local-models")
async def get_local_models():
    """Fetch all models currently installed in the user's Ollama library."""
    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            res = await client.get(f"{settings.LOCAL_LLM_URL}/api/tags")
            if res.status_code == 200:
                data = res.json()
                models = [m.get("name") for m in data.get("models", []) if m.get("name")]
                return {"models": models}
    except Exception:
        pass
    return {"models": []}


@router.post("/test-key")
async def test_api_key(req: TestKeyRequest):
    if not req.api_key or not req.api_key.strip():
        raise HTTPException(status_code=400, detail="API key cannot be empty.")
    
    clean_key = req.api_key.strip()

    try:
        # Test 1 token completion via OpenRouter / OpenAI API
        llm = ChatOpenAI(
            model=req.model,
            base_url="https://openrouter.ai/api/v1",
            api_key=clean_key,
            temperature=0.1,
            max_tokens=5,
            timeout=10.0
        )
        response = await llm.ainvoke("ping")
        return {
            "success": True,
            "message": "Connection successful! API key is valid and responsive.",
            "sample": response.content.strip()
        }
    except Exception as e:
        err_msg = str(e)
        if "401" in err_msg or "Unauthorized" in err_msg:
            detail = "Invalid API Key: Authentication failed (401 Unauthorized)."
        elif "402" in err_msg or "credits" in err_msg.lower():
            detail = "Insufficient credits on this API account."
        else:
            detail = f"Connection test failed: {err_msg[:120]}"
        raise HTTPException(status_code=400, detail=detail)

@router.post("/save")
async def save_settings(req: ProviderSettings):
    settings.USE_LOCAL_LLM = req.use_local_llm
    if req.api_key is not None:
        settings.OPENROUTER_API_KEY = req.api_key.strip()
    
    if req.use_local_llm:
        settings.MODEL_CHAT = req.local_model
    else:
        settings.MODEL_CHAT = req.cloud_model

    return {
        "success": True,
        "use_local_llm": settings.USE_LOCAL_LLM,
        "active_model": settings.MODEL_CHAT
    }
