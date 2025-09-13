import asyncio
import logging
from telegram import Bot
from database import db

logger = logging.getLogger(__name__)

# Conversation states
BROADCAST_WAIT_MESSAGE = 0

async def send_broadcast_message(bot: Bot, user_id: int, message):
    """Sends a single message to a user, handling potential errors."""
    try:
        if message.text:
            await bot.send_message(chat_id=user_id, text=message.text)
        elif message.photo:
            await bot.send_photo(chat_id=user_id, photo=message.photo[-1].file_id, caption=message.caption)
        elif message.video:
            await bot.send_video(chat_id=user_id, video=message.video.file_id, caption=message.caption)
        elif message.document:
            await bot.send_document(chat_id=user_id, document=message.document.file_id, caption=message.caption)
        # Add other message types as needed
        return True
    except Exception as e:
        logger.error(f"Failed to send message to {user_id}: {e}")
        return False

async def broadcast_logic(bot: Bot, users: list, message):
    """Handles the logic of sending a broadcast to a list of users."""
    success_count = 0
    failure_count = 0
    total_users = len(users)

    logger.info(f"Starting broadcast to {total_users} users.")

    for i, user in enumerate(users):
        user_id = user[0]
        if await send_broadcast_message(bot, user_id, message):
            success_count += 1
        else:
            failure_count += 1

        # Avoid rate limiting
        if (i + 1) % 20 == 0:
            logger.info(f"Broadcast progress: {i+1}/{total_users} users. Pausing for 1 second.")
            await asyncio.sleep(1)
        else:
            await asyncio.sleep(0.1)

    logger.info(f"Broadcast finished. Success: {success_count}, Failures: {failure_count}")
    return success_count, failure_count
