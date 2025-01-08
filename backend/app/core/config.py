"""
Core configuration settings for the application.
"""
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Application
    APP_NAME: str = "AgentZ"
    DEBUG: bool = False
    API_V1_STR: str = "/api/v1"
    
    # Authentication
    CLERK_SECRET_KEY: str
    CLERK_JWT_VERIFICATION_KEY: str
    
    # Database
    SUPABASE_URL: str
    SUPABASE_KEY: str
    SUPABASE_JWT_SECRET: str
    
    # AI/ML
    OPENAI_API_KEY: Optional[str] = None
    
    # Task Queue
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # Logging
    LOG_LEVEL: str = "INFO"
    
    model_config = SettingsConfigDict(env_file=".env", case_sensitive=True)


settings = Settings() 