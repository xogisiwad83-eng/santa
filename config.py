from dataclasses import dataclass
from dotenv import load_dotenv
from typing import Optional

import os

load_dotenv()

@dataclass
class Config:
    BOT_TOKEN: str
    DATABASE_PATH: Optional[str] = "secret_santa.db"


def load_config() -> Config:
    token = os.getenv("BOT_TOKEN")
    path = os.getenv('DATABASE_PATH')
    if token and path:
        return Config(
            BOT_TOKEN=token,
            DATABASE_PATH=path
        )
    elif token:
        return Config(BOT_TOKEN=token)
    raise ValueError("Токен не подгрузился")


config = load_config()
