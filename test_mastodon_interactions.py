import asyncio
import os
from dotenv import load_dotenv
from src.platforms.mastodon import MastodonPlatform

async def test_mastodon_interactions():
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
        hashtag = "media"
        print(f"\nSearching posts with #{hashtag}...")
        hashtag_posts = await platform.search_hashtag(hashtag, limit=5)
        print(f"Found {len(hashtag_posts)} posts with #{hashtag}")
        
        for post in hashtag_posts[:2]:  # Show first 2 posts
            print(f"\nPost by @{post['author']}:")
            print(f"Content: {post['content']}")
            print(f"Keywords: {', '.join(post['keywords'])}")
            
            print("\nAI Generated Response:")
            print(post['ai_response'])
            
            # Add delay between interactions
            await asyncio.sleep(2)
            
            # Interact with the post
            print("\nInteracting with post...")
            interaction = await platform.interact_with_post(post['id'])
            
            if 'error' not in interaction:
                print("\nGenerated Response:")
                print(interaction['response'])
                
                print("\nReply Status:")
                print(f"Reply ID: {interaction['reply_result'].get('id')}")
            else:
                print(f"\nError in interaction: {interaction['error']}")

        # Test mention handling
        print("\nChecking recent mentions...")
        mentions = await platform.get_mentions(limit=1)
        
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

        print("\n✅ Mastodon interactions completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Error during Mastodon interactions: {str(e)}")

if __name__ == "__main__":
    asyncio.run(test_mastodon_interactions()) 