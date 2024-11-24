from typing import Dict
from .base import SocialPlatform
from twitter_agent import TwitterAIAgent
from .mastodon import MastodonPlatform
from .pleroma import PleromaPlatform

class PlatformFactory:
    @staticmethod
    def create_platform(platform_type: str, credentials: Dict) -> SocialPlatform:
        """Create a platform instance based on type"""
        platforms = {
            'twitter': TwitterAIAgent,
            'mastodon': MastodonPlatform,
            'pleroma': PleromaPlatform
        }
        
        if platform_type not in platforms:
            raise ValueError(f"Unsupported platform: {platform_type}")
            
        return platforms[platform_type](credentials) 