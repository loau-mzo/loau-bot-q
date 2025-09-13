import json
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

try:
    with open('config.json', 'r') as f:
        config = json.load(f)
except FileNotFoundError:
    logger.error("config.json not found. Please create one.")
    config = {}
except json.JSONDecodeError:
    logger.error("Error decoding config.json. Please check the file for syntax errors.")
    config = {}

BOT_TOKEN = config.get('BOT_TOKEN')
GROQ_API_KEY = config.get('GROQ_API_KEY')
ADMIN_ID = config.get('ADMIN_ID')
DB_NAME = config.get('DB_NAME', 'bot_database.db')

# Validate essential configuration
if not BOT_TOKEN or not ADMIN_ID:
    logger.critical("BOT_TOKEN and ADMIN_ID must be set in config.json")
    # In a real application, you might exit or handle this differently.
    # For this script, we'll proceed but the bot will likely fail to start.
    pass
