import os
from dotenv import load_dotenv
from src.config.gemini_config import GeminiConfig

def test_gemini_setup():
    # Load environment variables
    load_dotenv()
    
    # Get API key
    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key:
        print("ERROR: GEMINI_API_KEY not found in .env file")
        return False
        
    try:
        # Test Gemini configuration
        config = GeminiConfig(api_key)
        
        # Test generate content
        response = config.model.generate_content("Test message")
        print("Gemini test response:", response.text)
        
        return True
    except Exception as e:
        print(f"Error testing Gemini setup: {str(e)}")
        return False

if __name__ == "__main__":
    success = test_gemini_setup()
    print("Setup test:", "PASSED" if success else "FAILED") 