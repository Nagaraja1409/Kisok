from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT = Path(__file__).resolve().parents[1]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")
    app_name: str = "VAPS AI Agent"
    school_name: str = "The School"
    ai_provider: str = "deterministic"
    groq_api_key: str = ""
    groq_base_url: str = "https://api.groq.com"
    groq_model: str = ""
    deepgram_api_key: str = ""
    voice_agent_enabled: bool = True
    nvidia_api_key: str = ""
    nvidia_base_url: str = "https://integrate.api.nvidia.com/v1"
    nvidia_model: str = "moonshotai/kimi-k3"
    nvidia_reasoning_effort: str = "max"
    nvidia_max_tokens: int = 16384
    ai_timeout_seconds: int = 15
    ai_max_context_records: int = 12
    data_dir: Path = ROOT / "data"


@lru_cache
def get_settings() -> Settings:
    return Settings()
