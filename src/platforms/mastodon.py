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
import requests
from io import BytesIO
from PIL import Image
from datetime import datetime, timedelta
import heapq
import json
import random

# Download required NLTK data
nltk.download('punkt')
nltk.download('stopwords')

class PostStyle:
    MEME = "meme"
    ENTERTAINER = "entertainer"
    INFORMATIVE = "informative"
    STORYTELLER = "storyteller"
    ANALYST = "analyst"

class MastodonPlatform:
    def __init__(self, credentials: Dict):
        self.client = Mastodon(
            client_id=credentials.get('client_id'),
            client_secret=credentials.get('client_secret'),
            access_token=credentials.get('access_token'),
            api_base_url=credentials.get('instance_url')
        )
        
        # Initialize Gemini with provided key
        genai.configure(api_key=credentials.get('gemini_api_key'))
        self.model = genai.GenerativeModel('gemini-1.5-pro')
        
        # Rate limiting settings
        self.last_request_time = 0
        self.request_count = 0
        self.max_requests_per_minute = 30  # Reduced from 60 to be safer
        self.retry_delay = 5  # Increased from 2 to 5 seconds
        
        # Add new attributes for autonomous posting
        self.auto_post_interval = 60  # 30 minutes in seconds
        self.last_auto_post_time = time.time()
        self.trending_cache = []
        self.trending_cache_timeout = 3600  # 1 hour in seconds
        self.last_cache_update = 0
        self.auto_post_interval = 1800  # 30 minutes
        self.last_post_time = time.time()
        self.post_count = 0
        self.max_daily_posts = 48  # 2 posts per hour for 24 hours
        self.current_style = PostStyle.ENTERTAINER  # Default style
        self.replied_dms = set()  # Store IDs of replied DMs
        self.dm_context_file = "dm_context.json"
        self._load_dm_context()
        self.dm_settings = {
            "enabled": False,
            "auto_reply": True,
            "reply_interval": 300
        }
        self.like_settings = {
            "enabled": False,
            "max_likes_per_hour": 20,
            "like_probability": 0.7  # 70% chance to like a trending post
        }
        self.likes_count = 0
        self.last_like_reset = time.time()
        
        # Add missing config parameters
        self.post_config = {
            "use_hashtags": True,
            "max_length": 240,
            "blacklisted_words": []
        }

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

    def _get_media_attachments(self, status: Dict) -> List[Dict]:
        """Extract media attachments from status"""
        try:
            media_attachments = status.get('media_attachments', [])
            return [
                {
                    'url': media['url'],
                    'type': media['type'],
                    'description': media.get('description', '')
                }
                for media in media_attachments
                if media['type'] in ['image']  # Only process images for now
            ]
        except Exception as e:
            print(f"Error processing media attachments: {str(e)}")
            return []

    async def _download_image(self, url: str) -> Optional[Image.Image]:
        """Download and process image from URL"""
        try:
            response = requests.get(url)
            response.raise_for_status()
            return Image.open(BytesIO(response.content))
        except Exception as e:
            print(f"Error downloading image: {str(e)}")
            return None

    async def generate_entertainment_response(self, post_text: str, status: Dict = None, max_retries=3) -> str:
        """Generate a short, fun response using Gemini, including image analysis if present"""
        clean_text = self._clean_html(post_text)
        
        # Get media attachments if status is provided
        images = []
        if status:
            media_attachments = self._get_media_attachments(status)
            for media in media_attachments:
                if image := await self._download_image(media['url']):
                    images.append({
                        'image': image,
                        'description': media['description']
                    })

        # Modify prompt based on presence of images
        base_prompt = f"""Create a fun, short response to this post: "{clean_text}" """
        
        if images:
            base_prompt += "\nThe post includes images which I'll analyze for context."
            base_prompt += "\nIncorporate relevant details from the images in the response."
        
        prompt = base_prompt + """
        Rules:
        - Maximum 2 sentences
        - Include 1-2 emojis
        - Be witty and friendly
        - Match the post's tone
        - Add a relevant pop culture reference if it fits naturally
        - Reference image content naturally (if images present)
        
        Format: Just the response text with emojis.
        """
        
        for attempt in range(max_retries):
            try:
                await asyncio.sleep(5)  # Wait 5 seconds between attempts
                
                if images:
                    # Use multimodal generation if images are present
                    generation_config = {
                        'temperature': 0.7,
                        'top_p': 0.8,
                        'top_k': 40
                    }
                    
                    # Create a list of content parts for multimodal input
                    content_parts = [prompt]
                    for img_data in images:
                        content_parts.append(img_data['image'])
                        if img_data['description']:
                            content_parts.append(f"Image description: {img_data['description']}")
                    
                    response = self.model.generate_content(
                        content_parts,
                        generation_config=generation_config
                    )
                else:
                    # Text-only generation
                    response = self.model.generate_content(prompt)
                
                return response.text[:240].strip()  # Maintain character limit
                
            except Exception as e:
                if attempt < max_retries - 1:
                    wait_time = 10 * (attempt + 1)
                    print(f"Retry {attempt + 1}/{max_retries} after {wait_time}s...")
                    await asyncio.sleep(wait_time)
                else:
                    print(f"Error generating response: {str(e)}")
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
        """Format post with key information including raw status for media processing"""
        try:
            clean_content = self._clean_html(status['content'])
            
            tokens = word_tokenize(clean_content.lower())
            stop_words = set(stopwords.words('english'))
            keywords = [word for word in tokens 
                       if word.isalnum() and word not in stop_words][:5]
            
            return {
                "id": status['id'],
                "content": clean_content,
                "author": status['account']['acct'],
                "keywords": keywords,
                "created_at": status['created_at'],
                "raw_status": status  # Include raw status for media processing
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

    async def process_single_post(self, post: Dict):
        """Process a single post including any images"""
        try:
            response = await self.generate_entertainment_response(
                post['content'],
                status=post['raw_status']  # Pass the original status object
            )
            
            reply = await self.reply_to_post(post['id'], response)
            return reply
        except Exception as e:
            print(f"Error processing post: {str(e)}")
            return {"error": str(e)}

    async def start_auto_posting(self):
        """Start autonomous posting loop"""
        print("Starting autonomous posting service...")
        while True:
            try:
                current_time = time.time()
                if current_time - self.last_auto_post_time >= self.auto_post_interval:
                    await self.create_trending_post()
                    self.last_auto_post_time = current_time
                await asyncio.sleep(60)  # Check every minute
            except Exception as e:
                print(f"Error in auto-posting loop: {str(e)}")
                await asyncio.sleep(300)  # Wait 5 minutes on error

    async def get_trending_posts(self, limit: int = 10) -> List[Dict]:
        """Get trending posts from the instance"""
        try:
            await self._handle_rate_limit()
            trending = self.client.trending_tags()
            posts = []
            
            for tag in trending[:5]:  # Use top 5 trending tags
                results = await self.search_hashtag(tag['name'], limit=2)
                posts.extend(results)
            
            # Sort by engagement (favorites + reblogs)
            sorted_posts = sorted(posts, 
                key=lambda x: (x.get('favourites_count', 0) + x.get('reblogs_count', 0)), 
                reverse=True)
            
            return sorted_posts[:limit]
        except Exception as e:
            print(f"Error getting trending posts: {str(e)}")
            return []

    async def create_trending_post(self):
        """Create a new post based on trending content"""
        try:
            # Get top trending posts
            trending_posts = await self.get_trending_posts(limit=5)
            if not trending_posts:
                return
            
            # Combine trending topics
            trending_content = "\n".join([
                f"- {post['content'][:100]}..." 
                for post in trending_posts
            ])
            
            # Generate summary post
            prompt = f"""
            Based on these trending topics on Mastodon:
            {trending_content}
            
            Create an engaging post that:
            1. Summarizes a key trending topic
            2. Adds valuable insight or perspective
            3. Includes relevant hashtags
            4. Uses 1-2 appropriate emojis
            5. Stays under 240 characters
            
            Format: Just the post text with hashtags and emojis.
            """
            
            response = await self.generate_entertainment_response(prompt)
            
            # Post the content
            await self._handle_rate_limit()
            status = self.client.status_post(
                response,
                visibility="public"
            )
            
            print(f"Auto-posted new content: {response}")
            return self._format_post(status)
            
        except Exception as e:
            print(f"Error creating trending post: {str(e)}")
            return None

    async def schedule_auto_posts(self):
        """Main loop for scheduled auto-posting and DM handling"""
        print("Starting scheduled auto-posting service...")
        first_run = True
        while True:
            try:
                current_time = time.time()
                
                # Handle regular posts
                if first_run or current_time - self.last_post_time >= self.auto_post_interval:
                    if self.post_count < self.max_daily_posts:
                        await self.create_scheduled_post()
                        self.last_post_time = current_time
                        self.post_count += 1
                        print(f"Auto-post complete. Posts today: {self.post_count}/{self.max_daily_posts}")
                    first_run = False
                
                # Handle DMs if enabled
                if self.dm_settings["enabled"] and self.dm_settings["auto_reply"]:
                    if current_time % self.dm_settings["reply_interval"] < 60:
                        await self.handle_direct_messages()
                
                # Handle auto-likes
                if current_time % 300 < 60:  # Check every 5 minutes
                    await self.auto_like_trending_posts()
                
                await asyncio.sleep(60)  # Check every minute
                
            except Exception as e:
                print(f"Error in auto-posting loop: {str(e)}")
                await asyncio.sleep(300)

    async def create_scheduled_post(self):
        """Create an engaging scheduled post"""
        try:
            # Get trending posts for inspiration
            trending = await self.get_trending_posts(limit=3)
            
            # Generate content based on trending topics
            prompt = "Create an engaging social media post about "
            
            if trending:
                topics = [post['keywords'] for post in trending if 'keywords' in post]
                flat_topics = [item for sublist in topics for item in sublist]
                prompt += f"these trending topics: {', '.join(flat_topics[:5])}"
            else:
                prompt += "technology, AI, or digital culture"
                
            prompt += """
            Requirements:
            - Be informative and engaging
            - Include 2-3 relevant hashtags
            - Add 1-2 appropriate emojis
            - Keep it under 240 characters
            - Make it conversation-starting
            """
            
            response = await self.create_styled_post(prompt, self.current_style)
            
            # Post the content
            await self._handle_rate_limit()
            status = self.client.status_post(
                response,
                visibility="public"
            )
            
            print(f"\n✅ Auto-posted: {response}")
            return self._format_post(status)
            
        except Exception as e:
            print(f"Error creating scheduled post: {str(e)}")
            return None

    async def set_post_style(self, style: str) -> bool:
        """Update the posting style"""
        if hasattr(PostStyle, style.upper()):
            self.current_style = getattr(PostStyle, style.upper())
            return True
        return False

    async def create_styled_post(self, content: str, style: str = None) -> str:
        """Create a post with specific style"""
        if not style:
            style = self.current_style

        style_prompts = {
            PostStyle.MEME: """
                Transform this into a meme-style post:
                - Use internet humor
                - Add trending references
                - Include popular emojis
                - Keep it light and funny
                - Add meme-related hashtags
            """,
            PostStyle.ENTERTAINER: """
                Create an entertaining post:
                - Make it fun and engaging
                - Use witty language
                - Include relevant emojis
                - Add pop culture references
                - Keep it conversational
            """,
            PostStyle.INFORMATIVE: """
                Create an informative post:
                - Focus on facts
                - Use clear language
                - Add educational value
                - Include relevant statistics
                - Add topic-specific hashtags
            """,
            PostStyle.STORYTELLER: """
                Transform this into a narrative-style post:
                - Create a mini-story
                - Build intrigue
                - Use descriptive language
                - End with a hook
                - Add story-related hashtags
            """,
            PostStyle.ANALYST: """
                Create an analytical post:
                - Present data-driven insights
                - Include trend analysis
                - Use professional terminology
                - Add relevant metrics
                - Include industry hashtags
            """
        }

        prompt = f"{style_prompts[style]}\n\nContent to transform: {content}"
        
        # Apply length limit
        if self.post_config["max_length"]:
            prompt += f"\nKeep response under {self.post_config['max_length']} characters."

        response = await self.generate_entertainment_response(prompt)
        
        # Add hashtags if enabled
        if self.post_config["use_hashtags"]:
            hashtags = await self._generate_relevant_hashtags(content)
            if len(response) + len(hashtags) <= self.post_config["max_length"]:
                response += f"\n{hashtags}"

        return response

    async def _generate_relevant_hashtags(self, content: str, max_tags: int = 3) -> str:
        """Generate relevant hashtags for the content"""
        try:
            prompt = f"""
            Generate {max_tags} relevant hashtags for this content: "{content}"
            Rules:
            - No spaces in hashtags
            - Related to the main topic
            - Trending if possible
            - Return only the hashtags separated by spaces
            """
            
            response = await self.generate_entertainment_response(prompt)
            hashtags = ' '.join([tag if tag.startswith('#') else f'#{tag}' 
                               for tag in response.split()[:max_tags]])
            return hashtags
        except Exception as e:
            print(f"Error generating hashtags: {str(e)}")
            return ""

    def _load_dm_context(self):
        """Load previously replied DM IDs from file"""
        try:
            if os.path.exists(self.dm_context_file):
                with open(self.dm_context_file, 'r') as f:
                    self.replied_dms = set(json.load(f))
        except Exception as e:
            print(f"Error loading DM context: {str(e)}")
            self.replied_dms = set()

    def _save_dm_context(self):
        """Save replied DM IDs to file"""
        try:
            with open(self.dm_context_file, 'w') as f:
                json.dump(list(self.replied_dms), f)
        except Exception as e:
            print(f"Error saving DM context: {str(e)}")

    async def handle_direct_messages(self):
        """Process and respond to DMs with style"""
        try:
            await self._handle_rate_limit()
            conversations = self.client.conversations()
            
            for conv in conversations:
                last_message = conv['last_status']
                if not last_message:
                    continue
                    
                message_id = last_message['id']
                
                # Skip if already replied
                if message_id in self.replied_dms:
                    continue
                
                # Process the message
                content = self._clean_html(last_message['content'])
                sender = last_message['account']['acct']
                
                # Determine response style based on content
                style = self._determine_message_style(content)
                
                # Generate styled response
                response = await self.create_styled_post(
                    f"Reply to @{sender}: {content}", 
                    style
                )
                
                # Send reply
                await self._handle_rate_limit()
                reply = self.client.status_post(
                    response,
                    visibility="direct",
                    in_reply_to_id=message_id
                )
                
                # Update context
                self.replied_dms.add(message_id)
                self._save_dm_context()
                
                print(f"Replied to DM from @{sender} with style: {style}")
                
        except Exception as e:
            print(f"Error handling DMs: {str(e)}")

    def _determine_message_style(self, content: str) -> str:
        """Determine appropriate response style based on message content"""
        content = content.lower()
        
        # Simple keyword-based style selection
        if any(word in content for word in ['meme', 'funny', 'lol', 'lmao']):
            return PostStyle.MEME
        elif any(word in content for word in ['explain', 'how', 'what', 'why']):
            return PostStyle.INFORMATIVE
        elif any(word in content for word in ['story', 'tell', 'happened']):
            return PostStyle.STORYTELLER
        elif any(word in content for word in ['analyze', 'data', 'stats']):
            return PostStyle.ANALYST
        else:
            return PostStyle.ENTERTAINER  # Default style

    async def auto_like_trending_posts(self):
        """Like trending posts based on settings"""
        try:
            if not self.like_settings["enabled"]:
                return

            # Reset hourly like counter
            current_time = time.time()
            if current_time - self.last_like_reset >= 3600:
                self.likes_count = 0
                self.last_like_reset = current_time

            if self.likes_count >= self.like_settings["max_likes_per_hour"]:
                return

            # Get trending posts
            trending_posts = await self.get_trending_posts(limit=10)
            
            for post in trending_posts:
                if self.likes_count >= self.like_settings["max_likes_per_hour"]:
                    break
                    
                if random.random() < self.like_settings["like_probability"]:
                    try:
                        await self._handle_rate_limit()
                        self.client.status_favourite(post['id'])
                        self.likes_count += 1
                        print(f"Liked post {post['id']} from @{post['author']}")
                    except Exception as e:
                        print(f"Error liking post: {str(e)}")

        except Exception as e:
            print(f"Error in auto-like process: {str(e)}")