from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = "sqlite:///./ai_blog.db"
    upload_dir: str = "uploads"

    openai_api_key: str | None = None
    llm_model: str = "gpt-5.6-luna"

    use_mock_ai: bool = True
    seo_provider: str = "mock"
    seo_rewriter_provider: str = "mock"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
