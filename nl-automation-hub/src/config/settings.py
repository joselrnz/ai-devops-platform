"""
Configuration settings for Natural Language Automation Hub.

Uses pydantic-settings for environment variable management.
"""

from typing import Optional, Literal
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # ========================================================================
    # Application Settings
    # ========================================================================
    APP_NAME: str = "NL Automation Hub"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"

    # ========================================================================
    # Server Settings
    # ========================================================================
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    WORKERS: int = 4

    # ========================================================================
    # LLM Configuration (Routes through Project 2)
    # ========================================================================
    LLM_GATEWAY_URL: str = "http://llm-security-gateway.llm-gateway:8000"
    LLM_PROVIDER: Literal["anthropic", "openai"] = "anthropic"

    # Anthropic
    ANTHROPIC_API_KEY: str = ""
    ANTHROPIC_MODEL: str = "claude-3-sonnet-20240229"

    # OpenAI
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4-turbo-preview"

    # ========================================================================
    # LangSmith Configuration
    # ========================================================================
    LANGCHAIN_TRACING_V2: bool = True
    LANGCHAIN_ENDPOINT: str = "https://api.smith.langchain.com"
    LANGCHAIN_API_KEY: str = ""
    LANGCHAIN_PROJECT: str = "nl-automation-hub"

    # ========================================================================
    # Project 1: MCP AWS Server
    # ========================================================================
    MCP_AWS_SERVER_URL: str = "http://mcp-aws-server.mcp-aws:8080"

    # ========================================================================
    # Project 3: K8s AgentOps Platform
    # ========================================================================
    K8S_AGENTOPS_URL: str = "http://agentops-api.agentops-system:8000"

    # ========================================================================
    # Project 4: Enterprise CI/CD Framework
    # ========================================================================
    CICD_API_URL: str = "http://cicd-api.cicd:8000"

    # ========================================================================
    # Project 5: Centralized Logging & Threat Analytics
    # ========================================================================
    OPENSEARCH_URL: str = "http://opensearch.logging:9200"
    OPENSEARCH_USER: str = "admin"
    OPENSEARCH_PASSWORD: str = ""

    # ========================================================================
    # Project 6: Multi-Cloud Observability Fabric
    # ========================================================================
    PROMETHEUS_URL: str = "http://prometheus.observability:9090"
    TEMPO_URL: str = "http://tempo.observability:3200"
    LOKI_URL: str = "http://loki.observability:3100"

    # ========================================================================
    # Database Configuration
    # ========================================================================
    POSTGRES_HOST: str = "nl-hub-postgres"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = "nl_automation_hub"
    POSTGRES_USER: str = "nl_hub_user"
    POSTGRES_PASSWORD: str = ""

    @property
    def DATABASE_URL(self) -> str:
        return f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

    # ========================================================================
    # Redis Configuration
    # ========================================================================
    REDIS_HOST: str = "nl-hub-redis"
    REDIS_PORT: int = 6379
    REDIS_PASSWORD: Optional[str] = None
    REDIS_DB: int = 0

    @property
    def REDIS_URL(self) -> str:
        if self.REDIS_PASSWORD:
            return f"redis://:{self.REDIS_PASSWORD}@{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"

    # ========================================================================
    # Voice Configuration (Whisper)
    # ========================================================================
    ENABLE_VOICE: bool = True
    WHISPER_MODEL_SIZE: str = "base"  # tiny, base, small, medium, large
    WHISPER_SERVICE_URL: Optional[str] = None  # If using external API

    # ========================================================================
    # Security Settings
    # ========================================================================
    JWT_SECRET_KEY: str = "your-secret-key-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_HOURS: int = 24

    # CORS
    CORS_ORIGINS: list = ["*"]
    CORS_ALLOW_CREDENTIALS: bool = True

    # ========================================================================
    # Rate Limiting
    # ========================================================================
    RATE_LIMIT_REQUESTS_PER_MINUTE: int = 60
    RATE_LIMIT_TOKENS_PER_MINUTE: int = 100000

    # ========================================================================
    # Feature Flags
    # ========================================================================
    ENABLE_WEBSOCKETS: bool = True
    ENABLE_STREAMING: bool = True
    ENABLE_AUDIT_LOG: bool = True


# Global settings instance
settings = Settings()
