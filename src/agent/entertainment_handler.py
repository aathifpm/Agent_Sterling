class EntertainmentHandler:
    def __init__(self, twitter_client, gemini_model):
        self.client = twitter_client
        self.model = gemini_model

    async def handle_reply(self, tweet_id, tweet_text):
        """Generate and post an entertaining reply to a tweet"""
        # Generate entertaining response
        prompt = f"""
        Create an entertaining reply to this tweet: "{tweet_text}"
        
        Requirements:
        1. Be witty and engaging
        2. Stay under 280 characters
        3. Match the tweet's tone
        4. Add relevant emojis if appropriate
        5. Keep it fun and light
        
        Format: Just the reply text, no explanations.
        """
        
        response = self.model.generate_content(prompt)
        reply_text = response.text.strip()
        
        # Post the reply
        try:
            self.client.create_tweet(
                text=reply_text,
                in_reply_to_tweet_id=tweet_id
            )
            return {"status": "success", "reply": reply_text}
        except Exception as e:
            return {"status": "error", "message": str(e)} 