from pydantic_settings import BaseSettings
from pydantic import Field, validator
from typing import List

class Config(BaseSettings):
    bot_token: str
    admin_chat_ids: List[int] = Field(..., env="ADMIN_CHAT_IDS")
    chat_id: int = Field(..., env="CHAT_ID")  # Используем существующую переменную CHAT_ID
    database_url: str

    class Config:
        env_file = ".env"

    @validator('admin_chat_ids', pre=True)
    def parse_admin_chat_ids(cls, v):
        if isinstance(v, str):
            return [int(x.strip()) for x in v.split(',')]
        return v

def load_config() -> Config:
    return Config()
