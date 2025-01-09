"""Configuration settings for the application."""
from pydantic_settings import BaseSettings
from typing import Optional, Dict, Any, List
import os
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    """Application settings."""
    PROJECT_NAME: str = "AgentZ"
    VERSION: str = "0.1.0"
    DESCRIPTION: str = "Agent Management System"
    API_V1_STR: str = "/api/v1"
    
    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./dev.db")
    
    # JWT
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8  # 8 days
    
    # CORS
    BACKEND_CORS_ORIGINS: List[str] = ["*"]
    
    # LLM
    OPENAI_API_KEY: Optional[str] = os.getenv("OPENAI_API_KEY")
    DEFAULT_MODEL: str = "gpt-4"
    DEFAULT_TEMPERATURE: float = 0.7
    
    # Agent defaults
    DEFAULT_MAX_ITERATIONS: int = 5
    DEFAULT_MEMORY_SIZE: int = 100
    ALLOW_DELEGATION: bool = True
    
    # Logging
    LOG_LEVEL: str = "INFO"
    
    # Redis settings
    REDIS_URL: str = "redis://localhost:6379/0"
    
    class Config:
        """Pydantic config."""
        case_sensitive = True

settings = Settings() 