from pydantic_settings import BaseSettings


class Config(BaseSettings):
    LOG_LEVEL: str = "DEBUG"


config = Config()
