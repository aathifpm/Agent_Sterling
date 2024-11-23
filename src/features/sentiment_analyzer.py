class SentimentAnalyzer:
    def __init__(self, gemini_handler):
        self.llm = gemini_handler
    
    async def analyze_sentiment(self, tweet_text):
        prompt = f"""
        Analyze the sentiment of this tweet:
        {tweet_text}
        
        Provide:
        1. Overall sentiment (positive/negative/neutral)
        2. Confidence level
        3. Key emotional indicators
        Format as JSON.
        """
        
        response = await self.llm.analyze_content(prompt)
        return self._parse_sentiment(response) 