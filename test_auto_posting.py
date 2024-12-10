import asyncio
import os
from dotenv import load_dotenv
from src.platforms.mastodon import MastodonPlatform

async def test_auto_posting(duration_minutes=60):
    """
    Test auto-posting functionality for a specified duration
    duration_minutes: How long to run the test (default 60 minutes)
    """
    load_dotenv()
    
    credentials = {
        'instance_url': os.getenv('MASTODON_INSTANCE_URL'),
        'client_id': os.getenv('MASTODON_CLIENT_ID'),
        'client_secret': os.getenv('MASTODON_CLIENT_SECRET'),
        'access_token': os.getenv('MASTODON_ACCESS_TOKEN')
    }
    
    try:
        print("\n🚀 Initializing Mastodon auto-posting test...")
        platform = MastodonPlatform(credentials)
        
        # Create task for auto-posting
        auto_post_task = asyncio.create_task(platform.schedule_auto_posts())
        
        # Run for specified duration
        print(f"\n⏱️ Running test for {duration_minutes} minutes...")
        await asyncio.sleep(duration_minutes * 60)
        
        # Cancel the task
        auto_post_task.cancel()
        print("\n✅ Auto-posting test completed!")
        
    except Exception as e:
        print(f"\n❌ Error during auto-posting test: {str(e)}")
    finally:
        # Cleanup
        try:
            auto_post_task.cancel()
        except:
            pass

if __name__ == "__main__":
    # Run test for 60 minutes by default
    asyncio.run(test_auto_posting(60)) 