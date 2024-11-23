import asyncio
import tweepy
from twitter_agent import TwitterAIAgent
import time

async def watch_account(username: str, agent: TwitterAIAgent, interval: int = 60):
    """Watch a specific account for new tweets"""
    print(f"🔍 Watching @{username}'s tweets...")
    
    # Keep track of most recent tweet ID
    last_tweet_id = None
    
    while True:
        try:
            tweets = agent.get_user_tweets(username, max_results=5)
            if tweets:
                # Process only new tweets
                for tweet in reversed(tweets):  # Process older tweets first
                    if last_tweet_id is None or tweet.id > last_tweet_id:
                        print(f"\n📝 New tweet from @{username}:")
                        print(f"Tweet: {tweet.text}")
                        
                        # Generate and post response
                        response = await agent.generate_entertainment_response(tweet.text)
                        print(f"🤖 Generated response: {response}")
                        
                        reply_result = await agent.reply_to_tweet(tweet.id, response)
                        print(f"📤 Reply status: {reply_result}")
                        
                        last_tweet_id = tweet.id
                        
            await asyncio.sleep(interval)  # Wait before checking again
            
        except Exception as e:
            print(f"Error: {str(e)}")
            await asyncio.sleep(interval)

async def watch_mentions(agent: TwitterAIAgent, interval: int = 30):
    """Watch for mentions of your account"""
    print("👀 Watching for mentions...")
    
    # Get your user ID first
    me = agent.client.get_me()
    if not me:
        print("Error: Couldn't get user information")
        return
        
    my_id = me.data.id
    last_mention_id = None
    
    while True:
        try:
            # Get mentions
            mentions = agent.client.get_users_mentions(
                my_id,
                max_results=10,
                since_id=last_mention_id
            )
            
            if mentions.data:
                for mention in reversed(mentions.data):  # Process older mentions first
                    print(f"\n📨 New mention:")
                    print(f"From: @{mention.author_id}")
                    print(f"Tweet: {mention.text}")
                    
                    # Analyze and generate response
                    analysis = await agent.analyze_tweet(mention.text)
                    print(f"🔍 Analysis: {analysis}")
                    
                    response = await agent.generate_entertainment_response(mention.text)
                    print(f"🤖 Generated response: {response}")
                    
                    # Reply
                    reply_result = await agent.reply_to_tweet(mention.id, response)
                    print(f"📤 Reply status: {reply_result}")
                    
                    last_mention_id = mention.id
                    
            await asyncio.sleep(interval)  # Wait before checking again
            
        except Exception as e:
            print(f"Error: {str(e)}")
            await asyncio.sleep(interval)

async def main():
    agent = TwitterAIAgent()
    
    # Choose what to watch:
    
    # Option 1: Watch specific account
    specific_account = "Aathif_PM"  # Replace with account you want to watch
    watch_account_task = asyncio.create_task(watch_account(specific_account, agent))
    
    # Option 2: Watch mentions
    watch_mentions_task = asyncio.create_task(watch_mentions(agent))
    
    # Run both watchers concurrently
    await asyncio.gather(watch_account_task, watch_mentions_task)

if __name__ == "__main__":
    print("🚀 Starting Twitter AI Agent...")
    asyncio.run(main())