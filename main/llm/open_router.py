import yaml
import os
from pathlib import Path
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.openai import OpenAIProvider
from typing import Literal

# Define model types
ModelType = Literal["free", "fast", "smart"]


def load_openrouter_settings() -> dict:
    """Load OpenRouter settings from YAML file."""
    settings_path = Path(__file__).parent / "open_router_settings.yaml"
    with open(settings_path, "r") as f:
        return yaml.safe_load(f)


def load_api_keys() -> dict:
    """Load API keys from the keys YAML file."""
    keys_path = Path(__file__).parent.parent.parent / "keys" / "key.yaml"
    with open(keys_path, "r") as f:
        return yaml.safe_load(f)


def get_openrouter_model_name(model_type: ModelType) -> str:
    """Get the OpenRouter model name for a given model type."""
    settings = load_openrouter_settings()

    model_mapping = {
        "free": settings["FREE_MODEL"],
        "fast": settings["FAST_MODEL"],
        "smart": settings["SMART_MODEL"],
    }

    return model_mapping[model_type]


def create_openrouter_model(model_type: ModelType) -> OpenAIChatModel:
    """Create an OpenRouter model instance for the specified model type."""
    settings = load_openrouter_settings()
    keys = load_api_keys()

    model_name = get_openrouter_model_name(model_type)

    return OpenAIChatModel(
        model_name=model_name,
        provider=OpenAIProvider(
            base_url=settings["OPENROUTER_BASE_URL"], api_key=keys["openrouter_key"]
        ),
    )


def get_model_display_name(model_type: ModelType) -> str:
    """Get a display name for the model type and actual model."""
    model_name = get_openrouter_model_name(model_type)
    return f"{model_type.upper()} ({model_name})"
