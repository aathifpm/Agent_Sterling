import os
from mastodon import Mastodon
from dotenv import load_dotenv

def setup_mastodon():
    """Interactive setup script for Mastodon credentials"""
    print("=== Mastodon Setup ===")
    
    instance_url = input("Enter Mastodon instance URL (e.g., https://mastodon.social): ").strip()
    email = input("Enter your Mastodon email: ").strip()
    password = input("Enter your Mastodon password: ").strip()
    
    try:
        # Create the application
        Mastodon.create_app(
            "Agent Sterling",
            api_base_url=instance_url,
            to_file="mastodon_credentials.secret"
        )
        
        # Create client instance
        mastodon = Mastodon(
            client_id="mastodon_credentials.secret",
            api_base_url=instance_url
        )
        
        # Log in and get access token
        mastodon.log_in(
            email,
            password,
            to_file="mastodon_user.secret"
        )
        
        # Read credentials
        with open("mastodon_credentials.secret") as f:
            client_id, client_secret = f.read().strip().split('\n')
        
        with open("mastodon_user.secret") as f:
            access_token = f.read().strip()
        
        # Create .env file
        env_content = f"""# Mastodon Credentials
MASTODON_INSTANCE_URL={instance_url}
MASTODON_CLIENT_ID={client_id}
MASTODON_CLIENT_SECRET={client_secret}
MASTODON_ACCESS_TOKEN={access_token}
"""
        
        # Write to .env file
        with open(".env", "a") as f:
            f.write("\n" + env_content)
        
        print("\n✅ Setup completed successfully!")
        print("Credentials have been added to your .env file")
        
        # Clean up secret files
        os.remove("mastodon_credentials.secret")
        os.remove("mastodon_user.secret")
        
    except Exception as e:
        print(f"\n❌ Error during setup: {str(e)}")

if __name__ == "__main__":
    setup_mastodon() 