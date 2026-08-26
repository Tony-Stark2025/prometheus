"""
Configuration module for Prometheus Enterprise Observability Platform.
Standardized on Gemini 3.7 Flash via Vertex AI & Gemini Enterprise Agent Platform (Agent Engine).
"""

from typing import List, Optional, Union, Any
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Core Application Settings
    app_name: str = "Prometheus Chief of Staff"
    environment: str = "development"
    log_level: str = "INFO"
    host: str = "0.0.0.0"
    port: int = 8000

    # Google Cloud & Vertex AI / Gemini Enterprise Agent Platform (Agent Engine)
    use_vertex_ai: bool = True
    gcp_project_id: Optional[str] = None
    gcp_location: str = "us-central1"
    agent_engine_app_id: Optional[str] = None
    agent_engine_location: str = "us-central1"
    gemini_request_timeout_seconds: float = 8.0

    # Unified Foundation Model (Standardized exclusively on Gemini 3.7 Flash)
    gemini_model: str = "gemini-3.7-flash"
    gemini_model_primary: str = "gemini-3.7-flash"

    # Telemetry Caching (TTL in seconds)
    cache_ttl_seconds: int = 900  # 15 minutes

    # Model Context Protocol (MCP) Configuration
    mcp_enabled: bool = True
    mcp_transport: str = "stdio,sse"

    # Persistence / Database (SQLite for local / free-tier; Cloud SQL / PostgreSQL for production)
    database_url: str = "sqlite+aiosqlite:///./prometheus_state.db"

    # Observability & Thresholds
    stale_pr_hours_threshold: int = 48
    ci_failure_threshold_count: int = 2
    default_org_scope: Union[List[str], str] = Field(
        default_factory=lambda: ["engineering", "platform"]
    )

    # Human-in-the-Loop (HITL) Enforcement
    enforce_human_in_the_loop: bool = True

    # External Integrations
    github_token: Optional[str] = None
    jira_api_token: Optional[str] = None
    jira_instance_url: Optional[str] = None
    slack_bot_token: Optional[str] = None

    @field_validator("default_org_scope", mode="after")
    @classmethod
    def normalize_list(cls, v: Any) -> List[str]:
        if isinstance(v, str):
            if not v.strip():
                return []
            if v.startswith("[") and v.endswith("]"):
                import json
                try:
                    return json.loads(v)
                except Exception:
                    pass
            return [item.strip() for item in v.split(",") if item.strip()]
        elif isinstance(v, list):
            return [str(item).strip() for item in v if str(item).strip()]
        return []

    @field_validator("github_token", "jira_api_token", "jira_instance_url", "slack_bot_token", mode="before")
    @classmethod
    def empty_str_to_none(cls, v: Any) -> Optional[str]:
        if isinstance(v, str) and not v.strip():
            return None
        return v

    def get_sqlite_db_path(self) -> str:
        """Extracts the filesystem path from the database URL for SQLite."""
        url = self.database_url
        for prefix in ["sqlite+aiosqlite:///", "sqlite:///", "sqlite+asyncpg:///"]:
            if url.startswith(prefix):
                return url[len(prefix):]
        return url


settings = Settings()
