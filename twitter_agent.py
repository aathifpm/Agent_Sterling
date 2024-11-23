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
TWITTER_ACCESS_SECRET = os.getenv('TWITTER_ACCESS_TOKEN_SECRET') 
TWITTER_BEARER_TOKEN = os.getenv('TWITTER_BEARER_TOKEN')

# Gemini API Key
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
genai.configure(api_key=GEMINI_API_KEY)

class TwitterAIAgent:
    def __init__(self):
        # Initialize Twitter client with write permissions
        try:
            # Initialize API v1 client for write operations
            auth = tweepy.OAuthHandler(
                os.getenv('TWITTER_API_KEY'),
                os.getenv('TWITTER_API_SECRET')
            )
            auth.set_access_token(
                os.getenv('TWITTER_ACCESS_TOKEN'),
                os.getenv('TWITTER_ACCESS_TOKEN_SECRET')
            )
            self.api = tweepy.API(auth)

            # Initialize API v2 client
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
        self.monthly_tweet_limit = 50000
        self.daily_tweet_limit = self.monthly_tweet_limit // 30
        self.tweet_counter = 0

    def _verify_write_permissions(self):
        """Verify that the app has write permissions"""
        try:
            # Try to post a test tweet using API v1
            test_tweet = self.api.update_status("Testing permissions... (will be deleted)")
            if test_tweet:
                # Delete the test tweet immediately
                self.api.destroy_status(test_tweet.id)
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
            # Ensure max_results is within valid range (5-100)
            max_results = max(5, min(max_results, 100))
            
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
            # Ensure max_results is within valid range
            max_results = max(5, min(max_results, 100))
            
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
        """Analyze a single tweet using Gemini"""
        await self._handle_rate_limit()
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
        """Generate an entertaining analysis/response to a tweet"""
        await self._handle_rate_limit()
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

            # Use API v1 for replies
            response = self.api.update_status(
                status=reply_text[:280],  # Twitter character limit
                in_reply_to_status_id=tweet_id,
                auto_populate_reply_metadata=True
            )
            return {"status": "success", "reply_id": response.id}
        except tweepy.Forbidden as e:
            print("Error: Write permissions not enabled. Please check your Twitter App settings.")
            return {"status": "error", "message": str(e)}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    async def smart_engagement(self, tweet_id):
        """Smart engagement based on tweet analysis"""
        # Analyze tweet
        analysis = await self.analyze_tweet(tweet_id)
        
        # If positive sentiment and relevant content
        if self._should_engage(analysis):
            await self.like_tweet(tweet_id)
            
            # Generate and post reply if appropriate
            if self._should_reply(analysis):
                reply = await self.generate_entertainment_response(analysis)
                await self.reply_to_tweet(tweet_id, reply)

    async def check_rate_limits(self):
        """Enhanced rate limit checking"""
        if self.tweet_counter >= self.daily_tweet_limit:
            print("Daily tweet limit reached")
            return False
        return True

    async def implement_basic_features(self):
        """
        Free Tier Available Features:
        1. Read Operations
        - get_user_tweets()
        - search_tweets()
        - get_tweet_metrics()
        
        2. Write Operations
        - create_tweet()
        - reply_to_tweet()
        - like_tweet()
        - retweet()
        """
        pass

    async def get_tweet_metrics(self, tweet_id):
        """Get basic engagement metrics for a tweet"""
        try:
            tweet = self.client.get_tweet(
                tweet_id,
                tweet_fields=['public_metrics']
            )
            return tweet.data.public_metrics if tweet.data else None
        except Exception as e:
            return {"error": str(e)}

    async def like_tweet(self, tweet_id):
        """Like a tweet"""
        try:
            # Use API v1 for liking tweets
            result = self.api.create_favorite(tweet_id)
            return {"status": "success", "data": result._json}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    async def retweet(self, tweet_id):
        """Retweet a tweet"""
        try:
            # Use API v1 for retweeting
            result = self.api.retweet(tweet_id)
            return {"status": "success", "data": result._json}
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
    tweets = agent.get_user_tweets(test_username, max_results=5)  # Minimum 5 results
    
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
            
            # Generate and post reply (using entertainment response)
            reply = await agent.generate_entertainment_response(tweet.text)
            reply_result = await agent.reply_to_tweet(tweet.id, reply[:280])
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
        # Get rate limits using API v1
        limits = agent.api.rate_limit_status()
        print("API Access Level:")
        print("Rate Limits:")
        for endpoint, data in limits['resources'].items():
            for path, details in data.items():
                if details['remaining'] < details['limit']:
                    print(f"{path}:")
                    print(f"  Remaining: {details['remaining']}/{details['limit']}")
                    reset_time = datetime.fromtimestamp(details['reset'])
                    print(f"  Reset at: {reset_time}")
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