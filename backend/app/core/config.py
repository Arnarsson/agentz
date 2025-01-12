"""Configuration settings for the application."""
from pydantic_settings import BaseSettings
from typing import Optional, Dict, Any, List
import os
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    """Application settings."""
    # Application
    PROJECT_NAME: str = "AgentZ"
    VERSION: str = "0.1.0"
    DESCRIPTION: str = "Agent Management System"
    API_V1_STR: str = "/api/v1"
    APP_NAME: str = "AgentZ"
    
    # Environment
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    IS_TEST: bool = os.getenv("IS_TEST", "false").lower() == "true"
    
    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./data/dev.db")
    
    # Authentication
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8  # 8 days
    CLERK_SECRET_KEY: Optional[str] = os.getenv("CLERK_SECRET_KEY")
    CLERK_JWT_VERIFICATION_KEY: Optional[str] = os.getenv("CLERK_JWT_VERIFICATION_KEY")
    
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
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    # Redis settings
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    REDIS_MAX_CONNECTIONS: int = 10
    
    # WebSocket settings
    WS_MESSAGE_QUEUE_SIZE: int = 100
    WS_HEARTBEAT_INTERVAL: int = 30
    
    class Config:
        """Pydantic config."""
        case_sensitive = True
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "allow"  # Allow extra fields

settings = Settings() 