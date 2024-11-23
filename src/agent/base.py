import tweepy
from src.config.gemini_config import GeminiConfig
from src.agent.handlers import AgentHandlers
from src.agent.llm_handler import GeminiHandler

class TwitterAIAgent:
    def __init__(self, api_credentials, gemini_config=None):
        # Initialize Twitter client
        self.client = tweepy.Client(
            bearer_token=api_credentials['bearer_token'],
            consumer_key=api_credentials['api_key'],
            consumer_secret=api_credentials['api_secret'],
            access_token=api_credentials['access_token'],
            access_token_secret=api_credentials['access_secret']
        )
        self.llm = GeminiHandler(gemini_config)
        self.handlers = AgentHandlers(self.client, self.llm)

    async def handle_mention(self, mention):
        """Handle incoming mentions and generate replies"""
        try:
            # Get the tweet being replied to
            parent_tweet = self.client.get_tweet(mention.referenced_tweet_id)
            if not parent_tweet.data:
                return {"error": "Could not find parent tweet"}

            # Generate and post reply
            if self._has_image(parent_tweet.data):
                result = self.handlers.handle_image_analysis(parent_tweet.data)
            else:
                result = self.handlers.handle_research(parent_tweet.data)
            return {"response": result}
        except Exception as e:
            return {"error": str(e)}

    def _has_image(self, tweet):
        """Check if tweet has an image attachment"""
        return (hasattr(tweet, 'attachments') and 
                tweet.attachments and
                any(m['type'] == 'photo' for m in tweet.attachments.get('media', [])))