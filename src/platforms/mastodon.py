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
    def __init__(self, credentials):
        # Initialize Mastodon client
        self.client = Mastodon(
            client_id=credentials['client_id'],
            client_secret=credentials['client_secret'],
            access_token=credentials['access_token'],
            api_base_url=credentials['instance_url']
        )
        
        # Initialize Gemini model
        if 'gemini_api_key' not in credentials:
            raise ValueError("Gemini API key is required")
        genai.configure(api_key=credentials['gemini_api_key'])
        try:
            self.model = genai.GenerativeModel('gemini-1.5-flash-latest')
            self.chat = self.model.start_chat(history=[])
        except Exception as e:
            raise Exception(f"Failed to initialize Gemini model: {str(e)}")
        
        # Initialize settings
        self.hashtags = []
        self.check_interval = 60
        self.cooldown_period = 5
        self.processed_posts = set()
        self.processed_dms = set()
        self.last_post_time = time.time()
        self.post_count = 0
        self.last_daily_reset = time.time()
        
        # Initialize rate limiting attributes
        self.last_request_time = time.time()
        self.request_count = 0
        self.max_requests_per_minute = 30
        
        # Initialize auto-like attributes
        self.last_like_reset = time.time()
        self.likes_count = 0
        
        # Service status tracking
        self.services_status = {
            'auto_post': False,
            'dm': False,
            'auto_like': False,
            'hashtag': False
        }
        
        # Settings
        self.auto_post_settings = {
            'enabled': True,
            'interval': 1800,
            'max_daily_posts': 48
        }
        
        self.dm_settings = {
            'enabled': False,
            'auto_reply': True,
            'reply_interval': 300
        }
        
        self.like_settings = {
            'enabled': False,
            'max_likes_per_hour': 20,
            'like_probability': 0.7
        }
        
        self.post_config = {
            'max_length': 240,
            'style': 'entertainer',
            'use_emojis': True,
            'use_hashtags': True
        }
        
        # Initialize current style
        self.current_style = PostStyle.ENTERTAINER
        
        # Initialize DM context file path
        self.dm_context_file = 'dm_context.json'
        self.replied_dms = set()
        self._load_dm_context()
        
        # Initialize last auto post time
        self.last_auto_post_time = time.time()
        self.auto_post_interval = self.auto_post_settings['interval']
        
        self.processed_trending_topics = {}  # Track processed topics and their last content
        self.topic_cooldown = 3600  # 1 hour cooldown for same topic
        self.max_topic_history = 10  # Keep track of last 10 contents per topic
        self.last_trending_check = 0
        self.trending_check_interval = 300  # 5 minutes

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
        """Search for posts with specific hashtag"""
        try:
            print(f"🔍 Searching posts with #{hashtag}...")
            # Remove # if present
            hashtag = hashtag.strip('#')
            
            # Get posts with hashtag
            results = []
            posts = self.client.timeline_hashtag(hashtag)
            
            for post in posts[:limit]:
                try:
                    # Skip posts we've already processed
                    if post['id'] in self.processed_posts:
                        continue
                        
                    # Skip our own posts
                    if post['account']['id'] == self.client.account_verify_credentials()['id']:
                        continue
                        
                    # Extract post info
                    post_info = {
                        'id': post['id'],
                        'content': self._clean_html(post['content']),
                        'author': post['account']['username'],
                        'created_at': post['created_at'],
                        'raw_status': post  # Keep original status for reference
                    }
                    
                    results.append(post_info)
                    
                except Exception as e:
                    print(f"❌ Error processing hashtag result: {str(e)}")
                    continue
                    
            print(f"✅ Found {len(results)} new posts with #{hashtag}")
            return results
            
        except Exception as e:
            print(f"❌ Error searching hashtag #{hashtag}: {str(e)}")
            return []

    async def reply_to_post(self, post_id: str, content: str, visibility: str = "public") -> Dict:
        """Post a reply with rate limiting and visibility control"""
        try:
            await self._handle_rate_limit()
            status = self.client.status_post(
                content,
                in_reply_to_id=post_id,
                visibility=visibility
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
        """Get recent mentions with rate limiting and context"""
        try:
            await self._handle_rate_limit()
            mentions = self.client.notifications(
                types=['mention'],
                limit=limit
            )
            
            formatted_mentions = []
            for mention in mentions:
                try:
                    # Format the mention with context
                    mention_data = self._format_post(mention['status'])
                    mention_data['context'] = {
                        'in_reply_to_id': mention['status'].get('in_reply_to_id'),
                        'in_reply_to_account_id': mention['status'].get('in_reply_to_account_id'),
                        'visibility': mention['status'].get('visibility', 'public'),
                        'language': mention['status'].get('language', 'en'),
                        'created_at': mention['created_at']
                    }
                    
                    # Get conversation context if available
                    if mention_data['context']['in_reply_to_id']:
                        try:
                            context = self.client.status_context(mention_data['context']['in_reply_to_id'])
                            mention_data['context']['conversation'] = [
                                self._clean_html(s['content']) for s in context['ancestors'][-2:]
                            ]
                        except Exception as e:
                            print(f"Error getting conversation context: {str(e)}")
                            mention_data['context']['conversation'] = []
                    
                    formatted_mentions.append(mention_data)
                    
                except Exception as e:
                    print(f"Error formatting mention: {str(e)}")
                    continue
                    
            return formatted_mentions
        except Exception as e:
            print(f"Error getting mentions: {str(e)}")
            return []

    async def handle_mention(self, mention: Dict) -> Dict:
        """Handle mentions with context-aware responses"""
        try:
            # Extract mention data and context
            content = mention['content']
            context = mention.get('context', {})
            conversation = context.get('conversation', [])
            
            # Analyze the mention content and context
            is_question = any(word in content.lower() for word in ['?', 'how', 'what', 'why', 'when', 'where', 'who'])
            is_greeting = any(word in content.lower() for word in ['hi', 'hello', 'hey', 'greetings'])
            has_conversation = len(conversation) > 0
            
            # Build prompt based on analysis
            prompt_parts = [
                f"Create a response to this mention: \"{content}\"",
                "\nContext:",
                f"- Previous messages: {' -> '.join(conversation)}" if has_conversation else "- No previous context",
                f"- Type: {'Question' if is_question else 'Greeting' if is_greeting else 'Statement'}",
                "\nRequirements:",
                "1. Be engaging and natural",
                "2. Match the conversation tone",
                "3. If it's a question, provide a helpful answer",
                "4. If it's a greeting, respond warmly",
                "5. Reference previous context if relevant",
                "6. Keep it concise and clear",
                f"7. Stay under {self.post_config.get('max_length', 240)} characters",
                "8. Add 1-2 relevant emojis"
            ]
            
            prompt = "\n".join(prompt_parts)
            
            # Generate and format response
            response = await self.generate_entertainment_response(prompt)
            
            # Post the reply with appropriate visibility
            reply = await self.reply_to_post(
                mention['id'], 
                response,
                visibility=context.get('visibility', 'public')
            )
            
            return {
                "status": "success",
                "response": response,
                "reply": reply,
                "context_used": bool(conversation)
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
        """Main loop for scheduled auto-posting"""
        print("\n🚀 Starting auto-posting service...")
        
        try:
            # Make an immediate first post if enabled
            if self.auto_post_settings['enabled']:
                print("📝 Creating initial post...")
                post_result = await self.create_scheduled_post()
                if post_result:
                    self.last_post_time = time.time()
                    self.post_count += 1
                    print(f"✅ Initial post successful! Posts today: {self.post_count}/{self.auto_post_settings['max_daily_posts']}")
                else:
                    print("❌ Failed to create initial post, will retry in regular interval")

            # Continue with regular posting schedule
            while True:
                try:
                    current_time = time.time()
                    
                    # Reset daily post count at midnight
                    if self._should_reset_daily_count(current_time):
                        self.post_count = 0
                        self.last_daily_reset = current_time
                        print("🔄 Daily post count reset")
                    
                    # Handle auto-posting if enabled
                    if self.auto_post_settings['enabled']:
                        # Check if we can post (time interval and daily limit)
                        if (current_time - self.last_post_time >= self.auto_post_settings['interval'] and 
                            self.post_count < self.auto_post_settings['max_daily_posts']):
                            
                            print("📝 Creating scheduled post...")
                            post_result = await self.create_scheduled_post()
                            if post_result:
                                self.last_post_time = current_time
                                self.post_count += 1
                                print(f"✅ Post successful! Posts today: {self.post_count}/{self.auto_post_settings['max_daily_posts']}")
                            else:
                                print("❌ Failed to create post, will retry next interval")
                                await asyncio.sleep(300)  # Wait 5 minutes before retrying
                        
                        elif self.post_count >= self.auto_post_settings['max_daily_posts']:
                            print(" Daily post limit reached, waiting for reset")
                            await asyncio.sleep(self._time_until_next_reset())
                    
                    await asyncio.sleep(60)  # Check every minute
                    
                except asyncio.CancelledError:
                    print("🛑 Auto-posting service stopped")
                    break
                except Exception as e:
                    print(f"❌ Error in auto-posting loop: {str(e)}")
                    await asyncio.sleep(300)  # Wait 5 minutes on error
                    
        except Exception as e:
            print(f"❌ Error starting auto-posting service: {str(e)}")
            raise

    def _should_reset_daily_count(self, current_time):
        """Check if we should reset the daily post count"""
        current_day = time.strftime("%Y-%m-%d", time.localtime(current_time))
        last_reset_day = time.strftime("%Y-%m-%d", time.localtime(self.last_daily_reset))
        return current_day != last_reset_day

    def _time_until_next_reset(self):
        """Calculate seconds until next day reset (midnight)"""
        now = time.localtime()
        seconds_since_midnight = now.tm_hour * 3600 + now.tm_min * 60 + now.tm_sec
        return 86400 - seconds_since_midnight  # Seconds until midnight

    async def get_trending_topics(self, limit: int = 5) -> List[str]:
        """Get trending topics by analyzing recent public posts"""
        try:
            await self._handle_rate_limit()
            
            # Get trending tags directly from Mastodon API
            trending_tags = self.client.trending_tags()
            
            # Fallback to timeline analysis if trending tags API fails
            if not trending_tags:
                timeline = self.client.timeline_public(limit=30)
                hashtag_counts = {}
                for status in timeline:
                    tags = status.get('tags', [])
                    for tag in tags:
                        tag_name = tag['name'].lower()
                        hashtag_counts[tag_name] = hashtag_counts.get(tag_name, 0) + 1
                
                trending = sorted(hashtag_counts.items(), 
                                key=lambda x: x[1], 
                                reverse=True)[:limit]
                return [tag[0] for tag in trending]
            
            return [tag['name'] for tag in trending_tags[:limit]]
            
        except Exception as e:
            print(f"Error getting trending topics: {str(e)}")
            return []

    async def create_scheduled_post(self):
        """Create an engaging scheduled post with trending topics"""
        try:
            print("\n📊 Fetching trending topics...")
            # Get current trending topics
            trending_topics = await self.get_trending_topics(limit=3)
            
            if trending_topics:
                topics_str = ', '.join(trending_topics)
                print(f"📈 Found trending topics: {topics_str}")
                prompt = f"""
                Create an engaging social media post about these trending topics: {topics_str}
                
                Requirements:
                - Focus on the most interesting aspects
                - Add valuable insights or perspectives
                - Include 1-2 relevant hashtags from: {topics_str}
                - Use 1-2 appropriate emojis
                - Keep it under {self.post_config['max_length']} characters
                - Make it conversation-starting
                """
            else:
                # Fallback topics if no trending tags found
                print("⚠️ No trending topics found, using fallback topics...")
                topics = ['technology', 'digital culture', 'innovation', 
                         'future tech', 'AI', 'social media']
                selected_topics = random.sample(topics, 2)
                print(f"🎲 Selected topics: {', '.join(selected_topics)}")
                prompt = f"""
                Create an engaging social media post about one of these topics: 
                {', '.join(selected_topics)}
                
                Requirements:
                - Be informative and engaging
                - Add valuable insights
                - Include 1-2 relevant hashtags
                - Use 1-2 appropriate emojis
                - Keep it under {self.post_config['max_length']} characters
                - Make it conversation-starting
                """
            
            # Generate post content using selected style
            print("🤖 Generating post content...")
            response = await self.create_styled_post(prompt, self.current_style)
            
            # Post the content
            print("📤 Posting content...")
            await self._handle_rate_limit()
            status = self.client.status_post(
                response,
                visibility="public"
            )
            
            formatted_post = self._format_post(status)
            print(f"\n✅ Successfully posted: {response}")
            return formatted_post
            
        except Exception as e:
            print(f"❌ Error creating scheduled post: {str(e)}")
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

    async def start_services(self):
        """Start all automated services"""
        print("\n🚀 Starting all automated services...")
        
        try:
            # Create tasks for each service
            tasks = []
            
            # Auto-posting service
            if self.auto_post_settings['enabled']:
                tasks.append(asyncio.create_task(self.schedule_auto_posts()))
                self.services_status['auto_post'] = True
                print("📝 Auto-posting service enabled")
                self.log_info("Auto-posting service enabled")
            
            # DM service
            if self.dm_settings['enabled']:
                tasks.append(asyncio.create_task(self.handle_dm_service()))
                self.services_status['dm'] = True
                print("📨 DM service enabled")
                self.log_info("DM service enabled")
            
            # Auto-like service
            if self.like_settings['enabled']:
                tasks.append(asyncio.create_task(self.handle_auto_likes()))
                self.services_status['auto_like'] = True
                print("❤️ Auto-like service enabled")
                self.log_info("Auto-like service enabled")
            
            # Hashtag monitoring
            if self.hashtags:
                tasks.append(asyncio.create_task(self.monitor_hashtags()))
                self.services_status['hashtag'] = True
                print("🔍 Hashtag monitoring enabled")
                self.log_info("Hashtag monitoring enabled")
            
            # Wait for all tasks
            if tasks:
                await asyncio.gather(*tasks)
            else:
                print("⚠️ No services enabled")
                self.log_info("No services enabled")
            
        except Exception as e:
            error_msg = f"Error in services: {str(e)}"
            print(f"❌ {error_msg}")
            self.log_error(error_msg)
            raise

    def log_info(self, message):
        """Add info log entry"""
        timestamp = datetime.now().isoformat()
        log_entry = {
            "timestamp": timestamp,
            "type": "info",
            "message": message
        }
        if hasattr(self, 'processor') and self.processor:
            self.processor.logs.append(log_entry)
        print(f"ℹ️ {message}")

    def log_error(self, message):
        """Add error log entry"""
        timestamp = datetime.now().isoformat()
        log_entry = {
            "timestamp": timestamp,
            "type": "error",
            "message": message
        }
        if hasattr(self, 'processor') and self.processor:
            self.processor.logs.append(log_entry)
        print(f"❌ {message}")

    async def handle_dm_service(self):
        """Handle DM monitoring and responses"""
        print("\n📨 Starting DM service...")
        last_check_time = 0
        
        while True:
            try:
                if not self.dm_settings["enabled"] or not self.dm_settings["auto_reply"]:
                    await asyncio.sleep(60)
                    continue
                    
                current_time = time.time()
                if current_time - last_check_time >= self.dm_settings["reply_interval"]:
                    print("\n🔍 Checking for new DMs...")
                    await self.handle_direct_messages()
                    last_check_time = current_time
                    
                await asyncio.sleep(60)  # Check every minute
                
            except asyncio.CancelledError:
                print("🛑 DM service stopped")
                break
            except Exception as e:
                print(f"❌ Error in DM service: {str(e)}")
                await asyncio.sleep(300)  # Wait 5 minutes on error

    async def handle_auto_likes(self):
        """Handle auto-liking of posts"""
        print("\n❤️ Starting auto-like service...")
        last_like_time = 0
        hourly_likes = 0
        last_hour_reset = time.time()
        
        while True:
            try:
                if not self.like_settings["enabled"]:
                    await asyncio.sleep(60)
                    continue
                
                current_time = time.time()
                
                # Reset hourly counter
                if current_time - last_hour_reset >= 3600:
                    hourly_likes = 0
                    last_hour_reset = current_time
                    print("🔄 Hourly like count reset")
                
                # Check if we can like more posts
                if hourly_likes >= self.like_settings["max_likes_per_hour"]:
                    await asyncio.sleep(60)
                    continue
                
                # Get trending posts to like
                if current_time - last_like_time >= 300:  # Check every 5 minutes
                    print("\n🔍 Finding posts to like...")
                    trending_posts = await self.get_trending_posts(limit=10)
                    
                    for post in trending_posts:
                        if hourly_likes >= self.like_settings["max_likes_per_hour"]:
                            break
                            
                        if random.random() < self.like_settings["like_probability"]:
                            try:
                                await self._handle_rate_limit()
                                self.client.status_favourite(post['id'])
                                hourly_likes += 1
                                print(f"❤️ Liked post from @{post['author']}")
                            except Exception as e:
                                print(f"❌ Error liking post: {str(e)}")
                                continue
                    
                    last_like_time = current_time
                
                await asyncio.sleep(60)  # Check every minute
                
            except asyncio.CancelledError:
                print("🛑 Auto-like service stopped")
                break
            except Exception as e:
                print(f"❌ Error in auto-like service: {str(e)}")
                await asyncio.sleep(300)  # Wait 5 minutes on error

    async def monitor_hashtags(self):
        """Monitor hashtags and respond to posts"""
        print("\n🔍 Starting hashtag monitoring service...")
        processed_posts = set()  # Keep track of processed posts
        
        while True:
            try:
                if not self.hashtags:
                    await asyncio.sleep(60)
                    continue
                
                print("\n#️⃣ Checking hashtags:", ", ".join(self.hashtags))
                for hashtag in self.hashtags:
                    try:
                        # Get posts for hashtag
                        posts = await self.search_hashtag(hashtag)
                        
                        for post in posts:
                            try:
                                # Skip if already processed
                                if post['id'] in processed_posts:
                                    continue
                                
                                print(f"\n📝 Processing #{hashtag} post from @{post['author']}")
                                
                                # Process the post
                                result = await self.process_single_post(post)
                                if result and 'error' not in result:
                                    processed_posts.add(post['id'])
                                    print(f"✅ Successfully responded to post from @{post['author']}")
                                
                                # Respect cooldown period
                                await asyncio.sleep(self.cooldown_period)
                                
                            except Exception as e:
                                print(f"❌ Error processing post: {str(e)}")
                                continue
                        
                    except Exception as e:
                        print(f"❌ Error checking hashtag #{hashtag}: {str(e)}")
                        continue
                
                # Cleanup old processed posts (keep last 1000)
                if len(processed_posts) > 1000:
                    processed_posts = set(list(processed_posts)[-1000:])
                
                # Wait before next check
                await asyncio.sleep(self.check_interval)
                
            except asyncio.CancelledError:
                print("🛑 Hashtag monitoring service stopped")
                break
            except Exception as e:
                print(f"❌ Error in hashtag monitoring: {str(e)}")
                await asyncio.sleep(300)  # Wait 5 minutes on error

    def update_settings(self, settings_type, new_settings):
        """Update service settings"""
        try:
            if settings_type == 'auto_post':
                self.auto_post_settings.update(new_settings)
                print(f"✅ Updated auto-post settings: {new_settings}")
            elif settings_type == 'dm':
                self.dm_settings.update(new_settings)
                print(f"✅ Updated DM settings: {new_settings}")
            elif settings_type == 'like':
                self.like_settings.update(new_settings)
                print(f"✅ Updated auto-like settings: {new_settings}")
            elif settings_type == 'hashtags':
                self.hashtags = new_settings
                print(f"✅ Updated hashtags: {new_settings}")
            elif settings_type == 'post_style':
                self.post_config.update(new_settings)
                print(f"✅ Updated post style: {new_settings}")
            return True
        except Exception as e:
            print(f"❌ Error updating {settings_type} settings: {str(e)}")
            return False

    def get_service_status(self):
        """Get current status of all services"""
        return {
            'services': self.services_status,
            'settings': {
                'auto_post': self.auto_post_settings,
                'dm': self.dm_settings,
                'like': self.like_settings,
                'hashtags': self.hashtags,
                'post_style': self.post_config
            }
        }

    async def create_trending_content(self, topic: str, context: Dict = None) -> str:
        """Generate unique content for a trending topic"""
        try:
            base_prompt = f"""Create a unique and engaging post about the trending topic: #{topic}
            
            Context from previous posts about this topic:
            {self._get_topic_context(topic)}
            
            Additional context (if any):
            {context if context else 'No additional context'}
            
            Rules:
            1. Must be different from previous posts
            2. Include relevant hashtags
            3. Be engaging and informative
            4. Include 1-2 relevant emojis
            5. Maximum 2-3 sentences
            6. Add a unique perspective or angle
            7. If possible, relate to current events
            8. Use conversational tone
            """
            
            response = await self.generate_entertainment_response(base_prompt)
            
            # Store this content in topic history
            self._update_topic_history(topic, response)
            
            return response
            
        except Exception as e:
            print(f"Error generating trending content: {str(e)}")
            return None

    def _get_topic_context(self, topic: str) -> str:
        """Get context of previous posts about this topic"""
        if topic not in self.processed_trending_topics:
            return "No previous posts about this topic"
            
        previous_contents = self.processed_trending_topics[topic]['contents']
        if not previous_contents:
            return "No previous posts about this topic"
            
        return "Previous posts:\n" + "\n".join(
            f"- {content[:100]}..." for content in previous_contents[-3:]
        )

    def _update_topic_history(self, topic: str, content: str):
        """Update the history of content for a topic"""
        current_time = time.time()
        
        if topic not in self.processed_trending_topics:
            self.processed_trending_topics[topic] = {
                'last_used': current_time,
                'contents': [content]
            }
        else:
            self.processed_trending_topics[topic]['last_used'] = current_time
            self.processed_trending_topics[topic]['contents'].append(content)
            
            # Keep only the last N contents
            if len(self.processed_trending_topics[topic]['contents']) > self.max_topic_history:
                self.processed_trending_topics[topic]['contents'] = \
                    self.processed_trending_topics[topic]['contents'][-self.max_topic_history:]

    def _cleanup_old_topics(self):
        """Remove old topics from tracking"""
        current_time = time.time()
        topics_to_remove = []
        
        for topic, data in self.processed_trending_topics.items():
            if current_time - data['last_used'] > 86400:  # Remove after 24 hours
                topics_to_remove.append(topic)
                
        for topic in topics_to_remove:
            del self.processed_trending_topics[topic]

    async def get_trending_topics_with_context(self) -> List[Dict]:
        """Get trending topics with additional context"""
        try:
            current_time = time.time()
            
            # Check if we should update trending topics
            if current_time - self.last_trending_check < self.trending_check_interval:
                return []
                
            self.last_trending_check = current_time
            
            # Get trending tags
            trending = self.client.trending_tags()
            
            # Get context for each trending topic
            enriched_topics = []
            for tag in trending[:5]:  # Use top 5 trending tags
                # Skip if topic is in cooldown
                if tag['name'] in self.processed_trending_topics:
                    last_used = self.processed_trending_topics[tag['name']]['last_used']
                    if current_time - last_used < self.topic_cooldown:
                        continue
                
                # Get recent posts for context
                recent_posts = await self.search_hashtag(tag['name'], limit=5)
                
                # Extract key information from recent posts
                engagement_metrics = []
                peak_hours = set()
                sentiment_counts = {'positive': 0, 'neutral': 0, 'negative': 0}
                
                for post in recent_posts:
                    # Calculate engagement score
                    engagement = post.get('favourites_count', 0) + post.get('reblogs_count', 0)
                    engagement_metrics.append(engagement)
                    
                    # Track posting hours
                    post_hour = datetime.fromisoformat(post['created_at']).hour
                    peak_hours.add(post_hour)
                    
                    # Simple sentiment analysis based on emojis and keywords
                    content = post['content'].lower()
                    if any(word in content for word in ['❤️', '😊', 'love', 'great', 'awesome']):
                        sentiment_counts['positive'] += 1
                    elif any(word in content for word in ['😢', '😠', 'bad', 'hate', 'terrible']):
                        sentiment_counts['negative'] += 1
                    else:
                        sentiment_counts['neutral'] += 1
                
                # Calculate engagement statistics
                avg_engagement = sum(engagement_metrics) / len(engagement_metrics) if engagement_metrics else 0
                max_engagement = max(engagement_metrics) if engagement_metrics else 0
                
                # Determine dominant sentiment
                dominant_sentiment = max(sentiment_counts.items(), key=lambda x: x[1])[0]
                
                context = {
                    'recent_discussions': [post['content'] for post in recent_posts],
                    'engagement_level': avg_engagement,
                    'peak_engagement': max_engagement,
                    'active_hours': sorted(list(peak_hours)),
                    'sentiment': dominant_sentiment,
                    'engagement_trend': 'rising' if max_engagement > avg_engagement * 1.5 else 'stable',
                    'post_frequency': len(recent_posts),
                    'sentiment_distribution': sentiment_counts
                }
                
                enriched_topics.append({
                    'tag': tag['name'],
                    'context': context
                })
            
            # Cleanup old topics periodically
            self._cleanup_old_topics()
            
            return enriched_topics
            
        except Exception as e:
            print(f"Error getting trending topics: {str(e)}")
            return []

    async def create_trending_post_improved(self) -> Dict:
        """Create an improved trending post with context awareness"""
        try:
            # Get trending topics with context
            topics = await self.get_trending_topics_with_context()
            if not topics:
                return {"error": "No suitable trending topics found"}
            
            # Sort topics by engagement level
            topics.sort(key=lambda x: x['context']['engagement_level'], reverse=True)
            
            for topic in topics:
                try:
                    # Generate unique content for this topic
                    content = await self.create_trending_content(
                        topic['tag'],
                        topic['context']
                    )
                    
                    if content:
                        # Post the content
                        post = self.client.status_post(
                            content,
                            visibility="public"
                        )
                        
                        return self._format_post(post)
                        
                except Exception as e:
                    print(f"Error creating post for topic {topic['tag']}: {str(e)}")
                    continue
            
            return {"error": "Failed to create trending post"}
            
        except Exception as e:
            print(f"Error in improved trending post creation: {str(e)}")
            return {"error": str(e)}