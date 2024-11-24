from abc import ABC, abstractmethod
from typing import List, Dict, Optional

class SocialPlatform(ABC):
    """Base interface for all social media platforms"""
    
    @abstractmethod
    async def post_content(self, content: str) -> Dict:
        """Post content to the platform"""
        pass
    
    @abstractmethod
    async def get_mentions(self) -> List[Dict]:
        """Get mentions/replies"""
        pass
    
    @abstractmethod
    async def reply_to_post(self, post_id: str, content: str) -> Dict:
        """Reply to a specific post"""
        pass
    
    @abstractmethod
    async def get_user_posts(self, username: str, limit: int = 10) -> List[Dict]:
        """Get posts from a specific user"""
        pass

class PostData:
    """Standardized post data across platforms"""
    def __init__(self, 
                 id: str,
                 content: str,
                 author: str,
                 created_at: str,
                 platform: str,
                 reply_to: Optional[str] = None,
                 metrics: Optional[Dict] = None):
        self.id = id
        self.content = content
        self.author = author
        self.created_at = created_at
        self.platform = platform
        self.reply_to = reply_to
        self.metrics = metrics or {}