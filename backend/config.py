"""Configuration management for MineContext-v2."""

import os
from pathlib import Path
from typing import Optional

import yaml
from pydantic import Field
from pydantic_settings import BaseSettings


class CaptureConfig(BaseSettings):
    """Screenshot capture configuration."""

    interval_seconds: int = Field(default=40, description="Base screenshot capture interval")
    auto_start: bool = Field(default=False, description="Auto-start capture on launch")
    screenshot_dir: str = Field(default="./screenshots", description="Screenshot storage directory")
    max_screenshots: int = Field(default=2000, description="Maximum screenshots to store")
    deduplicate: bool = Field(default=True, description="Enable deduplication")
    hash_threshold: int = Field(default=5, description="Perceptual hash difference threshold")
    # Random interval configuration
    random_interval: bool = Field(default=True, description="Enable random interval between captures")
    min_interval_seconds: int = Field(default=20, description="Minimum interval for random capture")
    max_interval_seconds: int = Field(default=60, description="Maximum interval for random capture")


class StorageConfig(BaseSettings):
    """Storage configuration."""

    database_path: str = Field(default="./data/context.db", description="SQLite database path")
    compression: bool = Field(default=True, description="Enable image compression")
    quality: int = Field(default=85, description="JPEG compression quality (1-100)")


class AIConfig(BaseSettings):
    """AI integration configuration."""

    enabled: bool = Field(default=False, description="Enable AI features")
    provider: str = Field(default="openai", description="AI provider (openai/anthropic)")
    model: str = Field(default="gpt-4-vision-preview", description="Model name")
    auto_analyze: bool = Field(default=False, description="Auto-analyze screenshots")
    analyze_on_demand: bool = Field(default=True, description="Allow on-demand analysis")


class EmbeddingsConfig(BaseSettings):
    """Embeddings configuration."""

    enabled: bool = Field(default=True, description="Enable embedding generation")
    model: str = Field(default="all-MiniLM-L6-v2", description="Sentence transformer model")
    auto_generate: bool = Field(default=True, description="Auto-generate embeddings after analysis")
    batch_size: int = Field(default=32, description="Batch size for embedding generation")


class VectorDBConfig(BaseSettings):
    """Vector database configuration."""

    enabled: bool = Field(default=True, description="Enable vector database")
    path: str = Field(default="./data/chroma_db", description="ChromaDB storage path")
    collection_name: str = Field(default="screenshot_contexts", description="Collection name")
    similarity_threshold: float = Field(default=0.7, description="Similarity threshold (0-1)")
    max_results: int = Field(default=10, description="Max results for similarity search")


class ContextResurfacingConfig(BaseSettings):
    """Context resurfacing configuration."""

    enabled: bool = Field(default=True, description="Enable context resurfacing")
    relevance_decay_days: int = Field(default=30, description="Relevance decay period in days")
    min_similarity: float = Field(default=0.6, description="Minimum similarity for resurfacing")
    max_suggestions: int = Field(default=5, description="Max proactive suggestions")


class ServerConfig(BaseSettings):
    """Server configuration."""

    host: str = Field(default="127.0.0.1", description="Server host")
    port: int = Field(default=8000, description="Server port")
    debug: bool = Field(default=False, description="Debug mode")

    class Config:
        env_prefix = "SERVER_"


class Settings(BaseSettings):
    """Main application settings."""

    capture: CaptureConfig = Field(default_factory=CaptureConfig)
    storage: StorageConfig = Field(default_factory=StorageConfig)
    ai: AIConfig = Field(default_factory=AIConfig)
    embeddings: EmbeddingsConfig = Field(default_factory=EmbeddingsConfig)
    vector_db: VectorDBConfig = Field(default_factory=VectorDBConfig)
    context_resurfacing: ContextResurfacingConfig = Field(default_factory=ContextResurfacingConfig)
    server: ServerConfig = Field(default_factory=ServerConfig)

    # Environment variables
    openai_api_key: Optional[str] = Field(default=None, description="OpenAI API key")
    anthropic_api_key: Optional[str] = Field(default=None, description="Anthropic API key")
    openrouter_api_key: Optional[str] = Field(default=None, description="OpenRouter API key")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


def load_config(config_path: str = "config/config.yaml") -> Settings:
    """Load configuration from YAML file and environment variables.

    Args:
        config_path: Path to the YAML configuration file

    Returns:
        Settings object with loaded configuration
    """
    settings = Settings()

    # Load YAML config if it exists
    if os.path.exists(config_path):
        with open(config_path, "r") as f:
            config_data = yaml.safe_load(f)

        if config_data:
            # Update settings from YAML
            if "capture" in config_data:
                settings.capture = CaptureConfig(**config_data["capture"])
            if "storage" in config_data:
                settings.storage = StorageConfig(**config_data["storage"])
            if "ai" in config_data:
                settings.ai = AIConfig(**config_data["ai"])
            if "embeddings" in config_data:
                settings.embeddings = EmbeddingsConfig(**config_data["embeddings"])
            if "vector_db" in config_data:
                settings.vector_db = VectorDBConfig(**config_data["vector_db"])
            if "context_resurfacing" in config_data:
                settings.context_resurfacing = ContextResurfacingConfig(**config_data["context_resurfacing"])
            if "server" in config_data:
                settings.server = ServerConfig(**config_data["server"])

    # Ensure directories exist
    Path(settings.storage.database_path).parent.mkdir(parents=True, exist_ok=True)
    Path(settings.capture.screenshot_dir).mkdir(parents=True, exist_ok=True)
    Path(settings.vector_db.path).mkdir(parents=True, exist_ok=True)

    return settings


# Global settings instance
settings = load_config()
