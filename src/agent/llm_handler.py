class GeminiHandler:
    def __init__(self, config):
        self.gemini = config.model
        
    async def analyze_content(self, content, image=None):
        """Analyze text or image content using Gemini"""
        if image:
            return await self._analyze_with_image(content, image)
        return await self._analyze_text(content)
    
    async def _analyze_text(self, text):
        prompt = f"""
        Analyze this tweet content and provide insights:
        {text}
        
        Provide:
        1. Main topic
        2. Key points
        3. Suggested response
        """
        response = await self.gemini.generate_content(prompt)
        return response.text 