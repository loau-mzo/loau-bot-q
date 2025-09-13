# ContentGenBot

ContentGenBot is a sophisticated Telegram bot for AI-powered content generation and scheduling. It allows users to connect their channels, generate content on various topics using the Groq API, and schedule posts automatically. The bot also features a comprehensive admin backend for user management, broadcasting, and system maintenance.

## Features

### User Features
- **/start**: Register with the bot.
- **/help**: Get a list of available commands.
- **/generate**: Generate AI content for a specific topic (requires admin approval).
- **/check_subs**: Check your subscription/approval status.
- **/add_channel**: Add a new Telegram channel to manage.
- **/my_channels**: View, edit, or delete your connected channels.

### Admin Features
- **/admin**: Access a fully interactive, button-based admin panel to manage the bot.

The admin panel includes the following sections:
- **User Management**: Approve, ban, unban, and view banned users.
- **Content Management**: Broadcast messages, and manage advertisements.
- **System Management**: Manage other admins and perform database backups and restores.

## Setup and Installation

1.  **Clone the repository:**
    ```bash
    git clone <repository_url>
    cd ContentGenBot
    ```

2.  **Install dependencies:**
    Make sure you have Python 3.10+ installed.
    ```bash
    pip install -r requirements.txt
    ```

3.  **Configure the bot:**
    -   Rename `config.json.example` to `config.json`.
    -   Open `config.json` and fill in the required values:
        -   `BOT_TOKEN`: Your Telegram Bot Token from BotFather.
        -   `GROQ_API_KEY`: Your API key from [Groq](https://console.groq.com/keys).
        -   `ADMIN_ID`: Your personal Telegram User ID. You can get this from a bot like `@userinfobot`.
        -   `DB_NAME`: (Optional) The name of the SQLite database file. Defaults to `bot_database.db`.

## Usage

1.  **Start the bot:**
    ```bash
    python main.py
    ```

2.  **Interact with the bot:**
    -   Open a chat with your bot on Telegram.
    -   Users can use commands like `/start` and `/generate`.
    -   As the admin, type `/admin` to open the interactive control panel.

## Note on User Approval
Admins can approve new users through the interactive admin panel: `/admin` -> `User Management` -> `Approve User`.
