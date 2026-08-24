"""
Configuration module for Prometheus Enterprise Observability & Multi-Agent Platform.
Supports Gemini 3.x Flash model tiers, multi-key keyring rotation, MCP, and Google Cloud Run.
"""

from typing import List, Optional, Set
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Core Application & Google Cloud Run Settings
    app_name: str = "Prometheus Chief of Staff"
    environment: str = Field(default="development", env="ENVIRONMENT")
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    host: str = Field(default="0.0.0.0", env="HOST")
    port: int = Field(default=8000, env="PORT")
    k_service: Optional[str] = Field(default=None, env="K_SERVICE")  # Google Cloud Run Service
    k_revision: Optional[str] = Field(default=None, env="K_REVISION")

    # Gemini 3.x Foundation Models & Rate-Limit Quota Pool
    gemini_api_key: Optional[str] = Field(default=None, env="GEMINI_API_KEY")
    gemini_api_keys: List[str] = Field(default_factory=list, env="GEMINI_API_KEYS")
    
    # Primary & Cascade Model Tiers
    gemini_model_primary: str = Field(default="gemini-3.7-flash", env="GEMINI_MODEL_PRIMARY")
    gemini_model_cascade: List[str] = Field(
        default_factory=lambda: [
            "gemini-3.7-flash",
            "gemini-3.6-flash",
            "gemini-3.5-flash",
            "gemini-3.5-flash-lite",
            "gemini-3.1-flash-lite",
        ],
        env="GEMINI_MODEL_CASCADE",
    )
    gemini_subagent_model: str = Field(default="gemini-3.5-flash-lite", env="GEMINI_SUBAGENT_MODEL")

    # Telemetry Caching (TTL in seconds)
    cache_ttl_seconds: int = Field(default=900, env="CACHE_TTL_SECONDS")  # 15 minutes

    # Model Context Protocol (MCP) Configuration
    mcp_enabled: bool = Field(default=True, env="MCP_ENABLED")
    mcp_transport: str = Field(default="stdio,sse", env="MCP_TRANSPORT")

    # Persistence / Database (SQLite for local / free-tier; Cloud SQL / PostgreSQL for production)
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

    # Human-in-the-Loop (HITL) Enforcement
    enforce_human_in_the_loop: bool = Field(default=True, env="ENFORCE_HUMAN_IN_THE_LOOP")

    # External Integrations
    github_token: Optional[str] = Field(default=None, env="GITHUB_TOKEN")
    jira_api_token: Optional[str] = Field(default=None, env="JIRA_API_TOKEN")
    jira_instance_url: Optional[str] = Field(default=None, env="JIRA_INSTANCE_URL")
    slack_bot_token: Optional[str] = Field(default=None, env="SLACK_BOT_TOKEN")

    def get_all_api_keys(self) -> List[str]:
        """Returns consolidated list of all provided Gemini API keys."""
        keys = list(self.gemini_api_keys)
        if self.gemini_api_key and self.gemini_api_key not in keys:
            keys.insert(0, self.gemini_api_key)
        return keys


settings = Settings()
