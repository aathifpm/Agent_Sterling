class ResearchAgent:
    def __init__(self, gemini_handler):
        self.llm = gemini_handler
    
    async def research_topic(self, tweet_text):
        prompt = f"""
        Provide comprehensive research on this tweet topic:
        {tweet_text}
        
        Include:
        1. Key facts and background
        2. Related statistics or data
        3. Current trends
        4. Expert opinions
        5. Format as concise bullet points
        """
        
        response = await self.llm.analyze_content(prompt)
        return self._format_research(response)
    
    def _format_research(self, raw_response):
        # Format the research response for Twitter
        try:
            return {
                "status": "success",
                "research": raw_response,
                "summary": self._create_summary(raw_response)
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}