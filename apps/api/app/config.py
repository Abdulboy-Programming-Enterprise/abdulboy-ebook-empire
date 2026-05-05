"""
Application Configuration
=========================
Pydantic settings for environment-based configuration.
"""

from typing import List, Optional
from pydantic_settings import BaseSettings
from pydantic import ConfigDict, Field


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    model_config = ConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )
    
    # Application
    APP_NAME: str = "Abdulboy Ebook Empire API"
    APP_ENV: str = "development"
    APP_DEBUG: bool = True
    APP_SECRET_KEY: str = Field(..., min_length=32)
    API_VERSION: str = "v1"
    
    # Server
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    WORKERS: int = 4
    
    # Database
    DATABASE_URL: str
    DATABASE_POOL_SIZE: int = 20
    DATABASE_MAX_OVERFLOW: int = 40
    
    # Redis
    REDIS_URL: str
    REDIS_PASSWORD: Optional[str] = None
    
    # JWT
    JWT_SECRET_KEY: str = Field(..., min_length=32)
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # Stripe
    STRIPE_SECRET_KEY: Optional[str] = None
    STRIPE_PUBLIC_KEY: Optional[str] = None
    STRIPE_WEBHOOK_SECRET: Optional[str] = None
    
    # OPay
    OPAY_MERCHANT_ID: Optional[str] = None
    OPAY_PUBLIC_KEY: Optional[str] = None
    OPAY_SECRET_KEY: Optional[str] = None
    OPAY_ENV: str = "sandbox"
    
    # AWS S3
    AWS_ACCESS_KEY_ID: Optional[str] = None
    AWS_SECRET_ACCESS_KEY: Optional[str] = None
    AWS_REGION: str = "us-east-1"
    AWS_BUCKET_NAME: Optional[str] = None
    
    # Email
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    EMAIL_FROM: str = "noreply@abdulboy-ebook.com"
    
    # Sentry
    SENTRY_DSN: Optional[str] = None
    
    # OpenAI
    OPENAI_API_KEY: Optional[str] = None
    
    # CORS
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:8000"]
    ALLOWED_HOSTS: List[str] = ["*"]
    
    # Rate Limiting
    RATE_LIMIT_REQUESTS: int = 100
    RATE_LIMIT_PERIOD: int = 60
    
    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"
    
    @property
    def is_production(self) -> bool:
        return self.APP_ENV == "production"
    
    @property
    def is_development(self) -> bool:
        return self.APP_ENV == "development"
    
    @property
    def is_testing(self) -> bool:
        return self.APP_ENV == "testing"


settings = Settings()
