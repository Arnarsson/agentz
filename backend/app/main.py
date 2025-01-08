from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# Set up CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "healthy"}

# Import and include API routers
from app.api.agents import router as agents_router
from app.api.tasks import router as tasks_router
from app.api.workflows import router as workflows_router

app.include_router(agents_router, prefix=f"{settings.API_V1_STR}/agents", tags=["agents"])
app.include_router(tasks_router, prefix=f"{settings.API_V1_STR}/tasks", tags=["tasks"])
app.include_router(workflows_router, prefix=f"{settings.API_V1_STR}/workflows", tags=["workflows"]) 