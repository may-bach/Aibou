from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    PROJECT_NAME: str = "Aibou"
    API_V1_STR: str = "/api/v1"
    
    DATABASE_URL: str = "sqlite+aiosqlite:///./aibou.db" 
    
    USE_LOCAL_LLM: bool = False 
    
    GEMINI_API_KEY: str | None = None
    ANTHROPIC_API_KEY: str | None = None
    
    LOCAL_LLM_URL: str = "http://localhost:11434"
    LOCAL_MODEL_NAME: str = "deepseek-r1:8b"

    class Config:
        env_file = ".env"

settings = Settings()