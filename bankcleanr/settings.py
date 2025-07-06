from pathlib import Path
from pydantic import BaseModel
import yaml
import os

CONFIG_PATH = Path.home() / ".bankcleanr" / "config.yml"


class Settings(BaseModel):
    llm_provider: str = "openai"
    api_key: str = ""
    config_path: Path = CONFIG_PATH


def load_settings(path: Path = CONFIG_PATH) -> Settings:
    data = {}
    if path.exists():
        data = yaml.safe_load(path.read_text()) or {}
    settings = Settings(**data, config_path=path)
    env_map = {
        "openai": "OPENAI_API_KEY",
        "gemini": "GEMINI_API_KEY",
        "mistral": "MISTRAL_API_KEY",
        "anthropic": "ANTHROPIC_API_KEY",
        "bfl": "BFL_API_KEY",
    }
    provider = settings.llm_provider.lower()
    env_var = env_map.get(provider)
    if env_var and os.getenv(env_var):
        settings.api_key = os.getenv(env_var)
    elif provider == "bfl" and os.getenv("OPENAI_API_KEY"):
        # Fall back to OpenAI credentials when BFL key is missing
        settings.api_key = os.getenv("OPENAI_API_KEY")
    return settings


def get_settings() -> Settings:
    return load_settings()
