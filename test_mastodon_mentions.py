import asyncio
import os
from dotenv import load_dotenv
from src.platforms.mastodon import MastodonPlatform

async def test_mastodon_mentions():
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

        print("\nChecking recent mentions...")
        mentions = await platform.get_mentions(limit=3)
        
        if mentions:
            for item in mentions:
                if "error" in item:
                    continue
                    
                mention = item['mention']
                response = item['response']
                
                print(f"\n=== New Mention ===")
                print(f"From: @{mention['author']}")
                print(f"Content: {mention['content']}")
                
                if response.get('status') == 'success':
                    print("\nGenerated Response:")
                    print(response['response'])
                    
                    print("\nReply Status:")
                    print(f"Reply ID: {response['reply'].get('id')}")
        else:
            print("No recent mentions found.")

        print("\n✅ Mention handling test completed!")
        
    except Exception as e:
        print(f"\n❌ Error during mention testing: {str(e)}")

if __name__ == "__main__":
    asyncio.run(test_mastodon_mentions()) 