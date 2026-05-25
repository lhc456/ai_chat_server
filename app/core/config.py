from pydantic_settings import BaseSettings
import secrets


class Settings(BaseSettings):
    app_name: str = "AI对话小助手后端"
    debug: bool = True
    database_url: str = "sqlite+aiosqlite:///./data/database.db"
    weather_api_key: str = ""
    ai_api_key: str = ""
    news_api_key: str = ""
    # JWT 配置
    secret_key: str = secrets.token_urlsafe(32)  # 生产环境应该从环境变量读取
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
