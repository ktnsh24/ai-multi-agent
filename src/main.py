"""FastAPI application factory for the multi-agent platform."""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.agents.crew import CrewOrchestrator
from src.config import Settings
from src.llm.provider import create_llm_provider
from src.tasks.store import create_task_store
from src.websocket.manager import WebSocketManager


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize and teardown application resources."""
    settings = Settings()

    logging.basicConfig(level=getattr(logging, settings.log_level))
    logger = logging.getLogger(__name__)

    logger.info(
        "Starting multi-agent platform (provider=%s)",
        settings.cloud_provider.value,
    )

    # Create components
    llm_provider = create_llm_provider(settings)
    llm = llm_provider.create_chat_model()

    app.state.settings = settings
    app.state.llm_provider = llm_provider
    app.state.crew_orchestrator = CrewOrchestrator(llm=llm, verbose=settings.crew_verbose)
    app.state.task_store = create_task_store()
    app.state.ws_manager = WebSocketManager()

    logger.info(
        "Platform ready (provider=%s, model=%s)",
        llm_provider.get_provider_name(),
        settings.ollama_model if settings.cloud_provider.value == "local" else "cloud",
    )

    yield

    logger.info("Shutting down multi-agent platform")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title="AI Multi-Agent Platform",
        description="Multi-agent collaboration with CrewAI, WebSockets, and real-time monitoring",
        version="0.1.0",
        lifespan=lifespan,
    )

    # CORS for Next.js frontend
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3000", "http://localhost:8400"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Routes
    from src.routes.health import router as health_router
    from src.routes.tasks import router as tasks_router
    from src.routes.ws import router as ws_router

    app.include_router(health_router)
    app.include_router(tasks_router)
    app.include_router(ws_router)

    return app


def get_ws_manager():
    """Helper to access WebSocket manager from routes."""
    pass


def start() -> None:
    """CLI entry point for `poetry run start` — launches uvicorn."""
    import uvicorn

    uvicorn.run(
        "src.main:create_app",
        factory=True,
        host="0.0.0.0",
        port=8400,
        reload=True,
    )
