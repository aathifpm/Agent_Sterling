from src.features.research_agent import ResearchAgent
from src.features.sentiment_analyzer import SentimentAnalyzer

class IntentRouter:
    def __init__(self, gemini_handler):
        self.llm = gemini_handler
        self.HANDLERS = {
            'research': self.handle_research,
            'sentiment': self.handle_sentiment,
            'image_analysis': self.handle_image_analysis
        }

    async def route(self, intent, tweet):
        handler = self.HANDLERS.get(intent)
        if handler:
            return await handler(tweet)
        return await self.handle_default(tweet)

    async def handle_research(self, tweet):
        agent = ResearchAgent(self.llm)
        return await agent.research_topic(tweet)
        
    async def handle_sentiment(self, tweet):
        analyzer = SentimentAnalyzer(self.llm)
        return await analyzer.analyze_sentiment(tweet)
        
    async def handle_image_analysis(self, tweet, image):
        """Handle image-specific analysis"""
        analysis = await self.llm.analyze_content(tweet, image)
        return {
            "status": "success",
            "analysis": analysis,
            "type": "image_analysis"
        }
        
    async def handle_default(self, tweet):
        return {"error": "Invalid intent specified"}