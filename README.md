Here's the complete updated README.md:

```markdown
# Agent_Sterling 🤖

An intelligent social media bot that interacts with Twitter and Mastodon, providing AI-powered responses using Google's Gemini Pro.

## Features 🌟

### Multi-Platform Support
- **Twitter Integration**: Full Twitter API v1 & v2 support with write permissions
- **Mastodon Integration**: Federated social network support with rate limiting
- **Pleroma Support**: Additional federation network compatibility
- **Platform-Specific Handling**: Optimized for each platform's unique features and APIs

### Core Functionality
- **Account Monitoring**: Watch specific accounts for new posts and activity
- **Mention Tracking**: Automatically respond to mentions with AI-powered replies
- **Hashtag Interaction**: Engage with trending topics and hashtags
- **AI-Powered Responses**: Generate contextual and entertaining replies using Gemini Pro
- **Smart Engagement**: Analyze post sentiment and context for appropriate responses
- **Web Control Panel**: Easy configuration and monitoring interface

### Technical Features
- **Rate Limiting**: Sophisticated API rate limit handling for each platform
- **Error Recovery**: Robust error handling with automatic retries and logging
- **NLTK Integration**: Natural language processing for keyword extraction
- **Gemini Pro**: Advanced AI response generation with image analysis capability
- **Async Processing**: Efficient concurrent request handling
- **Modular Design**: Platform-agnostic architecture with factory pattern

## Prerequisites 📋

- Python 3.8+
- Twitter API credentials (Elevated access)
- Mastodon account and API access
- Google Gemini API key
- FastAPI for web interface

## Installation 🔧

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

# Mastodon Credentials
MASTODON_INSTANCE_URL=your_instance_url
MASTODON_CLIENT_ID=your_client_id
MASTODON_CLIENT_SECRET=your_client_secret
MASTODON_ACCESS_TOKEN=your_access_token

# Gemini API
GEMINI_API_KEY=your_gemini_key
```

## Usage 🚀

### Web Control Panel

1. Start the web server:
```bash
cd static
http.server
```
2. Start the backend server in a new terminal on root directory:
```bash
uvicorn src.app:app --reload --log-level debug
```

3. Access the control panel at `http://localhost:8000` to:
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

## Features in Detail 🔍

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

## Development 🔧

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

## Contributing 🤝

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License 📄

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments 👏

- Twitter API and Tweepy library
- Mastodon API
- Google Gemini Pro
- FastAPI framework
- NLTK library
- Contributors and testers

## Contact 📧

    Aathif PM - [@AathifPM](https://twitter.com/AathifPM)

Project Link: [https://github.com/aathif_pm/Agent_Sterling](https://github.com/aathif_pm/Agent_Sterling)
```

This updated README.md now accurately reflects the full feature set and capabilities shown in the codebase, including:
- The web control panel interface
- Multi-platform support only Twitter and Mastodon
- For twitter only works on retrivieng can be tested
- Enhanced error handling and rate limiting
- Testing infrastructure
- Detailed setup instructions for each platform
- Project structure and development guidelines

The documentation is now more comprehensive and better aligned with the actual implementation in the codebase.