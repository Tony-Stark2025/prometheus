"""
Configuration module for Prometheus application settings.
"""

from typing import List, Optional
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Core Application Settings
    app_name: str = "Prometheus Chief of Staff"
    environment: str = Field(default="development", env="ENVIRONMENT")
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    host: str = Field(default="0.0.0.0", env="HOST")
    port: int = Field(default=8000, env="PORT")

    # Gemini LLM Settings
    gemini_api_key: Optional[str] = Field(default=None, env="GEMINI_API_KEY")
    gemini_model: str = Field(default="gemini-2.5-flash", env="GEMINI_MODEL")
    gemini_fallback_model: str = Field(default="gemini-1.5-flash", env="GEMINI_FALLBACK_MODEL")

    # Persistence / Database
    database_url: str = Field(
        default="sqlite+aiosqlite:///./prometheus_state.db",
        env="DATABASE_URL",
    )

    # Observability & Thresholds
    stale_pr_hours_threshold: int = Field(default=48, env="STALE_PR_HOURS_THRESHOLD")
    ci_failure_threshold_count: int = Field(default=2, env="CI_FAILURE_THRESHOLD_COUNT")
    default_org_scope: List[str] = Field(
        default_factory=lambda: ["engineering", "platform"],
        env="DEFAULT_ORG_SCOPE",
    )

    # Human in the Loop (HITL) Enforcement
    enforce_human_in_the_loop: bool = Field(default=True, env="ENFORCE_HUMAN_IN_THE_LOOP")

    # Integrations
    github_token: Optional[str] = Field(default=None, env="GITHUB_TOKEN")
    jira_api_token: Optional[str] = Field(default=None, env="JIRA_API_TOKEN")
    jira_instance_url: Optional[str] = Field(default=None, env="JIRA_INSTANCE_URL")
    slack_bot_token: Optional[str] = Field(default=None, env="SLACK_BOT_TOKEN")


settings = Settings()
