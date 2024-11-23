from google.generativeai import configure
import google.generativeai as genai

class GeminiConfig:
    def __init__(self, api_key):
        configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-1.5-pro')
        
    async def get_chat(self):
        return self.model.start_chat(history=[]) 