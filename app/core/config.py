from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "AI对话小助手后端"
    debug: bool = True
    database_url: str = "sqlite+aiosqlite:///./data/database.db"
    weather_api_key: str = ""
    ai_api_key: str = ""
    news_api_key: str = ""

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
