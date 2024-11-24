import requests
from .base import SocialPlatform, PostData
from typing import List, Dict

class PleromaPlatform(SocialPlatform):
    def __init__(self, credentials: Dict):
        self.base_url = credentials.get('instance_url')
        self.headers = {
            'Authorization': f"Bearer {credentials.get('access_token')}",
            'Content-Type': 'application/json'
        }
    
    async def post_content(self, content: str) -> Dict:
        try:
            response = requests.post(
                f"{self.base_url}/api/v1/statuses",
                headers=self.headers,
                json={"status": content}
            )
            response.raise_for_status()
            return self._format_post(response.json())
        except Exception as e:
            return {"error": str(e)}
    
    async def get_mentions(self) -> List[Dict]:
        try:
            response = requests.get(
                f"{self.base_url}/api/v1/notifications?type=mention",
                headers=self.headers
            )
            response.raise_for_status()
            return [self._format_post(notif['status']) for notif in response.json()]
        except Exception as e:
            return [{"error": str(e)}]
    
    async def reply_to_post(self, post_id: str, content: str) -> Dict:
        try:
            response = requests.post(
                f"{self.base_url}/api/v1/statuses",
                headers=self.headers,
                json={
                    "status": content,
                    "in_reply_to_id": post_id
                }
            )
            response.raise_for_status()
            return self._format_post(response.json())
        except Exception as e:
            return {"error": str(e)}
    
    async def get_user_posts(self, username: str, limit: int = 10) -> List[Dict]:
        try:
            response = requests.get(
                f"{self.base_url}/api/v1/accounts/{username}/statuses?limit={limit}",
                headers=self.headers
            )
            response.raise_for_status()
            return [self._format_post(status) for status in response.json()]
        except Exception as e:
            return [{"error": str(e)}]
    
    def _format_post(self, status: Dict) -> Dict:
        return {
            "id": status['id'],
            "content": status['content'],
            "author": status['account']['username'],
            "created_at": status['created_at'],
            "platform": "pleroma",
            "reply_to": status.get('in_reply_to_id'),
            "metrics": {
                "replies": status.get('replies_count', 0),
                "reblogs": status.get('reblogs_count', 0),
                "favorites": status.get('favourites_count', 0)
            }
        } 