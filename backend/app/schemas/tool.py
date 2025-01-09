"""Tool schemas."""
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field, validator

class ToolConfig(BaseModel):
    """Tool configuration schema."""
    api_key: Optional[str] = Field(None, description="API key for the tool")
    endpoint: Optional[str] = Field(None, description="API endpoint for the tool")
    max_files: Optional[int] = Field(None, description="Maximum number of files to process")
    supported_languages: Optional[List[str]] = Field(None, description="List of supported programming languages")
    timeout: Optional[int] = Field(default=30, description="Tool execution timeout in seconds")
    retry_attempts: Optional[int] = Field(default=3, description="Number of retry attempts")
    custom_config: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional tool-specific configuration")

    @validator("api_key")
    def validate_api_key(cls, v):
        """Validate API key if provided."""
        if v is not None and not v:
            raise ValueError("API key cannot be empty")
        return v

    @validator("max_files")
    def validate_max_files(cls, v):
        """Validate max_files if provided."""
        if v is not None and v <= 0:
            raise ValueError("max_files must be positive")
        return v

    @validator("timeout")
    def validate_timeout(cls, v):
        """Validate timeout."""
        if v <= 0:
            raise ValueError("timeout must be positive")
        return v

    @validator("retry_attempts")
    def validate_retry_attempts(cls, v):
        """Validate retry_attempts."""
        if v < 0:
            raise ValueError("retry_attempts cannot be negative")
        return v

class Tool(BaseModel):
    """Tool schema."""
    name: str = Field(..., description="Tool name")
    description: str = Field(..., description="Tool description")
    config: ToolConfig = Field(default_factory=ToolConfig, description="Tool configuration")
    enabled: bool = Field(default=True, description="Whether the tool is enabled")
    requires_auth: bool = Field(default=False, description="Whether the tool requires authentication")
    version: str = Field(default="1.0.0", description="Tool version")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional tool metadata")

    @validator("name")
    def validate_name(cls, v):
        """Validate tool name."""
        if not v.strip():
            raise ValueError("Tool name cannot be empty")
        if not v.isalnum() and not "_" in v:
            raise ValueError("Tool name must be alphanumeric with optional underscores")
        return v.lower()

    @validator("description")
    def validate_description(cls, v):
        """Validate tool description."""
        if not v.strip():
            raise ValueError("Tool description cannot be empty")
        if len(v) < 10:
            raise ValueError("Tool description must be at least 10 characters")
        return v

    class Config:
        """Pydantic config."""
        json_encoders = {
            set: list  # Convert sets to lists for JSON serialization
        } 