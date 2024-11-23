# Agent_Sterling 🤖

An intelligent Twitter bot that watches accounts and mentions, providing AI-powered responses using Gemini Pro.

## Features 🌟

- **Account Monitoring**: Watch specific Twitter accounts for new tweets
- **Mention Tracking**: Automatically respond to mentions of your account
- **AI-Powered Responses**: Generate contextual and entertaining replies using Google's Gemini Pro
- **Smart Engagement**: Analyze tweet sentiment and context before responding
- **Rate Limiting**: Built-in handling of Twitter API rate limits
- **Error Recovery**: Robust error handling and automatic recovery

## Prerequisites 📋

- Python 3.8+
- Twitter API credentials (Elevated access)
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

