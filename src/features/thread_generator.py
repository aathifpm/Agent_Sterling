class ThreadGenerator:
    async def generate_thread(self, topic):
        prompt = f"""
        Create a viral Twitter thread about:
        {topic}
        
        Requirements:
        1. 5 tweets maximum
        2. Each tweet under 280 characters
        3. Engaging and informative
        4. Include hooks and transitions
        """
        return await self.llm.analyze_content(prompt) 