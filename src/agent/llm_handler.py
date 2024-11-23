class GeminiHandler:
    def __init__(self, config=None):
        self.gemini = config.model if config else None
        
    def analyze_content(self, content, image=None):
        """Analyze text or image content using Gemini"""
        if image:
            return self._analyze_with_image(content, image)
        return self._analyze_text(content)
    
    def _analyze_text(self, text):
        prompt = f"""
        Analyze this tweet content and provide insights:
        {text}
        
        Provide:
        1. Main topic
        2. Key points
        3. Suggested response
        """
        response = self.generate_content(prompt)
        return response.text

    def generate_content(self, prompt):
        """Direct generation method for simple prompts"""
        if self.gemini:
            return self.gemini.generate_content(prompt)
        # Fallback response if no model is configured
        return type('Response', (), {'text': 'Model not configured'})()