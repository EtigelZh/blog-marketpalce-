from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Blog Marketplace"
    debug: bool = False

    postgres_db: str = ""
    postgres_user: str = ""
    postgres_password: str = ""
    postgres_host: str = ""
    postgres_port: int = 5432

    jwt_secret: str = "change-me"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60

    rabbitmq_host: str = "rabbitmq"
    rabbitmq_port: int = 5672
    rabbitmq_user: str = "guest"
    rabbitmq_password: str = "guest"
    rabbitmq_email_queue: str = "emails"

    smtp_host: str = ""
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_from: str = ""

    smtp_host: str = "mailpit"
    smtp_port: int = 1025
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_from: str = "noreply@blog-marketplace.local"

    minio_endpoint: str
    minio_public_endpoint: str
    minio_access_key: str
    minio_secret_key: str
    minio_bucket: str = "articles"
    minio_secure: bool = False

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

settings = Settings()