from pydantic_settings import BaseSettings
from typing import Optional

class MastodonSettings(BaseSettings):
    MASTODON_CLIENT_ID: str
    MASTODON_CLIENT_SECRET: str
    MASTODON_ACCESS_TOKEN: str
    MASTODON_INSTANCE_URL: str
    MASTODON_BOT_USERNAME: Optional[str] = None
    
    class Config:
        env_file = ".env" 