import asyncio
from datetime import datetime
from typing import Dict, List, Set
from twitter_agent import TwitterAIAgent
class PostProcessor:
    def __init__(self):
        self.is_running = False
        self.platform = None
        self.config = None
        self.logs = []
        self.posts_processed = 0
        self.responses_sent = 0
        self.processed_posts = set()
        self.processed_mentions = set()

    async def start_processing(self):
        """Start the post processing loop"""
        self.is_running = True
        self.log_info("Starting post processor...")
        
        while self.is_running:
            try:
                if not self.platform or not self.config:
                    await asyncio.sleep(1)
                    continue

                await self.process_hashtags()
                await self.process_mentions()
                
                self._cleanup_processed_sets()
                
                await asyncio.sleep(self.config.monitoring.checkInterval)
                
            except Exception as e:
                self.log_error(f"Processing error: {str(e)}")
                await asyncio.sleep(5)

    async def process_hashtags(self):
        """Process posts for each hashtag"""
        for hashtag in self.config.monitoring.hashtags:
            try:
                if isinstance(self.platform, TwitterAIAgent):
                    # Use Twitter-specific search
                    tweets = self.platform.search_tweets(hashtag, max_results=5)
                    if tweets:
                        for tweet in tweets:
                            if tweet.id not in self.processed_posts:
                                self.log_info(
                                    f"Retrieved tweet from @{tweet.author_id}", 
                                    {"content": tweet.text}
                                )
                                
                                # Generate and post response
                                response = await self.platform.generate_entertainment_response(tweet.text)
                                reply_result = await self.platform.reply_to_tweet(tweet.id, response)
                                
                                if "error" not in reply_result:
                                    self.log_success(
                                        f"Responded to @{tweet.author_id}",
                                        {"response": response}
                                    )
                                    self.responses_sent += 1
                                
                                self.processed_posts.add(tweet.id)
                                self.posts_processed += 1
                else:
                    # Handle Mastodon posts
                    posts = await self.platform.search_hashtag(hashtag, limit=5)
                    
                    if posts and not "error" in posts[0]:
                        for post in posts:
                            if "error" not in post and post['id'] not in self.processed_posts:
                                await self.process_single_post(post)
                                self.processed_posts.add(post['id'])
                            
            except Exception as e:
                self.log_error(f"Error processing #{hashtag}: {str(e)}")

    async def process_single_post(self, post: Dict):
        """Process a single post"""
        try:
            self.log_info(
                f"Processing post from @{post['author']}", 
                {
                    "content": post['content'][:200] + "..." if len(post['content']) > 200 else post['content']
                }
            )
            
            # Generate and send response
            response = await self.platform.generate_entertainment_response(post['content'])
            reply = await self.platform.reply_to_post(post['id'], response)
            
            if "error" not in reply:
                self.log_success(
                    f"Responded to @{post['author']}", 
                    {
                        "response": response
                    }
                )
                self.responses_sent += 1
            
            self.posts_processed += 1
            
            # Add delay before processing next post
            delay = self.config.response.processingDelay if self.config else 5
            self.log_info(f"Waiting {delay} seconds before next response...")
            await asyncio.sleep(delay)
            
        except Exception as e:
            self.log_error(f"Error processing post: {str(e)}")

    async def process_mentions(self):
        """Process mentions"""
        try:
            mentions = await self.platform.get_mentions(limit=3)
            
            for mention in mentions:
                if "error" not in mention and mention['mention']['id'] not in self.processed_mentions:
                    self.log_info(
                        f"Received mention from @{mention['mention']['author']}", 
                        {
                            "content": mention['mention']['content'][:200]
                        }
                    )
                    
                    response = await self.platform.handle_mention(mention['mention'])
                    if "error" not in response:
                        self.log_success(
                            f"Responded to mention from @{mention['mention']['author']}", 
                            {
                                "response": response['response']
                            }
                        )
                        self.processed_mentions.add(mention['mention']['id'])
                    
        except Exception as e:
            self.log_error(f"Error processing mentions: {str(e)}")

    def _cleanup_processed_sets(self):
        """Clean up processed sets to prevent memory growth"""
        if len(self.processed_posts) > 1000:
            self.processed_posts = set(list(self.processed_posts)[-1000:])
        if len(self.processed_mentions) > 1000:
            self.processed_mentions = set(list(self.processed_mentions)[-1000:])

    def log_info(self, message: str, details: Dict = None):
        """Log info message"""
        self._add_log("info", message, details)

    def log_success(self, message: str, details: Dict = None):
        """Log success message"""
        self._add_log("success", message, details)

    def log_error(self, message: str, details: Dict = None):
        """Log error message"""
        self._add_log("error", message, details)

    def _add_log(self, log_type: str, message: str, details: Dict = None):
        """Add a log entry"""
        log_entry = {
            "timestamp": datetime.now().strftime("%H:%M:%S"),
            "type": log_type,
            "message": message,
            "details": details
        }
        print(f"[{log_entry['timestamp']}] {message}")  # Console debug
        self.logs.append(log_entry)
        
        if len(self.logs) > 100:
            self.logs = self.logs[-100:]

    def stop(self):
        """Stop the processor"""
        self.is_running = False
        self.log_info("Agent stopped")
        self.processed_posts.clear()
        self.processed_mentions.clear()