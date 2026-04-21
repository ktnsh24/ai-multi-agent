"""LLM provider layer — Strategy pattern for multi-cloud support."""

from abc import ABC, abstractmethod

from langchain_core.language_models import BaseChatModel

from src.config import CloudProvider, Settings


class BaseLLMProvider(ABC):
    """Abstract base class for LLM providers."""

    @abstractmethod
    def create_chat_model(self) -> BaseChatModel:
        """Create and return a LangChain chat model."""
        ...

    @abstractmethod
    def get_provider_name(self) -> str:
        """Return human-readable provider name."""
        ...


class BedrockProvider(BaseLLMProvider):
    """AWS Bedrock provider using Claude."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def create_chat_model(self) -> BaseChatModel:
        from langchain_aws import ChatBedrock

        return ChatBedrock(
            model_id=self.settings.aws_bedrock_model,
            region_name=self.settings.aws_region,
            model_kwargs={"temperature": 0.3, "max_tokens": 4096},
        )

    def get_provider_name(self) -> str:
        return f"aws ({self.settings.aws_bedrock_model})"


class AzureOpenAIProvider(BaseLLMProvider):
    """Azure OpenAI provider."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def create_chat_model(self) -> BaseChatModel:
        from langchain_openai import AzureChatOpenAI

        return AzureChatOpenAI(
            azure_endpoint=self.settings.azure_openai_endpoint,
            api_key=self.settings.azure_openai_api_key,
            azure_deployment=self.settings.azure_openai_deployment,
            api_version=self.settings.azure_openai_api_version,
            temperature=0.3,
            max_tokens=4096,
        )

    def get_provider_name(self) -> str:
        return f"azure ({self.settings.azure_openai_deployment})"


class OllamaProvider(BaseLLMProvider):
    """Ollama local provider."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def create_chat_model(self) -> BaseChatModel:
        from langchain_ollama import ChatOllama

        return ChatOllama(
            model=self.settings.ollama_model,
            base_url=self.settings.ollama_base_url,
            temperature=0.3,
        )

    def get_provider_name(self) -> str:
        return f"local ({self.settings.ollama_model})"


def create_llm_provider(settings: Settings) -> BaseLLMProvider:
    """Factory function to create the appropriate LLM provider."""
    providers = {
        CloudProvider.AWS: BedrockProvider,
        CloudProvider.AZURE: AzureOpenAIProvider,
        CloudProvider.LOCAL: OllamaProvider,
    }
    provider_class = providers[settings.cloud_provider]
    return provider_class(settings)
