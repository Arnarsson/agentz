from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings."""
    
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "CrewAI Web"
    
    # CORS Configuration
    BACKEND_CORS_ORIGINS: list[str] = ["http://localhost:3000"]
    
    # OpenAI Configuration (for CrewAI)
    OPENAI_API_KEY: str = ""
    
    class Config:
        case_sensitive = True
        env_file = ".env"


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()

settings = get_settings() 