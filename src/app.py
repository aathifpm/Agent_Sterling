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

class PlatformConfig(BaseModel):
    platform: str
    monitoring: Monitoring
    response: Response
    rateLimits: RateLimits
    filters: Filters

# Global processor instance
processor = PostProcessor()
background_task = None

@app.post("/api/start")
async def start_agent(config: PlatformConfig):
    global background_task
    try:
        print("Starting agent with config:", config.dict())  # Debug print
        
        # Initialize platform
        if config.platform == "mastodon":
            credentials = {
                'instance_url': os.getenv('MASTODON_INSTANCE_URL'),
                'client_id': os.getenv('MASTODON_CLIENT_ID'),
                'client_secret': os.getenv('MASTODON_CLIENT_SECRET'),
                'access_token': os.getenv('MASTODON_ACCESS_TOKEN')
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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)