import os
from dataclasses import dataclass, field
from typing import List, Optional

@dataclass
class Settings:
    SECRET_KEY: str = os.getenv("SECRET_KEY", "dev")
    SQLALCHEMY_DATABASE_URI: str = os.getenv("DATABASE_URL", "sqlite:///instance/app.db")
    SQLALCHEMY_TRACK_MODIFICATIONS: bool = False
    CACHE_TYPE: str = os.getenv("CACHE_TYPE", "SimpleCache")
    CACHE_REDIS_URL: Optional[str] = os.getenv("CACHE_REDIS_URL")

    # mutable default handled with default_factory
    PROVIDERS: List[str] = field(
        default_factory=lambda: os.getenv("PROVIDERS", "sleeper").split(",")
    )
