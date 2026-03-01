from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "Aibou"
    API_V1_STR: str = "/api/v1"
    OPENROUTER_API_KEY: str
    DATABASE_URL: str = "postgresql+asyncpg://aibou:secret@localhost:5432/aibou_db"
    USE_LOCAL_LLM: bool = True
    LOCAL_LLM_URL: str = "http://localhost:11434"
    MODEL_REASONING: str = "deepseek-r1:14b"
    MODEL_CODING: str = "qwen2.5-coder:7b"
    MODEL_CHAT: str = "llama3:8b"
    MODEL_CREATIVE: str = "gemma2:9b"
    MODEL_MATH: str = "johnnyboy/qwen2.5-math-7b"
    MODEL_FINANCE: str = "adaptllm-finance:13b"
    MODEL_SCIENCE: str = "qwen2.5:7b"
    MODEL_EXTRACTOR: str = "llama3:8b"

    class Config:
        env_file = ".env"

settings = Settings()