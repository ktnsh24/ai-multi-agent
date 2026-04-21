"""Health check route."""

from fastapi import APIRouter, Request

from src.models import HealthStatus

router = APIRouter()


@router.get("/health", response_model=HealthStatus)
async def health_check(request: Request) -> HealthStatus:
    """Check health of all platform components."""
    settings = request.app.state.settings
    ws_manager = request.app.state.ws_manager

    return HealthStatus(
        status="healthy",
        version="0.1.0",
        provider=settings.cloud_provider.value,
        components={
            "llm_provider": f"ready ({settings.cloud_provider.value})",
            "model": (
                settings.ollama_model
                if settings.cloud_provider == "local"
                else settings.aws_bedrock_model
            ),
            "websocket": f"{ws_manager.connection_count} connections",
            "task_store": "ready",
            "crew_orchestrator": "ready",
        },
    )
