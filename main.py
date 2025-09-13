import logging
import logging
from telegram.ext import Application
from config import BOT_TOKEN
from handlers.user import register_user_handlers
from handlers.admin import register_admin_handlers
from handlers.callbacks import register_callback_handlers
from modules.scheduler import setup_scheduler

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

def main() -> None:
    """Start the bot."""
    application = Application.builder().token(BOT_TOKEN).build()

    # Register handlers
    register_user_handlers(application)
    register_admin_handlers(application)
    register_callback_handlers(application)

    # Set up and start the scheduler
    setup_scheduler(application)

    # Run the bot until the user presses Ctrl-C
    application.run_polling()

if __name__ == '__main__':
    main()
