"""Configuration management for the researcher application."""
import os
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    default_model: str = os.getenv("DEFAULT_MODEL", "gpt-4o")
    default_embedding_model: str = os.getenv("DEFAULT_EMBEDDING_MODEL", "text-embedding-3-small")
    database_path: str = "data/database.json"
    graph_db_path: str = "data/graph.json"
    
    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"  # Ignore extra fields from .env


settings = Settings()

