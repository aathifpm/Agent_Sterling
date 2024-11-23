class ThreadGenerator:
    def __init__(self, gemini_config):
        self.llm = gemini_config.model

    def generate_thread(self, topic):
        prompt = f"""
        Create a viral Twitter thread about:
        {topic}
        
        Requirements:
        1. 5 tweets maximum
        2. Each tweet under 280 characters
        3. Engaging and informative
        4. Include hooks and transitions
        5. Use relevant hashtags
        6. End with a call to action
        
        Format:
        Tweet 1: [hook]
        Tweet 2: [main point 1]
        Tweet 3: [main point 2]
        Tweet 4: [main point 3]
        Tweet 5: [conclusion + CTA]
        """
        
        try:
            response = self.llm.generate_content(prompt)
            return self._format_thread(response.text)
        except Exception as e:
            print(f"Error generating thread: {str(e)}")
            return []

    def _format_thread(self, response):
        try:
            # Split into individual tweets and clean up
            tweets = [tweet.strip() for tweet in response.split('Tweet') if tweet.strip()]
            return [tweet[3:] if tweet.startswith(' ') else tweet for tweet in tweets]
        except Exception as e:
            print(f"Error formatting thread: {str(e)}")
            return [] 