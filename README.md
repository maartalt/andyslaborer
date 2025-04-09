# Twitch Bot for Chenchen53

A custom Twitch bot built for [chenchen53](https://twitch.tv/chenchen53) that integrates Twitch chat functionality with Riot Games API to track game status and enhance stream interaction.

## Features

### Game Status Tracking
- Automatically detects when an account enters or leaves a League of Legends game
- Announces game starts in chat (Will later be replaced with gamble setup)
- Provides real-time game status updates through commands

### Chat Commands

#### Game Status Commands
- `!gamestatus` - Check if account is currently in a game
- `!retrievegamestatus` - Forced retrieve - Detailed game status check with Riot ID verification (For now using it to debug)

## Technical Details

### Built With
- Python 3.x
- TwitchIO - For Twitch chat integration
- Riot Games API - For game status tracking
- SQLite - For token storage
- AsyncIO - For asynchronous operations

### Requirements
- Twitch Developer Account
- Riot Games API Key
- Python 3.x
- Required Python packages (see requirements.txt)

## Setup

1. Clone the repository
2. Create a `.env` file with the following variables (I left 3 in bot.py because im lazy):
```env
CLIENT_ID=your_twitch_client_id
CLIENT_SECRET=your_twitch_client_secret
BOT_ID=your_bot_id
OWNER_ID=your_owner_id
RIOT_API_KEY=your_riot_api_key
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Run the bot:
```bash
python main.py
```

## Contributing

This bot is specifically designed for chenchen53's Twitch channel. However, if you find bugs or have suggestions for improvements, feel free to open an issue.

## License

[MIT License](LICENSE)

## Acknowledgments

- Thanks to chenchen53 for the opportunity to create this bot
- TwitchIO developers for the excellent Python library
- Riot Games for their API

---

*Note: This bot is maintained and operated by maartun_ for chenchen53's Twitch channel.*
