from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # LLM
    llm_provider: str = "openai"  # "openai" or "anthropic"
    anthropic_api_key: str = "sk-xxx"
    anthropic_model: str = "deepseek-chat"
    anthropic_base_url: str = "https://api.deepseek.com/v1"

    # Database — SQLite for local dev, PostgreSQL+pgvector for production
    database_url: str = "sqlite+aiosqlite:///./data.db"
    database_url_sync: str = "sqlite:///./data.db"
    vector_store: str = "simple"  # "simple" (SQLite) or "pgvector" (PostgreSQL)

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # MinIO
    minio_endpoint: str = "localhost:9000"
    minio_access_key: str = "minioadmin"
    minio_secret_key: str = "minioadmin"
    minio_bucket: str = "children-growth"

    # App
    app_env: str = "development"
    app_debug: bool = True
    log_level: str = "DEBUG"

    # LangGraph
    langgraph_checkpoint_db: str = "postgresql://postgres:postgres@localhost:5432/children_growth"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8", "env_prefix": "CGOS_"}


settings = Settings()
