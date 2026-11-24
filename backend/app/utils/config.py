import os
from enum import StrEnum

from pydantic import Field, SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy import URL


class Environment(StrEnum):
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"


ENVIRONMENT = os.getenv("ENVIRONMENT", Environment.DEVELOPMENT)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=(f".env.{ENVIRONMENT}", ".env"), extra="ignore")

    ENVIRONMENT: Environment = Environment.DEVELOPMENT
    PROJECT_NAME: str = "AI Ops Platform API"
    VERSION: str = "1.0"
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"
    DOCS_ENABLED: bool = True
    CORS_ORIGINS: list[str] = []
    FORWARDED_ALLOW_IPS: list[str] = ["127.0.0.1"]
    FRONTEND_URL: str = "http://localhost:3000"

    SECRET_KEY: SecretStr = Field(min_length=32)
    ACCESS_TOKEN_MINUTES: int = 480
    RESET_TOKEN_MINUTES: int = 15

    DB_USERNAME: str
    DB_PASS: str
    DB_HOST: str = "127.0.0.1"
    DB_PORT: int = 3306
    DB_NAME: str
    DB_POOL_SIZE: int = 5
    DB_MAX_OVERFLOW: int = 10

    REDIS_URL: str | None = None

    SMTP_HOST: str | None = None
    SMTP_PORT: int = 587
    SMTP_USERNAME: str | None = None
    SMTP_PASSWORD: SecretStr | None = None
    SMTP_TLS: bool = True
    SMTP_FROM: str = "AI Ops <no-reply@aiops.uz>"

    @property
    def DATABASE_URL(self) -> URL:
        return URL.create(
            "mysql+aiomysql",
            username=self.DB_USERNAME,
            password=self.DB_PASS,
            host=self.DB_HOST,
            port=self.DB_PORT,
            database=self.DB_NAME,
            query={"charset": "utf8mb4"},
        )

    @model_validator(mode="after")
    def check_production(self):
        if self.ENVIRONMENT is not Environment.PRODUCTION:
            return self
        if self.DEBUG:
            raise ValueError("DEBUG must be false in production")
        if not self.SMTP_HOST:
            raise ValueError("SMTP_HOST is required in production to send password reset emails")
        return self


settings = Settings()
