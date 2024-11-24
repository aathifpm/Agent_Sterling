from mastodon import Mastodon
import os
from dotenv import load_dotenv

load_dotenv()

def setup_mastodon_app():
    """
    First-time setup script for Mastodon application
    """
    instance_url = input("Enter your Mastodon instance URL (e.g., https://mastodon.social): ")
    email = input("Enter your Mastodon email: ")
    password = input("Enter your Mastodon password: ")
    
    # Create the application
    Mastodon.create_app(
        'YourAIBotName',
        api_base_url=instance_url,
        to_file='mastodon_client_secrets.txt'
    )
    
    # Create Mastodon instance
    mastodon = Mastodon(client_id='mastodon_client_secrets.txt')
    
    # Log in and get access token
    mastodon.log_in(
        email,
        password,
        to_file='mastodon_user_secrets.txt'
    )
    
    print("\nSetup completed! Add these values to your .env file:")
    with open('mastodon_client_secrets.txt', 'r') as f:
        client_id, client_secret = f.read().strip().split('\n')
    
    with open('mastodon_user_secrets.txt', 'r') as f:
        access_token = f.read().strip()
    
    print(f"""
MASTODON_INSTANCE_URL={instance_url}
MASTODON_CLIENT_ID={client_id}
MASTODON_CLIENT_SECRET={client_secret}
MASTODON_ACCESS_TOKEN={access_token}
    """)

if __name__ == "__main__":
    setup_mastodon_app() 