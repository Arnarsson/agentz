from typing import Optional
from fastapi import Depends, HTTPException, status

async def get_current_user():
    """Mock authentication for testing."""
    return {
        "id": "test-user",
        "email": "test@example.com",
        "roles": ["admin"]
    } 