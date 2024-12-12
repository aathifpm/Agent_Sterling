import asyncio
from datetime import datetime
from typing import Dict, List, Set

class PostProcessor:
    def __init__(self):
        self.is_running = False
        self.platform = None
        self.config = None
        self.logs = []
        self.sent_logs = set()  # Track logs that have been sent to UI
        self.posts_processed = 0
        self.responses_sent = 0
        self.processed_posts = set()
        self.processed_mentions = set()

    def stop(self):
        """Stop the processor and all platform services"""
        try:
            self.is_running = False
            if self.platform:
                # Update service status
                self.platform.services_status = {
                    'auto_post': False,
                    'dm': False,
                    'auto_like': False,
                    'hashtag': False
                }
            self.log_info("Agent stopped successfully")
        except Exception as e:
            self.log_error(f"Error stopping agent: {str(e)}")
            raise

    def update_config(self, config):
        """Update configuration and platform settings"""
        self.config = config
        if self.platform:
            # Set processor reference
            self.platform.processor = self
            
            # Update platform settings
            self.platform.update_settings('hashtags', config.monitoring.hashtags)
            self.platform.update_settings('auto_post', {
                'enabled': config.auto_post_settings.enabled,
                'interval': config.auto_post_settings.interval,
                'max_daily_posts': config.auto_post_settings.max_daily_posts
            })
            self.platform.update_settings('dm', config.dm_settings)
            self.platform.update_settings('like', config.like_settings)
            self.platform.update_settings('post_style', {
                'max_length': config.response.maxLength,
                'style': config.response.type,
                'use_emojis': config.response.useEmojis
            })

    async def start_processing(self):
        """Start the main processing loop"""
        self.is_running = True
        print("\n🚀 Starting Agent Sterling...")
        
        try:
            # Configure platform settings
            self.update_config(self.config)
            
            # Start all services
            await self.platform.start_services()
            
        except Exception as e:
            print(f"❌ Fatal error in processing: {str(e)}")
            self.is_running = False
            raise
        finally:
            self.is_running = False
            print("\n👋 Agent Sterling stopped")

    def get_status(self):
        """Get current status of the agent"""
        if not self.platform:
            return {
                "status": "stopped",
                "posts_processed": 0,
                "responses_sent": 0,
                "services": {},
                "settings": {}
            }
            
        platform_status = self.platform.get_service_status()
        
        # Get only new logs that haven't been sent to UI
        new_logs = []
        for log in self.logs:
            log_key = f"{log['timestamp']}:{log['message']}"
            if log_key not in self.sent_logs:
                new_logs.append(log)
                self.sent_logs.add(log_key)
        
        return {
            "status": "running" if self.is_running else "stopped",
            "posts_processed": self.posts_processed,
            "responses_sent": self.responses_sent,
            "services": platform_status['services'],
            "settings": platform_status['settings'],
            "logs": new_logs  # Send only new logs
        }

    def log_info(self, message):
        """Add info log entry"""
        self.logs.append({
            "timestamp": datetime.now().isoformat(),
            "type": "info",
            "message": message
        })

    def log_error(self, message):
        """Add error log entry"""
        self.logs.append({
            "timestamp": datetime.now().isoformat(),
            "type": "error",
            "message": message
        })