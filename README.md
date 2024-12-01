# 🤖 Agent Sterling: The Social Media Smooth Talker

Hey there, fellow humans! Meet Agent Sterling, your new AI bestie who's basically a social media butterfly with a PhD in witty responses. Powered by Google's Gemini Pro (because regular AI was too mainstream), this bot's here to slide into your Twitter and Mastodon DMs with style! 

## 🎭 What Makes This Bot The Life of The Party?

### Platform Hopping Skills
- **Twitter Game**: Smooth as butter (when it works 😅)
- **Mastodon Mastery**: Like Twitter, but with cooler dinosaur vibes
- **Pleroma Support**: Because three's company!
- **Platform-Specific Sweet Talk**: Different platforms, different pickup lines

### Core Superpowers 💪
- **Professional Stalking**: I mean... "Account Monitoring"
- **Mention Detective**: Never misses a name-drop (helicopter parent mode)
- **Hashtag Surfer**: Rides the trending waves like a pro
- **AI-Powered Charm**: Thanks to Gemini Pro's galaxy brain
- **Emotional Intelligence**: Reads the room better than your ex
- **Control Panel**: Because even AI needs a remote control

### Nerdy Stuff (For The Tech Geeks) 🤓
- **Rate Limiting**: Because nobody likes a spammer
- **Error Recovery**: Falls gracefully, gets up fabulously
- **NLTK Magic**: Natural Language Processing (fancy words for "understands your gibberish")
- **Gemini Pro Integration**: Like GPT but with Google's sass
- **Async Processing**: Multitasking like your mom during holidays
- **Modular Design**: More organized than your sock drawer

## 📋 What You'll Need (The Boring But Important Stuff)

- Python 3.8+
- Twitter API credentials (Elevated access)
- Mastodon account and API access
- Google Gemini API key
- FastAPI for web interface

## 🔧 Getting This Party Started

1. Clone the repository:
```bash
git clone https://github.com/aathif_pm/Agent_Sterling.git
cd Agent_Sterling
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Create `.env` file with your credentials:
```env
# Twitter Credentials
TWITTER_API_KEY=your_api_key
TWITTER_API_SECRET=your_api_secret
TWITTER_ACCESS_TOKEN=your_access_token
TWITTER_ACCESS_TOKEN_SECRET=your_access_token_secret
TWITTER_BEARER_TOKEN=your_bearer_token
(For Now twitter's api not needed as )

# Mastodon Credentials
MASTODON_INSTANCE_URL=your_instance_url
MASTODON_CLIENT_ID=your_client_id
MASTODON_CLIENT_SECRET=your_client_secret
MASTODON_ACCESS_TOKEN=your_access_token

# Gemini API
GEMINI_API_KEY=your_gemini_key
```

## 🎓 The "Getting Access" Saga

### Getting Your Hands on Gemini Pro's Power

1. Visit [Google AI Studio](https://makersuite.google.com/app/apikey)

2. Sign in with your Google account

3. Click on "Get API Key" in the top navigation

4. Either:
   - Create a new API key
   - Use an existing key from your projects

5. Add the API key to:
   - Your `.env` file:
     ```env
     GEMINI_API_KEY=your_gemini_key
     ```
   - Not required on web control panel's API configuration section

Note: Gemini Pro features include:
- Multimodal capabilities (text, images, audio, video)
- Context window of up to 2 million tokens
- Advanced reasoning and code analysis
- Support for multiple programming languages

For more details about Gemini Pro capabilities, visit [Google DeepMind's Gemini Pro page](https://deepmind.google/technologies/gemini/pro/).

### Mastodon Setup (The Social Network That Actually Likes Developers)

1. Log in to your Mastodon account at [mastodon.social](https://mastodon.social/)

2. Go to Settings > Development > New Application

3. Fill in the application details:
   - Application name: `Agent_Sterling` (or your preferred name)
   - Website: Your website (optional)
   - Redirect URI: Leave as default
   - Scopes (select all):
     - `read`
     - `write`
     - `follow`
     - `push`

4. Click "Submit" to create your application

5. You'll receive these credentials:
   - Client key (API key)
   - Client secret
   - Access token

6. Add these credentials to:
   - Your `.env` file:
     ```env
     MASTODON_INSTANCE_URL=https://mastodon.social
     MASTODON_CLIENT_ID=your_client_key
     MASTODON_CLIENT_SECRET=your_client_secret
     MASTODON_ACCESS_TOKEN=your_access_token
     ```
   - The web control panel's Mastodon configuration section

## 🚀 Time To Let It Rip!

### Starting The Engine

Start the Backend Server:
```bash
# From root directory
uvicorn src.app:app --reload --log-level debug
```

### Web Control Panel

#### Prerequisites
Before using Method, you'll need to install Node.js:

1. Visit [Node.js official website](https://nodejs.org/)
2. Download and install the LTS (Long Term Support) version
3. Verify installation by running:
```bash
node --version
npm --version
```

#### Method : Node.js HTTP Server
```bash
# Install http-server globally (one-time setup)
npm install -g http-server

# Navigate to static directory and start Frontend server
cd static
http-server
```

3. Access the control panel at `http://localhost:8080` to:
- Configure platform settings and credentials
- Set monitoring parameters and hashtags
- Customize response behavior and rate limits
- View real-time logs and metrics
- Start/stop the agent

### Command Line Usage

For Twitter monitoring:
```python
python watch_twitter.py
```

For Mastodon testing:
```python
python test_mastodon.py
```

### Platform Setup

#### Mastodon Setup
```python
python scripts/setup_mastodon.py
```
This will guide you through the Mastodon authentication process.

## ⚠️ Plot Twists and Drama

1. **Current Relationship Status**
   - Mastodon: In a committed relationship ✅
   - Twitter: "It's complicated" ❌

2. **The Double Life**
   - Your bot needs two identities (like Batman):
     * One for the fancy web panel
     * One for the mysterious .env file
   - Yes, it's redundant. No, we're not fixing it (yet) 😅

3. **Words of Wisdom**
   - Save before you start (like a video game)
   - Patience is virtue (wait for that confirmation)
   - THEN unleash the chaos (start the agent)

## 🎭 The Bot's Many Talents

### Content Analysis
- Sentiment analysis with confidence scoring
- Topic identification and research capabilities
- Context understanding with thread awareness
- Image analysis for media posts
- Entertainment response generation
- Thread generation for detailed responses

### Response Types
- Entertainment responses with emoji support
- Research-based analytical replies
- Smart engagement with context awareness
- Thread generation capabilities
- Image-aware responses
- Pop culture references and wordplay

### Rate Limiting
- Platform-specific rate limit handling
- Automatic cooldown periods
- Request tracking and management
- Configurable limits per platform
- Monthly and daily tweet limits

### Error Handling 🛠️
The agent handles:
- Network errors and timeouts
- API rate limits and cooldowns
- Authentication issues
- Invalid responses
- Connection timeouts
- Platform-specific errors

## 🔧 For The Brave Souls (Development)

### Testing
Run the test suite:
```bash
python -m pytest test_*.py
```

Available test modules:
- `test_agent.py`: Core agent functionality
- `test_mastodon.py`: Mastodon integration
- `test_entertainment_responses.py`: Response generation
- `test_integrated.py`: Full integration testing

### Project Structure
```
src/
├── agent/         # Core agent functionality
├── platforms/     # Platform-specific implementations
├── features/      # Feature modules
├── config/        # Configuration handlers
├── listener/      # Stream listeners
└── setup/         # Setup utilities
```

## 🤝 Wanna Join The Party?

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 Legal Stuff (Yawn)

This project is under the MIT License - because sharing is caring!

## 👏 Shoutout to the Real MVPs

- Twitter API and Tweepy library
- Mastodon API
- Google Gemini Pro
- FastAPI framework
- NLTK library
- Contributors and testers

## 📧 Hit Me Up!

    Aathif PM - [@AathifPM](https://twitter.com/AathifPM)

Project Link: [https://github.com/aathif_pm/Agent_Sterling](https://github.com/aathif_pm/Agent_Sterling)

Remember: This bot is like a social media influencer, but with actual intelligence! 🎉

*P.S. If this bot starts posting cryptocurrency advice or tries to sell you NFTs, please contact support immediately. That's not a feature, that's a bug!* 😅
```
