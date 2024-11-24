import asyncio
import os
from dotenv import load_dotenv
from src.platforms.mastodon import MastodonPlatform

async def test_entertainment_responses():
    # Load environment variables
    load_dotenv()
    
    credentials = {
        'instance_url': os.getenv('MASTODON_INSTANCE_URL'),
        'client_id': os.getenv('MASTODON_CLIENT_ID'),
        'client_secret': os.getenv('MASTODON_CLIENT_SECRET'),
        'access_token': os.getenv('MASTODON_ACCESS_TOKEN')
    }
    
    try:
        print("\nInitializing Mastodon client...")
        platform = MastodonPlatform(credentials)

        # Test hashtag interaction
        hashtag = "AI"
        print(f"\nSearching posts with #{hashtag}...")
        hashtag_posts = await platform.search_hashtag(hashtag, limit=5)
        print(f"Found {len(hashtag_posts)} posts with #{hashtag}")
        
        for post in hashtag_posts[:2]:  # Show first 2 posts
            print(f"\nPost by @{post['author']}:")
            print(f"Content: {post['content']}")
            
            # Generate multiple entertainment responses
            print("\nGenerating various entertainment responses:")
            for _ in range(3):  # Generate 3 different types of responses
                response = await platform.generate_entertainment_response(post['content'])
                print(f"\nResponse: {response}")

        print("\n✅ Entertainment response test completed!")
        
    except Exception as e:
        print(f"\n❌ Error during testing: {str(e)}")

if __name__ == "__main__":
    asyncio.run(test_entertainment_responses()) 