from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "Aibou"
    API_V1_STR: str = "/api/v1"
    OPENROUTER_API_KEY: str = ""
    DATABASE_URL: str = "postgresql+asyncpg://aibou:secret@localhost:5432/aibou_db"
    USE_LOCAL_LLM: bool = True
    LOCAL_LLM_URL: str = "http://localhost:11434"
    LOCAL_LLM_API_KEY: str = "ollama"  # Configurable via .env
    
    # Active model configuration
    MODEL_ARCHITECT: str = "hf.co/bartowski/Qwen2.5-32B-Instruct-GGUF:Q3_K_M"
    MODEL_REASONING: str = "hf.co/bartowski/Qwen2.5-32B-Instruct-GGUF:Q3_K_M"
    MODEL_CODING: str = "hf.co/bartowski/Qwen2.5-32B-Instruct-GGUF:Q3_K_M"
    MODEL_CHAT: str = "hf.co/bartowski/Qwen2.5-32B-Instruct-GGUF:Q3_K_M"
    MODEL_CREATIVE: str = "hf.co/bartowski/Qwen2.5-32B-Instruct-GGUF:Q3_K_M"
    MODEL_MATH: str = "hf.co/bartowski/Qwen2.5-32B-Instruct-GGUF:Q3_K_M"
    MODEL_FINANCE: str = "hf.co/bartowski/Qwen2.5-32B-Instruct-GGUF:Q3_K_M"
    MODEL_SCIENCE: str = "hf.co/bartowski/Qwen2.5-32B-Instruct-GGUF:Q3_K_M"
    MODEL_EXTRACTOR: str = "hf.co/bartowski/Qwen2.5-32B-Instruct-GGUF:Q3_K_M"


    class Config:
        env_file = ".env"

settings = Settings()