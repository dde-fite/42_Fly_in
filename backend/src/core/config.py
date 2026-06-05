from pydantic_settings import BaseSettings


class Config(BaseSettings):
    FRONTEND_URL: str = "http://localhost:3000"
    LOG_LEVEL: str = "DEBUG"
    EXTENDED_LOGGING: bool = False
    STRICT_PARSER: bool = True


config = Config()
