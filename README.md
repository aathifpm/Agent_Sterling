# Agent_Sterling 🤖

An intelligent social media bot that interacts with Twitter and Mastodon, providing AI-powered responses using Google's Gemini Pro.

## Features 🌟

### Multi-Platform Support
- **Twitter Integration**: Full Twitter API support
- **Mastodon Integration**: Federated social network support
- **Platform-Specific Handling**: Optimized for each platform's unique features

### Core Functionality
- **Account Monitoring**: Watch specific accounts for new posts
- **Mention Tracking**: Automatically respond to mentions
- **Hashtag Interaction**: Engage with trending topics and hashtags
- **AI-Powered Responses**: Generate contextual and entertaining replies
- **Smart Engagement**: Analyze post sentiment and context

### Technical Features
- **Rate Limiting**: Built-in handling of API rate limits
- **Error Recovery**: Robust error handling and automatic recovery
- **NLTK Integration**: Natural language processing for better understanding
- **Gemini Pro**: Advanced AI response generation

## Prerequisites 📋

- Python 3.8+
- Twitter API credentials (Elevated access)
- Mastodon account and API access
- Google Gemini API key

## Installation 🔧

1. Clone the repository:
```bash
git clone https://github.com/yourusername/Agent_Sterling.git
cd Agent_Sterling
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Create `.env` file with your credentials:
```env
TWITTER_API_KEY=your_api_key
TWITTER_API_SECRET=your_api_secret
TWITTER_ACCESS_TOKEN=your_access_token
TWITTER_ACCESS_TOKEN_SECRET=your_access_token_secret
TWITTER_BEARER_TOKEN=your_bearer_token
GEMINI_API_KEY=your_gemini_key
```

## Usage 🚀

### Watch Specific Account and Mentions

```python
python watch_twitter.py
```

This will:
- Monitor specified Twitter account(s) for new tweets
- Watch for mentions of your account
- Generate and post AI responses
- Handle rate limits and errors automatically

### Customize Monitoring

Edit `watch_twitter.py` to change:
```python
specific_account = "username"  # Account to watch
interval = 60  # Check interval in seconds
```

## Features in Detail 🔍

### Tweet Analysis
- Sentiment analysis
- Topic identification
- Context understanding
- Appropriate response generation

### Response Types
- Entertainment responses
- Research-based replies
- Smart engagement
- Context-aware threads

### Rate Limiting
- Twitter API limits respected
- Automatic cooldown periods
- Request tracking and management

## Error Handling 🛠️

The agent handles:
- Network errors
- API rate limits
- Authentication issues
- Invalid responses
- Connection timeouts

## Contributing 🤝

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License 📄

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments 👏

- Twitter API
- Google Gemini Pro
- Tweepy library
- FastAPI framework

## Contact 📧

Your Name - [@your_twitter](https://twitter.com/your_twitter)

