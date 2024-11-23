import tweepy

class TweetStreamListener(tweepy.StreamingClient):
    def __init__(self, bearer_token, agent):
        super().__init__(bearer_token)
        self.agent = agent

    async def on_tweet(self, tweet):
        """Handle incoming tweets"""
        if tweet.referenced_tweets:  # This is a reply
            await self.agent.handle_mention(tweet) 