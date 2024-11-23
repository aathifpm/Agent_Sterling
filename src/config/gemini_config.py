from google.generativeai import configure
import google.generativeai as genai

class GeminiConfig:
    def __init__(self, api_key):
        if not api_key:
            raise ValueError("Gemini API key is required")
        
        # Configure the Gemini API
        genai.configure(api_key=api_key)
        try:
            self.model = genai.GenerativeModel('gemini-1.5-pro')
        except Exception as e:
            raise Exception(f"Failed to initialize Gemini model: {str(e)}")
        
    async def get_chat(self):
        return self.model.start_chat(history=[]) 