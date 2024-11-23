import asyncio
import tweepy
from dotenv import load_dotenv
import os
from src.agent.base import TwitterAIAgent
from src.listener.stream import TweetStreamListener

async def test_entertainment_replies():
    load_dotenv()
    
    # Initialize credentials
    credentials = {
        'bearer_token': os.getenv('TWITTER_BEARER_TOKEN'),
        'api_key': os.getenv('TWITTER_API_KEY'),
        'api_secret': os.getenv('TWITTER_API_SECRET'),
        'access_token': os.getenv('TWITTER_ACCESS_TOKEN'),
        'access_secret': os.getenv('TWITTER_ACCESS_SECRET')
    }
    
    # Initialize agent
    agent = TwitterAIAgent(credentials)
    
    # Start stream listener
    stream = TweetStreamListener(credentials['bearer_token'], agent)
    
    # Add rule to track mentions of your bot
    stream.add_rules(tweepy.StreamRule("@your_bot_handle"))
    
    # Start streaming
    print("Starting stream listener...")
    stream.filter()

if __name__ == "__main__":
    asyncio.run(test_entertainment_replies())