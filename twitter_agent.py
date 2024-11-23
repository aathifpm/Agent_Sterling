import asyncio
import os
import tweepy
import google.generativeai as genai
from dotenv import load_dotenv
from datetime import datetime, timedelta
import time
from typing import Optional, List

# Load environment variables
load_dotenv()

# Twitter API Credentials
TWITTER_API_KEY = os.getenv('TWITTER_API_KEY')
TWITTER_API_SECRET = os.getenv('TWITTER_API_SECRET')
TWITTER_ACCESS_TOKEN = os.getenv('TWITTER_ACCESS_TOKEN')
TWITTER_ACCESS_SECRET = os.getenv('TWITTER_ACCESS_TOKEN_SECRET') # Fixed variable name
TWITTER_BEARER_TOKEN = os.getenv('TWITTER_BEARER_TOKEN')

# Gemini API Key
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
genai.configure(api_key=GEMINI_API_KEY)

class TwitterAIAgent:
    def __init__(self):
        # Initialize Twitter client with write permissions
        try:
            self.client = tweepy.Client(
                bearer_token=os.getenv('TWITTER_BEARER_TOKEN'),
                consumer_key=os.getenv('TWITTER_API_KEY'),
                consumer_secret=os.getenv('TWITTER_API_SECRET'),
                access_token=os.getenv('TWITTER_ACCESS_TOKEN'),
                access_token_secret=os.getenv('TWITTER_ACCESS_TOKEN_SECRET'),
                wait_on_rate_limit=True
            )
            # Test write permissions
            self._verify_write_permissions()
        except Exception as e:
            print(f"Authentication Error: {str(e)}")
            raise

        self.model = genai.GenerativeModel('gemini-1.5-pro')
        self.request_count = 0
        self.last_request_time = time.time()

    def _verify_write_permissions(self):
        """Verify that the app has write permissions"""
        try:
            # Try to post a test tweet
            test_tweet = self.client.create_tweet(text="Testing permissions... (will be deleted)")
            if test_tweet and test_tweet.data:
                # Delete the test tweet immediately
                self.client.delete_tweet(test_tweet.data['id'])
                print("Write permissions verified successfully")
            return True
        except Exception as e:
            print(f"Write permissions verification failed: {str(e)}")
            print("Please ensure your Twitter App has Read and Write permissions enabled")
            return False

    async def _handle_rate_limit(self):
        """Handle Gemini API rate limiting"""
        self.request_count += 1
        current_time = time.time()
        
        # Reset counter after 60 seconds
        if current_time - self.last_request_time >= 60:
            self.request_count = 0
            self.last_request_time = current_time
            
        # If we've made too many requests, wait
        if self.request_count >= 60:  # Gemini's limit
            wait_time = 60 - (current_time - self.last_request_time)
            if wait_time > 0:
                print(f"Rate limit reached, waiting {wait_time:.2f} seconds...")
                await asyncio.sleep(wait_time)
                self.request_count = 0
                self.last_request_time = time.time()

    def get_user_tweets(self, username: str, max_results: int = 5) -> Optional[List]:
        """Get recent tweets from a specific user"""
        try:
            # Get user ID first
            user_response = self.client.get_user(username=username)
            if not user_response or not user_response.data:
                print(f"Could not find user: {username}")
                return None

            # Get tweets with a single API call
            tweets = self.client.get_users_tweets(
                id=user_response.data.id,
                max_results=max_results,
                tweet_fields=['created_at', 'public_metrics']
            )

            if not tweets.data:
                print(f"No tweets found for user: {username}")
                return []

            return tweets.data

        except tweepy.TooManyRequests as e:
            print(f"Rate limit exceeded. Details: {str(e)}")
            return None
        except tweepy.Unauthorized as e:
            print(f"Authentication error. Check your API keys. Details: {str(e)}")
            return None
        except Exception as e:
            print(f"Error: {str(e)}")
            return None

    def search_tweets(self, query, max_results=10):
        """Search for tweets containing specific keywords"""
        try:
            # Search tweets from the last 7 days (Twitter API limitation for basic access)
            tweets = self.client.search_recent_tweets(
                query=query,
                max_results=max_results,
                tweet_fields=['created_at', 'public_metrics']
            )
            return tweets.data if tweets.data else []
        except Exception as e:
            return f"Error: {str(e)}"

    async def analyze_tweet(self, tweet_text):
        await self._handle_rate_limit()
        """Analyze a single tweet using Gemini"""
        prompt = f"""
        Analyze this tweet:
        "{tweet_text}"
        
        Provide:
        1. Main topic/theme
        2. Sentiment analysis
        3. Key points or insights
        4. Suggested response (if appropriate)
        """
        
        response = self.model.generate_content(prompt)
        return response.text

    async def generate_entertainment_response(self, tweet_text):
        await self._handle_rate_limit()
        """Generate an entertaining analysis/response to a tweet"""
        prompt = f"""
        Create an entertaining analysis of this tweet:
        "{tweet_text}"
        
        Requirements:
        1. Be witty and humorous
        2. Include playful observations
        3. Add pop culture references if relevant
        4. Use emojis where appropriate
        5. Keep it fun and engaging
        
        Format your response as:
        🎭 Vibe Check: [overall mood/vibe]
        🎯 The Tea: [witty observation]
        🌟 Pop Culture Corner: [any relevant references]
        🎪 Entertainment Value: [rating out of 10]
        """
        
        response = self.model.generate_content(prompt)
        return response.text

    async def reply_to_tweet(self, tweet_id, reply_text):
        """Reply to a tweet with rate limiting and error handling"""
        try:
            # Ensure the reply starts with the @ mention
            if not reply_text.startswith('@'):
                reply_text = f"@{tweet_id} {reply_text}"

            response = self.client.create_tweet(
                text=reply_text[:280],  # Twitter character limit
                in_reply_to_tweet_id=tweet_id
            )
            return {"status": "success", "reply_id": response.data['id']}
        except tweepy.Forbidden as e:
            print("Error: Write permissions not enabled. Please check your Twitter App settings.")
            return {"status": "error", "message": str(e)}
        except Exception as e:
            return {"status": "error", "message": str(e)}

def test_authentication():
    """Test Twitter API authentication"""
    try:
        agent = TwitterAIAgent()
        # Try to get your own user info as a test
        me = agent.client.get_me()
        if me.data:
            print(f"Successfully authenticated as: {me.data.username}")
            return True
        return False
    except Exception as e:
        print(f"Authentication failed: {str(e)}")
        return False

async def test_agent():
    agent = TwitterAIAgent()
    
    print("\n=== Twitter AI Agent Test ===\n")
    
    test_username = "Dr_abul_khalifa"
    print(f"Getting recent tweets from @{test_username}:")
    tweets = agent.get_user_tweets(test_username, max_results=5)
    
    if tweets is None:
        print("Failed to fetch tweets. Please try again later.")
        return
        
    if not tweets:
        print(f"No tweets found for @{test_username}")
        return
        
    for tweet in tweets:
        print(f"\nTweet: {tweet.text}")
        
        try:
            # Regular analysis
            print("\n🔍 Standard Analysis:")
            analysis = await agent.analyze_tweet(tweet.text)
            print(analysis)
            
            # Entertainment analysis
            print("\n🎭 Entertainment Analysis:")
            entertainment = await agent.generate_entertainment_response(tweet.text)
            print(entertainment)
            
            # Generate and post reply
            reply = await agent.generate_entertainment_response(tweet.text)
            reply_result = await agent.reply_to_tweet(tweet.id, reply[:280])  # Twitter char limit
            print("\n📤 Reply Status:", reply_result)
            
            print("\n" + "=" * 50 + "\n")
            await asyncio.sleep(1)  # Rate limiting
            
        except Exception as e:
            print(f"Error processing tweet: {str(e)}")
            continue

def check_api_limits():
    """Check your Twitter API access level"""
    try:
        agent = TwitterAIAgent()
        # Try to get rate limit status
        response = agent.client.get_me()
        print("API Access Level:")
        print(f"Rate limit remaining: {response.rate_limit_remaining}")
        print(f"Rate limit reset: {response.rate_limit_reset}")
    except Exception as e:
        print(f"Could not check API limits: {str(e)}")

if __name__ == "__main__":
    # Check for required environment variables
    required_vars = [
        'TWITTER_API_KEY',
        'TWITTER_API_SECRET',
        'TWITTER_ACCESS_TOKEN',
        'TWITTER_ACCESS_TOKEN_SECRET', # Fixed variable name
        'TWITTER_BEARER_TOKEN',
        'GEMINI_API_KEY'
    ]
    
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print("Missing required environment variables:")
        for var in missing_vars:
            print(f"- {var}")
        print("\nPlease add them to your .env file:")
        exit(1)
    
    print("Testing Twitter API Authentication...")
    if test_authentication():
        check_api_limits()
        asyncio.run(test_agent())
    else:
        print("Authentication failed. Please check your credentials.") 