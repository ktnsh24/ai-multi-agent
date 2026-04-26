"""
AI Multi-Agent — Shared Test Fixtures

Reusable fixtures for all test files. Components are mocked on app.state
(bypassing lifespan) so no Ollama/CrewAI is needed.
"""

from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from src.tasks.store import InMemoryTaskStore
from src.websocket.manager import WebSocketManager


@pytest.fixture
def mock_settings() -> MagicMock:
    """Mock settings — local provider."""
    settings = MagicMock()
    settings.cloud_provider = MagicMock()
    settings.cloud_provider.value = "local"
    settings.ollama_model = "llama3.2"
    settings.aws_bedrock_model = "anthropic.claude-3-5-sonnet"
    return settings


@pytest.fixture
def mock_llm_provider() -> MagicMock:
    """Mock LLM provider."""
    llm = MagicMock()
    llm.get_provider_name.return_value = "local"
    return llm


@pytest.fixture
def mock_crew_orchestrator() -> MagicMock:
    """Mock CrewAI orchestrator."""
    crew = MagicMock()
    return crew


@pytest.fixture
def task_store() -> InMemoryTaskStore:
    """Real in-memory task store."""
    return InMemoryTaskStore()


@pytest.fixture
def ws_manager() -> WebSocketManager:
    """Real WebSocket manager."""
    return WebSocketManager()


@pytest.fixture
def app(
    mock_settings: MagicMock,
    mock_llm_provider: MagicMock,
    mock_crew_orchestrator: MagicMock,
    task_store: InMemoryTaskStore,
    ws_manager: WebSocketManager,
):
    """FastAPI app with all components on app.state."""
    from src.main import create_app

    application = create_app()
    application.state.settings = mock_settings
    application.state.llm_provider = mock_llm_provider
    application.state.crew_orchestrator = mock_crew_orchestrator
    application.state.task_store = task_store
    application.state.ws_manager = ws_manager
    return application


@pytest.fixture
def client(app) -> TestClient:
    """Test client with all mocks wired."""
    with TestClient(app, raise_server_exceptions=False) as c:
        yield c
