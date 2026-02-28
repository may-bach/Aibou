from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "Aibou"
    API_V1_STR: str = "/api/v1"
    OPENROUTER_API_KEY: str
    DATABASE_URL: str = "sqlite+aiosqlite:///./Storage/relational/aibou.db" 
    USE_LOCAL_LLM: bool = True
    LOCAL_LLM_URL: str = "http://localhost:11434"
    LOCAL_MODEL_NAME: str = "deepseek-r1:14b"

    class Config:
        env_file = ".env"

settings = Settings()