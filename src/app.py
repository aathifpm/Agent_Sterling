from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from src.features.research_agent import ResearchAgent
from src.features.sentiment_analyzer import SentimentAnalyzer
from src.features.thread_generator import ThreadGenerator
from src.agent.base import TwitterAIAgent
from src.config.gemini_config import GeminiConfig
from src.platforms.factory import PlatformFactory
from typing import Dict
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Verify required environment variables
required_vars = [
    'GEMINI_API_KEY',
    'TWITTER_API_KEY',
    'TWITTER_API_SECRET',
    'TWITTER_ACCESS_TOKEN',
    'TWITTER_ACCESS_TOKEN_SECRET',
    'TWITTER_BEARER_TOKEN'
]

missing_vars = [var for var in required_vars if not os.getenv(var)]
if missing_vars:
    raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")

app = FastAPI()

# Initialize configurations
gemini_config = GeminiConfig(os.getenv("GEMINI_API_KEY"))
credentials = {
    'bearer_token': os.getenv('TWITTER_BEARER_TOKEN'),
    'api_key': os.getenv('TWITTER_API_KEY'),
    'api_secret': os.getenv('TWITTER_API_SECRET'),
    'access_token': os.getenv('TWITTER_ACCESS_TOKEN'),
    'access_secret': os.getenv('TWITTER_ACCESS_TOKEN_SECRET')
}

# Initialize agent
agent = TwitterAIAgent(credentials)

class TweetRequest(BaseModel):
    text: str
    type: str

class PlatformConfig(BaseModel):
    platform_type: str
    credentials: Dict

@app.post("/analyze")
async def analyze_tweet(request: TweetRequest):
    try:
        if request.type == "research":
            research_agent = ResearchAgent(gemini_config)
            return research_agent.research_topic(request.text)
        elif request.type == "sentiment":
            sentiment_analyzer = SentimentAnalyzer(gemini_config)
            return sentiment_analyzer.analyze_sentiment(request.text)
        elif request.type == "thread":
            thread_generator = ThreadGenerator(gemini_config)
            return thread_generator.generate_thread(request.text)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
def health_check():
    return {"status": "healthy"}

@app.post("/platform/initialize")
async def initialize_platform(config: PlatformConfig):
    try:
        platform = PlatformFactory.create_platform(
            config.platform_type,
            config.credentials
        )
        return {"status": "success", "platform": config.platform_type}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))