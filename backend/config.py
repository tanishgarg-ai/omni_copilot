from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


class Settings(BaseSettings):
    execution_mode: str = "offline"
    database_url: str = "sqlite+aiosqlite:///./omni_copilot.db"
    secret_key: str = "replace_me_in_production"
    api_v1_prefix: str = "/api"

    google_api_key: Optional[str] = None
    ollama_base_url: str = "http://localhost:11434"
    offline_llm_model: str = "llama3"
    offline_embedding_model: str = "all-MiniLM-L6-v2"

    chroma_persist_dir: str = "./chroma_db"
    documents_dir: str = "./docs"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()