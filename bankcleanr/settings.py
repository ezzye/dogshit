from pathlib import Path
from pydantic import BaseModel
import yaml

CONFIG_PATH = Path.home() / ".bankcleanr" / "config.yml"


class Settings(BaseModel):
    llm_provider: str = "openai"
    api_key: str = ""
    config_path: Path = CONFIG_PATH


def load_settings(path: Path = CONFIG_PATH) -> Settings:
    if path.exists():
        data = yaml.safe_load(path.read_text()) or {}
        return Settings(**data, config_path=path)
    return Settings(config_path=path)


def get_settings() -> Settings:
    return load_settings()
