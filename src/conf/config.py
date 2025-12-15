from pydantic_settings import BaseSettings
from pydantic import ConfigDict, EmailStr


class Settings(BaseSettings):
    BIND_HOST: str = "0.0.0.0"
    BIND_PORT: int = 80
    ENV: str = "dev"

    # SQL DB
    DB_URL: str = ""

    # redis
    REDIS_URL: str = "redis://localhost"
    CACHE_TTL_SEC: int = 3600

    # jwt
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    EMAIL_TOKEN_EXPIRE_DAYS: int = 7
    EMAIL_PASSWORD_TOKEN_EXPIRE_DAYS: int = 1
    ALGORITHM: str = "HS256"
    SECRET_KEY: str = "secret"

    # limits
    LIMIT_ORIGINS: str = "*"
    LIMIT4_USERS_ME: str = "5/minute"
    LIMIT4_USERS_RESENT: str = "3/day"
    LIMIT4_USERS_PASSWD: str = "1/day"

    # mail by meta.ua
    MAIL_USERNAME: EmailStr = "???@meta.ua"
    MAIL_PASSWORD: str = "password"
    MAIL_FROM: EmailStr = "not.replay@meta.ua"
    MAIL_PORT: int = 465
    MAIL_SERVER: str = "smtp.meta.ua"
    MAIL_FROM_NAME: str = "Rest API Service"
    MAIL_STARTTLS: bool = False
    MAIL_SSL_TLS: bool = True
    USE_CREDENTIALS: bool = True
    VALIDATE_CERTS: bool = True

    # Cloudinary
    CLOUDINARY_NAME: str = ""
    CLOUDINARY_API_KEY: str = ""
    CLOUDINARY_API_SECRET: str = ""

    model_config = ConfigDict(
        env_file=".env", env_file_encoding="utf-8", case_sensitive=True, extra="ignore"
    )


settings = Settings()
