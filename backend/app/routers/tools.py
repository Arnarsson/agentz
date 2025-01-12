"""Tool management router."""
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime

from app.core.auth import get_current_user
from app.core.database import get_db
from app.services.tools import ToolService, ToolConfig
from app.schemas.user import User

router = APIRouter(prefix="/tools", tags=["tools"])

@router.get("/", response_model=List[ToolConfig])
async def list_tools(
    current_user: User = Depends(get_current_user)
):
    """List all available tools."""
    return ToolService.get_default_tools()

@router.get("/{tool_name}", response_model=Dict[str, Any])
async def get_tool_info(
    tool_name: str,
    current_user: User = Depends(get_current_user)
):
    """Get detailed information about a specific tool."""
    tool_info = ToolService.get_tool_documentation(tool_name)
    if "error" in tool_info:
        raise HTTPException(status_code=404, detail="Tool not found")
    return tool_info

@router.post("/{tool_name}/execute")
async def execute_tool(
    tool_name: str,
    parameters: Dict[str, Any],
    agent_id: str,
    current_user: User = Depends(get_current_user)
):
    """Execute a tool with given parameters."""
    try:
        result = await ToolService.execute_tool(
            tool_name=tool_name,
            parameters=parameters,
            agent_id=agent_id
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{tool_name}/metrics")
async def get_tool_metrics(
    tool_name: str,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    current_user: User = Depends(get_current_user)
):
    """Get usage metrics for a specific tool."""
    return ToolService.get_tool_usage_metrics(
        tool_name=tool_name,
        start_time=start_time,
        end_time=end_time
    )

@router.post("/{tool_name}/validate")
async def validate_tool_config(
    tool_name: str,
    config: ToolConfig,
    current_user: User = Depends(get_current_user)
):
    """Validate a tool configuration."""
    is_valid = ToolService.validate_tool_config(config)
    if not is_valid:
        raise HTTPException(status_code=400, detail="Invalid tool configuration")
    return {"status": "valid", "config": config}

@router.get("/{tool_name}/permissions")
async def get_tool_permissions(
    tool_name: str,
    current_user: User = Depends(get_current_user)
):
    """Get required permissions for a tool."""
    return {
        "tool_name": tool_name,
        "required_permissions": ToolService.get_tool_permissions(tool_name)
    } 