from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from src.features.research_agent import ResearchAgent
from src.features.sentiment_analyzer import SentimentAnalyzer
from src.agent.llm_handler import GeminiHandler
from src.config.gemini_config import GeminiConfig
import os

app = FastAPI()

class TweetRequest(BaseModel):
    text: str
    type: str  # research, sentiment, context, etc.

@app.post("/analyze")
async def analyze_tweet(request: TweetRequest):
    try:
        gemini_config = GeminiConfig(os.getenv("GEMINI_API_KEY"))
        gemini_handler = GeminiHandler(gemini_config)
        
        if request.type == "research":
            agent = ResearchAgent(gemini_handler)
            return await agent.research_topic(request.text)
        elif request.type == "sentiment":
            analyzer = SentimentAnalyzer(gemini_handler)
            return await analyzer.analyze_sentiment(request.text)
        # Add more handlers as needed
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))