import os
import google.generativeai as genai
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure Gemini
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
genai.configure(api_key=GEMINI_API_KEY)

class TestAgent:
    def __init__(self):
        self.model = genai.GenerativeModel('gemini-1.5-pro')
    
    async def research_topic(self, tweet_text):
        prompt = f"""
        Based on this tweet, provide a detailed research summary:
        Tweet: {tweet_text}
        
        Requirements:
        1. Key facts and context
        2. Related important information
        3. Present in a thread-friendly format (3-5 points)
        """
        
        response = self.model.generate_content(prompt)
        return response.text
    
    async def analyze_sentiment(self, tweet_text):
        prompt = f"""
        Analyze the sentiment of this tweet:
        {tweet_text}
        
        Provide:
        1. Overall sentiment (positive/negative/neutral)
        2. Confidence level
        3. Key emotional indicators
        Format as JSON.
        """
        
        response = self.model.generate_content(prompt)
        return response.text

# Test function
def run_tests():
    agent = TestAgent()
    
    # Test tweets
    test_tweets = [
        "I absolutely love how AI is transforming the way we work! #AI #Future",
        "This new phone is terrible, worst purchase ever. Don't buy it! 😡",
        "Just published a research paper on quantum computing breakthroughs"
    ]
    
    print("\n=== Testing Agent ===\n")
    
    for tweet in test_tweets:
        print(f"Testing tweet: {tweet}\n")
        
        # Test research
        print("Research Analysis:")
        research_result = agent.research_topic(tweet)
        print(research_result)
        print("\n---\n")
        
        # Test sentiment
        print("Sentiment Analysis:")
        sentiment_result = agent.analyze_sentiment(tweet)
        print(sentiment_result)
        print("\n=================\n")

async def run_full_test():
    agent = TwitterAIAgent()
    intent_classifier = IntentClassifier(agent.model)
    context_bridge = ContextBridge(agent.client)
    
    test_tweet = "What's the latest research on AI safety? #AI #AGI"
    
    # Classify intent
    intent = await intent_classifier.classify_intent(test_tweet)
    print(f"Detected Intent: {intent}")
    
    # Route to appropriate handler
    router = IntentRouter(agent.model)
    result = await router.route(intent, test_tweet)
    print(f"Handler Result: {result}")

if __name__ == "__main__":
    # Create .env file if it doesn't exist
    if not os.path.exists('.env'):
        with open('.env', 'w') as f:
            f.write('GEMINI_API_KEY=your_key_here')
        print("Created .env file. Please add your Gemini API key to it.")
        exit(1)
        
    if GEMINI_API_KEY is None or GEMINI_API_KEY == 'your_key_here':
        print("Please add your Gemini API key to the .env file")
        exit(1)
        
    run_tests() 