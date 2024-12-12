from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, List, Optional, Set
from datetime import datetime
import asyncio
import os
from src.platforms.mastodon import MastodonPlatform
from src.agent.processor import PostProcessor
from pydantic import BaseModel, validator
import time

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
    postStyleEmojis: bool = True
    useHashtags: bool = True
    maxLength: int = 240

class MastodonCredentials(BaseModel):
    instance_url: str
    client_id: str
    client_secret: str
    access_token: str
    gemini_api_key: str

class DMConfig(BaseModel):
    enabled: bool = False
    auto_reply: bool = True
    reply_interval: int = 300  # 5 minutes

class LikeConfig(BaseModel):
    enabled: bool = False
    max_likes_per_hour: int = 20
    like_probability: float = 0.7

class AutoPostConfig(BaseModel):
    enabled: bool = True
    interval: int = 1800  # 30 minutes in seconds
    max_daily_posts: int = 48  # 2 posts per hour for 24 hours
    
class PlatformConfig(BaseModel):
    platform: str
    credentials: MastodonCredentials
    monitoring: Monitoring
    response: Response
    rateLimits: RateLimits
    filters: Filters
    postStyle: PostStyleConfig
    dm_settings: Optional[DMConfig] = DMConfig()
    like_settings: Optional[LikeConfig] = LikeConfig()
    auto_post_settings: Optional[AutoPostConfig] = AutoPostConfig()

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

# Global processor instance
processor = PostProcessor()
background_task = None

# Track processed items
processed_posts: Set[str] = set()
processed_mentions: Set[str] = set()
last_trending_post_time = 0

async def process_mention(platform, mention):
    """Process a single mention with context-aware handling"""
    mention_id = mention['id']
    if mention_id not in processed_mentions:
        try:
            # Get conversation context
            context = mention.get('context', {})
            conversation = context.get('conversation', [])
            
            # Process the mention with context
            response = await platform.handle_mention(mention)
            
            if response and response.get('status') == 'success':
                processed_mentions.add(mention_id)
                print(f"Successfully processed mention {mention_id}")
                if response.get('context_used'):
                    print(f"Used conversation context: {len(conversation)} previous messages")
                return True
                
        except Exception as e:
            print(f"Error processing mention {mention_id}: {str(e)}")
    return False

async def check_mentions(platform):
    """Check and process new mentions"""
    try:
        mentions = await platform.get_mentions(limit=5)
        
        for mention in mentions:
            try:
                if mention['id'] not in processed_mentions:
                    await process_mention(platform, mention)
                    # Add small delay between processing mentions
                    await asyncio.sleep(2)
            except Exception as e:
                print(f"Error processing mention: {str(e)}")
                continue
                
    except Exception as e:
        print(f"Error checking mentions: {str(e)}")
        return False
    
    return True

async def create_trending_post(platform):
    """Create a trending post with enhanced context awareness and improved content generation"""
    global last_trending_post_time
    current_time = datetime.now().timestamp()
    
    # Check if enough time has passed since last post
    if current_time - last_trending_post_time < platform.auto_post_settings['interval']:
        return False
        
    try:
        # Get trending topics with enhanced context
        topics = await platform.get_trending_topics_with_context()
        if not topics:
            print("No trending topics found at the moment")
            return False

        # Sort topics by engagement and trend
        topics.sort(key=lambda x: (
            x['context']['engagement_level'] * (2 if x['context']['engagement_trend'] == 'rising' else 1),
            x['context']['post_frequency']
        ), reverse=True)
        
        for topic in topics:
            try:
                # Skip topics with predominantly negative sentiment
                if topic['context']['sentiment'] == 'negative':
                    continue
                    
                # Generate content with enhanced context
                content = await platform.create_trending_content(
                    topic['tag'],
                    topic['context']
                )
                
                if content:
                    # Post during active hours if possible
                    active_hours = topic['context'].get('active_hours', [])
                    current_hour = datetime.now().hour
                    
                    if not active_hours or current_hour in active_hours:
                        post = platform.client.status_post(
                            content,
                            visibility="public"
                        )
                        
                        if post:
                            post_id = post['id']
                            if post_id not in processed_posts:
                                processed_posts.add(post_id)
                                last_trending_post_time = current_time
                                print(f"Successfully created enhanced trending post about {topic['tag']}")
                                
                                # Track engagement for future reference
                                platform.processed_trending_topics[topic['tag']] = {
                                    'last_used': current_time,
                                    'engagement_level': topic['context']['engagement_level'],
                                    'sentiment': topic['context']['sentiment']
                                }
                                
                                return True
                    else:
                        print(f"Skipping post for {topic['tag']} - outside active hours")
                        continue
                        
            except Exception as e:
                print(f"Error creating post for topic {topic['tag']}: {str(e)}")
                continue
        
        print("No suitable topics found for posting at this time")
        return False
        
    except Exception as e:
        print(f"Error in trending post creation: {str(e)}")
        return False

async def monitor_platform(platform):
    """Main monitoring function for the platform"""
    while True:
        try:
            # Check for new mentions
            mentions = await platform.get_mentions(limit=1)
            if mentions and len(mentions) > 0:
                mention = mentions[0]
                if "error" not in mention:
                    await process_mention(platform, mention['mention'])
            
            # Handle trending posts if enabled
            if platform.auto_post_settings['enabled']:
                await create_trending_post(platform)
            
            # Cleanup old processed items (keep last 1000)
            if len(processed_posts) > 1000:
                processed_posts.clear()
                processed_posts.update(list(processed_posts)[-1000:])
            if len(processed_mentions) > 1000:
                processed_mentions.clear()
                processed_mentions.update(list(processed_mentions)[-1000:])
            
            # Short sleep to prevent rate limiting
            await asyncio.sleep(10)
            
        except Exception as e:
            print(f"Error in platform monitoring: {str(e)}")
            await asyncio.sleep(30)

@app.post("/api/start")
async def start_agent(config: PlatformConfig):
    global background_task, processor
    try:
        print("Starting agent with config:", config.dict())
        
        if config.platform == "mastodon":
            # Validate credentials
            if not all([
                config.credentials.instance_url,
                config.credentials.client_id,
                config.credentials.client_secret,
                config.credentials.access_token,
                config.credentials.gemini_api_key
            ]):
                raise HTTPException(status_code=400, detail="Missing required credentials")
            
            credentials = {
                'instance_url': config.credentials.instance_url,
                'client_id': config.credentials.client_id,
                'client_secret': config.credentials.client_secret,
                'access_token': config.credentials.access_token,
                'gemini_api_key': config.credentials.gemini_api_key
            }
            
            try:
                # Initialize platform with credentials
                platform = MastodonPlatform(credentials)
                
                # Set up platform configuration
                platform.processor = processor
                platform.dm_settings = config.dm_settings.dict()
                platform.like_settings = config.like_settings.dict()
                platform.auto_post_settings = config.auto_post_settings.dict()
                platform.hashtags = config.monitoring.hashtags
                platform.check_interval = config.monitoring.checkInterval
                platform.cooldown_period = config.rateLimits.cooldownPeriod
                
                # Set processor platform
                processor.platform = platform
                processor.config = config
                
                print("Mastodon platform initialized")
                
                # Cancel existing task if running
                if background_task and not background_task.done():
                    background_task.cancel()
                    try:
                        await background_task
                    except asyncio.CancelledError:
                        pass
                
                # Clear processed items on restart
                processed_posts.clear()
                processed_mentions.clear()
                
                # Start the platform monitoring task
                background_task = asyncio.create_task(monitor_platform(platform))
                print("Platform monitoring started")
                
                return {
                    "status": "success",
                    "message": "Agent started successfully",
                    "logs": processor.logs
                }
                
            except Exception as e:
                error_msg = f"Failed to initialize Mastodon: {str(e)}"
                print(error_msg)
                raise HTTPException(status_code=400, detail=error_msg)
                
        else:
            raise HTTPException(status_code=400, detail="Unsupported platform")
            
    except HTTPException as he:
        raise he
    except Exception as e:
        error_msg = f"Error starting agent: {str(e)}"
        print(error_msg)
        raise HTTPException(status_code=500, detail=error_msg)

@app.post("/api/stop")
async def stop_agent():
    global background_task
    try:
        # Stop the processor
        if processor:
            processor.stop()
        
        # Cancel the background task
        if background_task and not background_task.done():
            background_task.cancel()
            try:
                await background_task
            except asyncio.CancelledError:
                pass
            background_task = None
        
        return {
            "status": "success", 
            "message": "Agent stopped successfully",
            "logs": processor.logs if processor else []
        }
    except Exception as e:
        error_msg = f"Error stopping agent: {str(e)}"
        print(error_msg)
        raise HTTPException(status_code=500, detail=error_msg)

@app.get("/api/status")
async def get_status():
    try:
        if not processor:
            return {
                "status": "not_initialized",
                "message": "Agent not initialized"
            }
        status = processor.get_status()
        return status
    except Exception as e:
        error_msg = f"Error in status check: {str(e)}"
        print(error_msg)
        raise HTTPException(status_code=500, detail=error_msg)

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
        if not processor or not processor.platform:
            raise HTTPException(
                status_code=400, 
                detail="Agent not initialized. Please start the agent first."
            )
            
        processor.platform.dm_settings = dm_config.dict()
        return {
            "status": "success",
            "message": "DM settings updated",
            "settings": dm_config.dict()
        }
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/update-like-settings")
async def update_like_settings(like_config: LikeConfig):
    try:
        if not processor or not processor.platform:
            raise HTTPException(
                status_code=400, 
                detail="Agent not initialized. Please start the agent first."
            )
            
        processor.platform.like_settings = like_config.dict()
        return {
            "status": "success",
            "message": "Like settings updated",
            "settings": like_config.dict()
        }
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/update-auto-post-settings")
async def update_auto_post_settings(auto_post_config: AutoPostConfig):
    try:
        if not processor or not processor.platform:
            raise HTTPException(
                status_code=400, 
                detail="Agent not initialized. Please start the agent first."
            )
        
        # Validate and update settings
        try:
            # Convert to dict and update platform settings
            settings_dict = auto_post_config.dict()
            processor.platform.update_settings('auto_post', settings_dict)
            
            # Update processor config if it exists
            if processor.config and processor.config.auto_post_settings:
                processor.config.auto_post_settings = auto_post_config
            
            return {
                "status": "success",
                "message": "Auto-posting settings updated",
                "settings": settings_dict
            }
        except ValueError as ve:
            raise HTTPException(status_code=400, detail=str(ve))
            
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)