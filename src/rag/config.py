import os
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, model_validator


class Settings(BaseSettings):
    """
    Application settings, loaded from environment variables or .env file.
    """
    model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8', extra='ignore')

    execution_mode: Literal['offline', 'online'] = Field(default='offline', alias='EXECUTION_MODE')

    # Online mode settings
    google_api_key: str | None = Field(default=None, alias='GOOGLE_API_KEY')

    # Offline mode settings
    ollama_base_url: str = Field(default='http://localhost:11434', alias='OLLAMA_BASE_URL')
    offline_llm_model: str = Field(default='llama3', alias='OFFLINE_LLM_MODEL')
    offline_embedding_model: str = Field(default='all-MiniLM-L6-v2', alias='OFFLINE_EMBEDDING_MODEL')

    # Storage settings
    chroma_persist_dir: str = Field(default='./chroma_db', alias='CHROMA_PERSIST_DIR')
    # documents_dir: str = Field(default='./docs', alias='DOCUMENTS_DIR')
    documents_dir: str = Field(default=r'C:\Users\tanis\Documents\Chitkara_sem5', alias='DOCUMENTS_DIR')

    @model_validator(mode='after')
    def validate_online_mode(self) -> 'Settings':
        """
        Ensures that if execution_mode is 'online', the google_api_key is provided.
        """
        if self.execution_mode == 'online' and not self.google_api_key:
            raise ValueError("GOOGLE_API_KEY must be set when EXECUTION_MODE is 'online'")
        return self


# Global settings instance
settings = Settings()
