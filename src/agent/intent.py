class IntentClassifier:
    def __init__(self, gemini_handler):
        self.llm = gemini_handler
    
    async def classify_intent(self, tweet_text):
        prompt = f"""
        Classify the intent of this tweet:
        {tweet_text}
        
        Categories:
        - research (seeking information)
        - sentiment (expressing emotion)
        - entertainment (casual/fun)
        - support (asking for help)
        
        Return only the category name.
        """
        
        response = await self.llm.analyze_content(prompt)
        return response.strip().lower() 