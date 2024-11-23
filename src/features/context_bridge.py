class ContextBridge:
    def __init__(self, twitter_client):
        self.client = twitter_client
    
    async def get_thread_context(self, tweet_id):
        """Get the full context of a tweet thread"""
        try:
            # Get conversation ID
            tweet = self.client.get_tweet(
                tweet_id, 
                tweet_fields=['conversation_id']
            )
            
            if not tweet.data:
                return []
                
            # Get all tweets in the conversation
            thread = self.client.search_recent_tweets(
                query=f"conversation_id:{tweet.data.conversation_id}",
                tweet_fields=['created_at', 'in_reply_to_user_id']
            )
            
            return self._organize_thread(thread.data) if thread.data else []
            
        except Exception as e:
            return {"error": str(e)}
    
    def _organize_thread(self, tweets):
        """Organize tweets in chronological order"""
        return sorted(tweets, key=lambda x: x.created_at)
    
    async def simplify_text(self, complex_text):
        prompt = f"""
        Simplify this technical text for a general audience:
        {complex_text}
        
        Make it:
        1. Easy to understand
        2. Maintain key information
        3. Use simple language
        """
        return await self.llm.analyze_content(prompt) 