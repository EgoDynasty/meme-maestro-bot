# 🎭 Meme Maestro Bot

![Meme Maestro](https://img.shields.io/badge/Meme-Maestro-blueviolet?style=flat-square)  
A Telegram bot that collects and shares video memes with a touch of chaos and fun! 🚀

## 💡 Overview

Meme Maestro is a Telegram bot designed to curate and distribute video memes. It:

- 📹 **Collects memes**: Saves video memes when a message contains the keyword `save` (case-insensitive) or links from supported platforms like YouTube Shorts or Instagram Reels.
- ☁️ **Stores in Firebase**: Securely saves meme metadata in a Firebase Realtime Database.
- 😂 **Shares on demand**: Responds to the command `скука` (boredom) by sending a random meme from its collection.
- 🕒 **Deletion protection**: Waits 10 seconds before saving to allow users to delete mistaken submissions.

## ✨ Features

- **Smart filtering**: Uses regular expressions to detect supported domains and the `save` keyword.
- **Silent operation**: Processes memes without spamming the chat (except for `скука` requests).
- **Random meme delivery**: Brings joy with a single word: `скука`.
- **Firebase integration**: Stores meme data (chat ID, message ID, author) for reliable retrieval.
- **Log group support**: Copies messages to a private log group for validation, keeping the main chat clean.

## 🛠️ Technologies

- 🐍 **Python 3.8+**
- 🤖 **python-telegram-bot v20+**
- 🔥 **Firebase Realtime Database**
- 📜 **python-dotenv** for environment variables
- 🔍 **Regular expressions** for text filtering
- 🌐 **http.server** for a lightweight health check endpoint

## 📋 Prerequisites

- A **Telegram Bot Token** from [BotFather](https://t.me/BotFather).
- A **Firebase project** with Realtime Database and service account credentials.
- A **Telegram group for logs** where the bot has send and delete message permissions.
- Python 3.8+ installed on your system.

## 🚀 Setup

1. **Clone the repository**:
   ```bash
   git clone https://github.com/EgoDynasty/meme-maestro-bot.git
   cd meme-maestro
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
   Required packages:
   - `python-telegram-bot>=20.0`
   - `firebase-admin`
   - `python-dotenv`

3. **Set up environment variables**:
   Create a `.env` file in the project root:
   ```env
   TOKEN=your_telegram_bot_token
   FIREBASE_PROJECT_ID=your_firebase_project_id
   FIREBASE_PRIVATE_KEY_ID=your_private_key_id
   FIREBASE_PRIVATE_KEY=your_private_key
   FIREBASE_CLIENT_EMAIL=your_client_email
   FIREBASE_CLIENT_ID=your_client_id
   FIREBASE_DATABASE_URL=your_firebase_database_url
   FIREBASE_CLIENT_X509_CERT_URL=your_client_x509_cert_url
   PORT=10000
   ```

   - **Telegram Bot Token**:
     - Message `@BotFather` on Telegram, use `/newbot`, and follow the instructions to get your token.
   - **Firebase Credentials**:
     - Go to [Firebase Console](https://console.firebase.google.com/).
     - Create a project and enable Realtime Database.
     - Navigate to **Project Settings > Service Accounts**.
     - Generate a new private key (JSON) and extract the required fields for the `.env` file.
   - **PORT**: Optional, defaults to `10000` for the health check server.

4. **Configure the log group**:
   - Add the bot to your Telegram log group and grant it **send messages** and **delete messages** permissions.
   - Find the group ID by sending a message to the group and temporarily adding this to `handle_message`:
     ```python
     print(f"Chat ID: {update.message.chat_id}")
     ```
   - Update the `bot_chat_id` in `main.py`:
     ```python
     bot_chat_id = 'your log group ID'  # Replace with your log group ID
     ```

5. **Run the bot**:
   ```bash
   python memeBot.py
   ```

## 📖 Usage

- **Start the bot**:
  Send `/start` to get a welcome message with instructions.
- **Save a meme**:
  - Send a video with the caption `save` (case-insensitive).
  - Or send a link from supported domains (e.g., `https://www.youtube.com/shorts/...`).
  - The bot waits 10 seconds to allow deletion, then saves the meme to Firebase.
- **Get a random meme**:
  Send `скука` (boredom) in any chat, and the bot will forward a random meme from its collection with the author's username.

## 🐛 Troubleshooting

- **Bot doesn't save memes**:
  - Check `.env` for correct Firebase credentials and Telegram token.
  - Ensure the bot has read permissions in the main chat and send/delete permissions in the log group.
- **"Chat not found" error**:
  - Verify the `bot_chat_id` in `main.py` matches your log group ID.
- **"Message to copy not found"**:
  - Normal if the user deleted the message within 10 seconds (intended behavior).
- **Firebase errors**:
  - Confirm all Firebase `.env` variables are correct and the Realtime Database is enabled.

## 🤝 Contributing

Feel free to fork, submit PRs, or open issues! Let's make Meme Maestro the ultimate meme curator! 😎

## 📜 License

MIT License. See [LICENSE](LICENSE) for details.

## 🌟 Acknowledgments

- Inspired by the chaos of meme culture and the power of Telegram bots.
- Thanks to the `python-telegram-bot` and `firebase-admin` communities for awesome libraries!