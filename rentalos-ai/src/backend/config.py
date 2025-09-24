"""Application configuration module."""

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Runtime configuration for the FastAPI application."""

    app_name: str = Field(default="RentalOS-AI", description="Human friendly application name")
    environment: str = Field(default="development", description="Runtime environment name")
    enable_mock_data: bool = Field(
        default=True, description="Toggle for Stage 1 deterministic data"
    )

    model_config = {
        "env_prefix": "rentalos_",
        "case_sensitive": False,
    }


settings = Settings()
