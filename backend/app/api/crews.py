"""
API endpoints for crew management.
"""
from fastapi import APIRouter, HTTPException, Depends, Query, WebSocket
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from app.core.database import get_db
from app.schemas.crew import (
    CrewCreate, CrewUpdate, CrewResponse,
    WorkflowConfig, CrewMetrics
)
from app.services.crew_service import CrewService
from app.core.errors import CrewError, WorkflowError
from app.core.websocket import ws_manager
from datetime import datetime

router = APIRouter()

@router.post("/", response_model=CrewResponse)
async def create_crew(
    crew_data: CrewCreate,
    db: Session = Depends(get_db)
):
    """Create a new crew."""
    try:
        crew = await CrewService.create_crew(db, crew_data)
        return CrewResponse(
            **crew.dict(),
            agent_count=len(crew.agent_ids),
            success_rate=_calculate_success_rate(crew.metrics),
            total_execution_time=crew.metrics.get("total_execution_time", 0.0)
        )
    except CrewError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{crew_id}", response_model=CrewResponse)
async def get_crew(
    crew_id: str,
    db: Session = Depends(get_db)
):
    """Get crew by ID."""
    try:
        crew = await CrewService.get_crew(db, crew_id)
        if not crew:
            raise HTTPException(status_code=404, detail="Crew not found")
        
        return CrewResponse(
            **crew.dict(),
            agent_count=len(crew.agent_ids),
            success_rate=_calculate_success_rate(crew.metrics),
            total_execution_time=crew.metrics.get("total_execution_time", 0.0)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/", response_model=List[CrewResponse])
async def list_crews(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    """List all crews with pagination."""
    try:
        crews = await CrewService.list_crews(db, skip=skip, limit=limit)
        return [
            CrewResponse(
                **crew.dict(),
                agent_count=len(crew.agent_ids),
                success_rate=_calculate_success_rate(crew.metrics),
                total_execution_time=crew.metrics.get("total_execution_time", 0.0)
            )
            for crew in crews
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{crew_id}/workflow", response_model=Dict[str, Any])
async def execute_workflow(
    crew_id: str,
    workflow_data: Dict[str, Any],
    db: Session = Depends(get_db)
):
    """Execute a workflow with the crew."""
    try:
        result = await CrewService.execute_workflow(db, crew_id, workflow_data)
        return result
    except WorkflowError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.websocket("/{crew_id}/ws")
async def crew_websocket(
    websocket: WebSocket,
    crew_id: str,
    db: Session = Depends(get_db)
):
    """WebSocket connection for real-time crew updates."""
    try:
        # Validate crew exists
        crew = await CrewService.get_crew(db, crew_id)
        if not crew:
            await websocket.close(code=4004, reason="Crew not found")
            return

        # Accept connection
        await ws_manager.connect_crew(crew_id, websocket)
        
        try:
            while True:
                # Handle incoming messages
                data = await websocket.receive_json()
                
                # Process message based on type
                if data.get("type") == "workflow_control":
                    # Handle workflow control commands
                    await _handle_workflow_control(db, crew_id, data, websocket)
                elif data.get("type") == "status_request":
                    # Send current status
                    await _send_crew_status(db, crew_id, websocket)
        except Exception as e:
            await ws_manager.disconnect_crew(crew_id, websocket)
            raise

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/{crew_id}", response_model=CrewResponse)
async def update_crew(
    crew_id: str,
    crew_data: CrewUpdate,
    db: Session = Depends(get_db)
):
    """Update crew configuration."""
    try:
        # Get existing crew
        crew = await CrewService.get_crew(db, crew_id)
        if not crew:
            raise HTTPException(status_code=404, detail="Crew not found")

        # Update crew
        updated_crew = await CrewService.update_crew(db, crew_id, crew_data)
        
        return CrewResponse(
            **updated_crew.dict(),
            agent_count=len(updated_crew.agent_ids),
            success_rate=_calculate_success_rate(updated_crew.metrics),
            total_execution_time=updated_crew.metrics.get("total_execution_time", 0.0)
        )
    except CrewError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{crew_id}/workflow/template", response_model=Dict[str, Any])
async def create_workflow_template(
    crew_id: str,
    template_data: Dict[str, Any],
    db: Session = Depends(get_db)
):
    """Create a workflow template for the crew."""
    try:
        template = await CrewService.create_workflow_template(db, crew_id, template_data)
        return template
    except CrewError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Helper functions

def _calculate_success_rate(metrics: Dict[str, Any]) -> float:
    """Calculate success rate from metrics."""
    total = metrics.get("total_tasks", 0)
    if total == 0:
        return 0.0
    successful = metrics.get("successful_tasks", 0)
    return (successful / total) * 100

async def _handle_workflow_control(
    db: Session,
    crew_id: str,
    data: Dict[str, Any],
    websocket: WebSocket
):
    """Handle workflow control commands with detailed status updates."""
    command = data.get("command")
    try:
        if command == "pause":
            await CrewService.pause_workflow(db, crew_id)
        elif command == "resume":
            await CrewService.resume_workflow(db, crew_id)
        elif command == "stop":
            await CrewService.stop_workflow(db, crew_id)
        elif command == "get_task_progress":
            task_id = data.get("task_id")
            if task_id:
                crew = await CrewService.get_crew(db, crew_id)
                if crew and crew.state.get("task_progress"):
                    await websocket.send_json({
                        "type": "task_progress",
                        "data": crew.state["task_progress"].get(task_id, {})
                    })
                    return
        
        # Send updated status
        await _send_crew_status(db, crew_id, websocket)
    
    except Exception as e:
        await websocket.send_json({
            "type": "error",
            "data": {
                "message": str(e),
                "command": command
            }
        })

async def _send_crew_status(
    db: Session,
    crew_id: str,
    websocket: WebSocket
):
    """Send comprehensive crew status via WebSocket."""
    crew = await CrewService.get_crew(db, crew_id)
    if crew:
        # Get current task progress
        current_task = crew.state.get("current_task")
        task_progress = crew.state.get("task_progress", {})
        
        # Get detailed status
        detailed_status = crew.state.get("detailed_status", {})
        
        # Prepare status response
        status_response = {
            "type": "status_update",
            "data": {
                "state": {
                    "status": crew.state.get("status"),
                    "current_task": current_task,
                    "progress": crew.state.get("progress", 0),
                    "last_update": datetime.utcnow().isoformat()
                },
                "detailed_status": detailed_status,
                "metrics": crew.metrics,
                "performance": {
                    "success_rate": _calculate_success_rate(crew.metrics),
                    "total_execution_time": crew.metrics.get("total_execution_time", 0.0),
                    "task_completion_rate": detailed_status.get("performance_metrics", {}).get("task_completion_rate", 0),
                    "error_rate": detailed_status.get("performance_metrics", {}).get("error_rate", 0)
                }
            }
        }
        
        await websocket.send_json(status_response) 