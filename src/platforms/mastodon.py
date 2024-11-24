from mastodon import Mastodon
from typing import List, Dict, Optional
import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
import google.generativeai as genai
import os
from dotenv import load_dotenv
import re

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

    def _clean_html(self, text: str) -> str:
        """Remove HTML tags and clean up text"""
        # Remove HTML tags
        clean_text = re.sub(r'<[^>]+>', '', text)
        # Remove URLs
        clean_text = re.sub(r'http\S+|www.\S+', '', clean_text)
        # Remove multiple spaces and newlines
        clean_text = ' '.join(clean_text.split())
        return clean_text

    async def generate_entertainment_response(self, post_text: str) -> str:
        """Generate a short, fun response using Gemini"""
        # Clean the post text first
        clean_text = self._clean_html(post_text)
        
        prompt = f"""
        Create a fun, short response to this post: "{clean_text}"
        
        Rules:
        - Maximum 2 sentences
        - Include 1-2 emojis
        - Be witty and friendly
        - Match the post's tone
        - Add a relevant pop culture reference if it fits naturally
        
        Format: Just the response text with emojis, no labels or sections.
        """
        
        try:
            response = self.model.generate_content(prompt)
            return response.text[:240].strip()  # Ensure length limit
        except Exception as e:
            return f"🤖 Having a moment... {str(e)[:100]}"

    async def analyze_post_sentiment(self, post_text: str) -> Dict:
        """Quick sentiment analysis"""
        clean_text = self._clean_html(post_text)
        prompt = f"""
        Analyze: "{clean_text}"
        Return only:
        TONE: [one word]
        TOPIC: [one phrase]
        """
        
        try:
            response = self.model.generate_content(prompt)
            return {"analysis": response.text.strip()}
        except Exception as e:
            return {"error": str(e)}

    async def search_hashtag(self, hashtag: str, limit: int = 20) -> List[Dict]:
        """Search and respond to hashtag posts"""
        try:
            hashtag = hashtag.strip('#')
            results = self.client.timeline_hashtag(hashtag, limit=limit)
            formatted_posts = []
            
            for status in results:
                post = self._format_post(status)
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