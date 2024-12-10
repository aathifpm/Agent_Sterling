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

    def _analyze_with_image(self, text, image):
        """Analyze content with image using Gemini's multimodal capabilities"""
        prompt = f"""
        Analyze this post and its image:
        Text: {text}
        
        Provide:
        1. Image description
        2. Relevance to text
        3. Key visual elements
        4. Suggested response incorporating both
        """
        
        try:
            content_parts = [prompt, image]
            response = self.gemini.generate_content(content_parts)
            return response.text
        except Exception as e:
            print(f"Error in image analysis: {str(e)}")
            return self._analyze_text(text)  # Fallback to text-only analysis

    def generate_content(self, prompt):
        """Direct generation method for simple prompts"""
        if self.gemini:
            return self.gemini.generate_content(prompt)
        # Fallback response if no model is configured
        return type('Response', (), {'text': 'Model not configured'})()