from agents import OpenAIChatCompletionsModel
from openai import AsyncOpenAI

from ..config import get_config


# "google/gemma-2-9b-it"


def _create_cheap_model():
    config = get_config()
    if not config.openrouter_key:
        raise ValueError("OPENROUTER_KEY environment variable is required")

    return OpenAIChatCompletionsModel(
        # model="mistralai/ministral-3b",
        model="google/gemma-2-9b-it",
        openai_client=AsyncOpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=config.openrouter_key,
        ),
    )


def _create_model():
    config = get_config()
    if not config.openrouter_key:
        raise ValueError("OPENROUTER_KEY environment variable is required")

    return OpenAIChatCompletionsModel(
        # model="openai/gpt-4.1-nano",
        model="mistralai/mistral-small-3.1-24b-instruct",
        openai_client=AsyncOpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=config.openrouter_key,
        ),
    )


# Model factory functions
MODEL_FACTORIES = {
    "default": _create_model,
    "cheap_model": _create_cheap_model,
}


def create_model_by_key(
    model_key: str, overrides: dict = None
) -> OpenAIChatCompletionsModel:
    """Create a fresh model instance by its key name."""
    if model_key not in MODEL_FACTORIES:
        raise ValueError(
            f"Model '{model_key}' not found. Available models: {list(MODEL_FACTORIES.keys())}"
        )

    # Create fresh instance every time
    return MODEL_FACTORIES[model_key]()
