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
        self.max_requests_per_minute = 1000  # Adjust based on your API limits
        self.retry_delay = 2  # seconds between retries

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
        
        self.request_count += 1

    async def generate_entertainment_response(self, post_text: str, max_retries=3) -> str:
        """Generate a short, fun response with retry logic"""
        clean_text = self._clean_html(post_text)
        
        prompt = f"""
        Create a fun, short response to: "{clean_text}"
        Rules:
        - Maximum 2 sentences
        - Include 1-2 emojis
        - Be witty and friendly
        - Match the post's tone
        
        Format: Just the response text with emojis.
        """
        
        for attempt in range(max_retries):
            try:
                await self._handle_rate_limit()
                response = self.model.generate_content(prompt)
                return response.text[:240].strip()
            except Exception as e:
                if attempt < max_retries - 1:
                    wait_time = self.retry_delay * (attempt + 1)
                    print(f"Retry {attempt + 1}/{max_retries} after {wait_time}s...")
                    await asyncio.sleep(wait_time)
                else:
                    return f"🤖 Having a moment... Will be back soon! ✨"

    async def search_hashtag(self, hashtag: str, limit: int = 5) -> List[Dict]:
        """Search and respond to hashtag posts with rate limiting"""
        try:
            hashtag = hashtag.strip('#')
            results = self.client.timeline_hashtag(hashtag, limit=limit)
            formatted_posts = []
            
            for status in results:
                post = self._format_post(status)
                # Add delay between responses
                await asyncio.sleep(1)
                response = await self.generate_entertainment_response(post['content'])
                post['ai_response'] = response
                formatted_posts.append(post)
            
            return formatted_posts
        except Exception as e:
            return [{"error": str(e)}]

    async def interact_with_post(self, post_id: str) -> Dict:
        """Interact with a post"""
        try:
            status = self.client.status(post_id)
            post = self._format_post(status)
            
            # Generate response
            response = await self.generate_entertainment_response(post['content'])
            
            # Post reply
            reply_result = await self.reply_to_post(post_id, response)
            
            return {
                "post": post,
                "response": response,
                "reply_result": reply_result
            }
        except Exception as e:
            return {"error": str(e)}

    async def reply_to_post(self, post_id: str, content: str) -> Dict:
        """Post a reply"""
        try:
            # Mastodon automatically handles the @ mention when replying
            status = self.client.status_post(
                content,
                in_reply_to_id=post_id,
                visibility="public"
            )
            return self._format_post(status)
        except Exception as e:
            return {"error": str(e)}

    def _format_post(self, status: Dict) -> Dict:
        """Format post with key information"""
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

    async def handle_mention(self, mention: Dict) -> Dict:
        """Handle mentions with fun responses"""
        try:
            post = self._format_post(mention)
            clean_text = self._clean_html(post['content'])
            
            # Generate entertaining response for mention
            prompt = f"""
            Create a friendly response to: "{clean_text}"
            
            Rules:
            - Maximum 2 sentences
            - Include 1-2 emojis
            - Be conversational and engaging
            - Keep it fun and friendly
            - No need to include greetings or mentions
            
            Format: Just the response text with emojis.
            """
            
            response = self.model.generate_content(prompt)
            reply_text = response.text[:240].strip()  # Ensure length limit
            
            # Post the reply (Mastodon handles the @ mention automatically)
            reply = await self.reply_to_post(post['id'], reply_text)
            
            return {
                "status": "success",
                "original_mention": post,
                "response": reply_text,
                "reply": reply
            }
        except Exception as e:
            return {"error": str(e)}

    async def get_mentions(self, limit: int = 10) -> List[Dict]:
        """Get recent mentions and handle them"""
        try:
            # Get notifications that are mentions
            mentions = self.client.notifications(
                types=['mention'],
                limit=limit
            )
            
            responses = []
            for mention in mentions:
                # Format the mention
                mention_data = self._format_post(mention['status'])
                
                # Generate and post response
                response = await self.handle_mention(mention['status'])
                
                responses.append({
                    "mention": mention_data,
                    "response": response
                })
            
            return responses
        except Exception as e:
            return [{"error": str(e)}]