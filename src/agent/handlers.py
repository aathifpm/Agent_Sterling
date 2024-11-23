class AgentHandlers:
    def __init__(self, twitter_client, gemini_handler):
        self.client = twitter_client
        self.llm = gemini_handler

    def handle_image_analysis(self, tweet):
        """Handle Picture Perfect Agent functionality"""
        image = self._extract_image(tweet)
        analysis = self.llm.analyze_content(tweet.text, image)
        response = self.llm.generate_content(f"Create a friendly response about: {analysis}")
        return response.text

    def handle_research(self, tweet):
        """Handle Screenshot + Research Agent functionality"""
        prompt = f"""
        Research and analyze this topic:
        {tweet.text}
        
        Provide:
        1. Key findings
        2. Related insights
        3. Relevant context
        Format as a concise summary.
        """
        research = self.llm.generate_content(prompt)
        return research.text

    def _extract_image(self, tweet):
        """Extract image from tweet if present"""
        try:
            if hasattr(tweet, 'attachments') and tweet.attachments:
                media = tweet.attachments.get('media', [])
                if media and media[0]['type'] == 'photo':
                    return media[0]['url']
        except Exception:
            pass
        return None 