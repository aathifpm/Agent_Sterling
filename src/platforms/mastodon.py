from mastodon import Mastodon
from typing import List, Dict, Optional
import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
import google.generativeai as genai
import os
from dotenv import load_dotenv
import re
import time
import asyncio

# Download required NLTK data
nltk.download('punkt')
nltk.download('stopwords')

class MastodonPlatform:
    def __init__(self, credentials: Dict):
        self.client = Mastodon(
            client_id=credentials.get('client_id'),
            client_secret=credentials.get('client_secret'),
            access_token=credentials.get('access_token'),
            api_base_url=credentials.get('instance_url')
        )
        
        # Initialize Gemini
        load_dotenv()
        genai.configure(api_key=os.getenv('GEMINI_API_KEY'))
        self.model = genai.GenerativeModel('gemini-1.5-pro')
        
        # Rate limiting settings
        self.last_request_time = 0
        self.request_count = 0
        self.max_requests_per_minute = 30  # Reduced from 60 to be safer
        self.retry_delay = 5  # Increased from 2 to 5 seconds

    def _clean_html(self, text: str) -> str:
        """Remove HTML tags and clean up text"""
        clean_text = re.sub(r'<[^>]+>', '', text)
        clean_text = re.sub(r'http\S+|www.\S+', '', clean_text)
        clean_text = ' '.join(clean_text.split())
        return clean_text

    async def _handle_rate_limit(self):
        """Handle API rate limiting"""
        current_time = time.time()
        time_diff = current_time - self.last_request_time
        
        # Reset counter after a minute
        if time_diff >= 60:
            self.request_count = 0
            self.last_request_time = current_time
        
        # If we're at the limit, wait
        if self.request_count >= self.max_requests_per_minute:
            wait_time = 60 - time_diff
            if wait_time > 0:
                print(f"Rate limit reached, waiting {wait_time:.1f} seconds...")
                await asyncio.sleep(wait_time)
                self.request_count = 0
                self.last_request_time = time.time()
        
        # Add small delay between requests
        await asyncio.sleep(2)  # Add 2-second delay between requests
        self.request_count += 1

    async def generate_entertainment_response(self, post_text: str, max_retries=3) -> str:
        """Generate a short, fun response using Gemini"""
        clean_text = self._clean_html(post_text)
        
        prompt = f"""
        Create a fun, short response to: "{clean_text}"
        Rules:
        - Maximum 2 sentences
        - Include 1-2 emojis
        - Be witty and friendly
        - Match the post's tone
        - Add a relevant pop culture reference if it fits naturally
        
        Format: Just the response text with emojis.
        """
        
        for attempt in range(max_retries):
            try:
                # Add longer delay between Gemini API calls
                await asyncio.sleep(5)  # Wait 5 seconds between attempts
                response = self.model.generate_content(prompt)
                return response.text[:240].strip()
            except Exception as e:
                if attempt < max_retries - 1:
                    wait_time = 10 * (attempt + 1)  # Longer wait times between retries
                    print(f"Retry {attempt + 1}/{max_retries} after {wait_time}s...")
                    await asyncio.sleep(wait_time)
                else:
                    # Generate a simple response instead of the default message
                    return "✨ Interesting perspective! Thanks for sharing! 🌟"

    async def search_hashtag(self, hashtag: str, limit: int = 5) -> List[Dict]:
        """Search and respond to hashtag posts with rate limiting"""
        try:
            await self._handle_rate_limit()
            hashtag = hashtag.strip('#')
            results = self.client.timeline_hashtag(hashtag, limit=limit)
            formatted_posts = []
            
            for status in results:
                post = self._format_post(status)
                formatted_posts.append(post)
            
            return formatted_posts
        except Exception as e:
            print(f"Error searching hashtag {hashtag}: {str(e)}")
            return [{"error": str(e)}]

    async def reply_to_post(self, post_id: str, content: str) -> Dict:
        """Post a reply with rate limiting"""
        try:
            await self._handle_rate_limit()
            status = self.client.status_post(
                content,
                in_reply_to_id=post_id,
                visibility="public"
            )
            return self._format_post(status)
        except Exception as e:
            print(f"Error replying to post: {str(e)}")
            return {"error": str(e)}

    def _format_post(self, status: Dict) -> Dict:
        """Format post with key information"""
        try:
            # Clean the content
            clean_content = self._clean_html(status['content'])
            
            # Extract keywords
            tokens = word_tokenize(clean_content.lower())
            stop_words = set(stopwords.words('english'))
            keywords = [word for word in tokens 
                       if word.isalnum() and word not in stop_words][:5]
            
            return {
                "id": status['id'],
                "content": clean_content,
                "author": status['account']['acct'],
                "keywords": keywords,
                "created_at": status['created_at']
            }
        except Exception as e:
            print(f"Error formatting post: {str(e)}")
            return {"error": str(e)}

    async def get_mentions(self, limit: int = 3) -> List[Dict]:
        """Get recent mentions with rate limiting"""
        try:
            await self._handle_rate_limit()
            mentions = self.client.notifications(
                types=['mention'],
                limit=limit
            )
            
            responses = []
            for mention in mentions:
                mention_data = self._format_post(mention['status'])
                response = await self.handle_mention(mention['status'])
                responses.append({
                    "mention": mention_data,
                    "response": response
                })
            
            return responses
        except Exception as e:
            print(f"Error getting mentions: {str(e)}")
            return [{"error": str(e)}]

    async def handle_mention(self, mention: Dict) -> Dict:
        """Handle mentions with rate limiting"""
        try:
            post = self._format_post(mention)
            response = await self.generate_entertainment_response(post['content'])
            reply = await self.reply_to_post(post['id'], response)
            
            return {
                "status": "success",
                "response": response,
                "reply": reply
            }
        except Exception as e:
            print(f"Error handling mention: {str(e)}")
            return {"error": str(e)}