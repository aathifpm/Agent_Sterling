from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, List, Optional
from datetime import datetime
import asyncio
import os
from dotenv import load_dotenv
from src.platforms.mastodon import MastodonPlatform
from src.agent.processor import PostProcessor
from pydantic import BaseModel, validator

load_dotenv()

app = FastAPI()

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Models
class Monitoring(BaseModel):
    accountToWatch: str
    hashtags: List[str]
    checkInterval: int

class Response(BaseModel):
    type: str
    useEmojis: bool
    maxLength: int

class RateLimits(BaseModel):
    maxPostsPerHour: int
    cooldownPeriod: int

class Filters(BaseModel):
    keywords: List[str]
    blacklist: List[str]

class PostStyleConfig(BaseModel):
    style: str = "entertainer"
    useEmojis: bool = True
    useHashtags: bool = True
    maxLength: int = 240

class MastodonCredentials(BaseModel):
    instance_url: str
    client_id: str
    client_secret: str
    access_token: str
    gemini_api_key: str

class PlatformConfig(BaseModel):
    platform: str
    credentials: MastodonCredentials
    monitoring: Monitoring
    response: Response
    rateLimits: RateLimits
    filters: Filters
    postStyle: PostStyleConfig

    class Config:
        validate_assignment = True
        
    @validator('credentials')
    def validate_credentials(cls, v):
        if not v.instance_url.startswith(('http://', 'https://')):
            raise ValueError('Instance URL must start with http:// or https://')
        if not all([v.client_id, v.client_secret, v.access_token, v.gemini_api_key]):
            raise ValueError('All credentials are required')
        return v
        
    @validator('rateLimits')
    def validate_rate_limits(cls, v):
        if v.maxPostsPerHour < 1 or v.maxPostsPerHour > 50:
            raise ValueError('Max posts per hour must be between 1 and 50')
        if v.cooldownPeriod < 30 or v.cooldownPeriod > 3600:
            raise ValueError('Cooldown period must be between 30 and 3600 seconds')
        return v

class DMConfig(BaseModel):
    enabled: bool = False
    auto_reply: bool = True
    reply_interval: int = 300  # 5 minutes

class LikeConfig(BaseModel):
    enabled: bool = False
    max_likes_per_hour: int = 20
    like_probability: float = 0.7

# Global processor instance
processor = PostProcessor()
background_task = None

@app.post("/api/start")
async def start_agent(config: PlatformConfig):
    global background_task
    try:
        print("Starting agent with config:", config.dict())
        
        if config.platform == "mastodon":
            credentials = {
                'instance_url': config.credentials.instance_url,
                'client_id': config.credentials.client_id,
                'client_secret': config.credentials.client_secret,
                'access_token': config.credentials.access_token,
                'gemini_api_key': config.credentials.gemini_api_key
            }
            processor.platform = MastodonPlatform(credentials)
            print("Mastodon platform initialized")

        # Set config and start processing
        processor.config = config
        
        # Cancel existing task if running
        if background_task:
            background_task.cancel()
            try:
                await background_task
            except asyncio.CancelledError:
                pass
        
        # Start new background task
        background_task = asyncio.create_task(processor.start_processing())
        print("Background task created")
        
        return {
            "status": "success",
            "message": "Agent started successfully",
            "logs": processor.logs
        }
    except Exception as e:
        print(f"Error starting agent: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/stop")
async def stop_agent():
    global background_task
    try:
        # Stop the processor
        processor.stop()
        
        # Cancel the background task
        if background_task:
            background_task.cancel()
            try:
                await background_task
            except asyncio.CancelledError:
                pass
            background_task = None
        
        return {
            "status": "success", 
            "message": "Agent stopped successfully",
            "logs": processor.logs
        }
    except Exception as e:
        print(f"Error stopping agent: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/status")
async def get_status():
    try:
        return {
            "status": "running" if processor.is_running else "stopped",
            "posts_processed": processor.posts_processed,
            "responses_sent": processor.responses_sent,
            "logs": processor.logs[-10:]  # Return last 10 logs
        }
    except Exception as e:
        print(f"Error in status check: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/update-style")
async def update_post_style(style_config: PostStyleConfig):
    try:
        if processor.platform:
            success = await processor.platform.set_post_style(style_config.style)
            if success:
                return {
                    "status": "success",
                    "message": f"Post style updated to {style_config.style}",
                    "current_style": style_config.style
                }
            else:
                raise HTTPException(status_code=400, detail="Invalid style option")
        else:
            raise HTTPException(status_code=400, detail="Platform not initialized")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/update-dm-settings")
async def update_dm_settings(dm_config: DMConfig):
    try:
        if processor.platform:
            processor.platform.dm_settings = {
                "enabled": dm_config.enabled,
                "auto_reply": dm_config.auto_reply,
                "reply_interval": dm_config.reply_interval
            }
            return {
                "status": "success",
                "message": "DM settings updated",
                "settings": dm_config.dict()
            }
        else:
            raise HTTPException(status_code=400, detail="Platform not initialized")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/update-like-settings")
async def update_like_settings(like_config: LikeConfig):
    try:
        if processor.platform:
            processor.platform.like_settings = like_config.dict()
            return {
                "status": "success",
                "message": "Like settings updated",
                "settings": like_config.dict()
            }
        else:
            raise HTTPException(status_code=400, detail="Platform not initialized")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)