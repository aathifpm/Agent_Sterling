import asyncio
import os
from dotenv import load_dotenv
from src.platforms.mastodon import MastodonPlatform

async def test_mastodon_connection():
    # Load environment variables
    load_dotenv()
    
    # Get credentials from .env
    credentials = {
        'instance_url': os.getenv('MASTODON_INSTANCE_URL'),
        'client_id': os.getenv('MASTODON_CLIENT_ID'),
        'client_secret': os.getenv('MASTODON_CLIENT_SECRET'),
        'access_token': os.getenv('MASTODON_ACCESS_TOKEN')
    }
    
    try:
        print("\nInitializing Mastodon client...")
        platform = MastodonPlatform(credentials)
        
        # Test post
        print("\nTesting post...")
        result = await platform.post_content("Hello from Agent Sterling! 🤖 #test")
        print(f"Post result: {result}")
        
        # Test mentions
        print("\nTesting mentions...")
        mentions = await platform.get_mentions()
        print(f"Recent mentions: {mentions[:2]}")
        
        print("\n✅ Mastodon tests completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Error during Mastodon testing: {str(e)}")

if __name__ == "__main__":
    asyncio.run(test_mastodon_connection())