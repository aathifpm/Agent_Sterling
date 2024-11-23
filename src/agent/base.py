import tweepy
import genai
from entertainment_handler import EntertainmentHandler

class TwitterAIAgent:
    def __init__(self, api_credentials):
        # Initialize Twitter client
        self.client = tweepy.Client(
            bearer_token=api_credentials['bearer_token'],
            consumer_key=api_credentials['api_key'],
            consumer_secret=api_credentials['api_secret'],
            access_token=api_credentials['access_token'],
            access_token_secret=api_credentials['access_secret']
        )
        self.model = genai.GenerativeModel('gemini-1.5-pro')
        self.entertainment_handler = EntertainmentHandler(self.client, self.model)

    async def handle_mention(self, mention):
        """Handle incoming mentions and generate entertaining replies"""
        try:
            # Get the tweet being replied to
            parent_tweet = self.client.get_tweet(mention.referenced_tweet_id)
            if not parent_tweet.data:
                return {"error": "Could not find parent tweet"}

            # Generate and post reply
            result = await self.entertainment_handler.handle_reply(
                tweet_id=mention.id,
                tweet_text=parent_tweet.data.text
            )
            return result
        except Exception as e:
            return {"error": str(e)}