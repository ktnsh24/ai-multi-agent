"""Configuration for the multi-agent platform."""

from enum import Enum

from pydantic_settings import BaseSettings


class CloudProvider(str, Enum):
    AWS = "aws"
    AZURE = "azure"
    LOCAL = "local"


class AppEnvironment(str, Enum):
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # App
    cloud_provider: CloudProvider = CloudProvider.LOCAL
    app_env: AppEnvironment = AppEnvironment.DEVELOPMENT
    log_level: str = "INFO"

    # LLM - Ollama (local)
    ollama_model: str = "llama3.2"
    ollama_base_url: str = "http://localhost:11434"

    # LLM - AWS Bedrock
    aws_region: str = "eu-west-1"
    aws_bedrock_model: str = "anthropic.claude-3-5-sonnet-20241022-v2:0"

    # LLM - Azure OpenAI
    azure_openai_endpoint: str = ""
    azure_openai_api_key: str = ""
    azure_openai_deployment: str = "gpt-4o"
    azure_openai_api_version: str = "2024-02-01"

    # WebSocket
    ws_port: int = 8401

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # Database
    database_url: str = "sqlite+aiosqlite:///./data/multi_agent.db"

    # Portfolio integration
    gateway_url: str = "http://localhost:8100"
    agent_url: str = "http://localhost:8200"
    mcp_server_url: str = "http://localhost:8300"

    # n8n
    n8n_webhook_url: str = ""

    # CrewAI
    max_iterations: int = 15
    crew_verbose: bool = True

    model_config = {"env_file": ".env", "case_sensitive": False}
