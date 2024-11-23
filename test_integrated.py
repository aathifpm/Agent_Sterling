import os
from dotenv import load_dotenv
from src.config.gemini_config import GeminiConfig
from src.features.thread_generator import ThreadGenerator
from src.features.research_agent import ResearchAgent
from src.features.sentiment_analyzer import SentimentAnalyzer

def test_all_features():
    # Load environment variables
    load_dotenv()
    
    # Initialize Gemini config
    gemini_config = GeminiConfig(os.getenv("GEMINI_API_KEY"))
    
    # Initialize components
    thread_gen = ThreadGenerator(gemini_config)
    
    # Test tweet
    test_tweet = "Exploring the future of AI and its impact on society #AI #Future"
    
    # Test thread generation (synchronous)
    results = {
        "thread": thread_gen.generate_thread(test_tweet)
    }
    
    return results

if __name__ == "__main__":
    print(test_all_features()) 