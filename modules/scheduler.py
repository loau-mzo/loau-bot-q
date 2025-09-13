import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from telegram.ext import Application
from database import db
from utils.ai import generate_content

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()

async def post_to_channel(application: Application, channel_id: int, topic: str, signature: str):
    """Generates content and posts it to a specific channel."""
    logger.info(f"Generating content for channel {channel_id} on topic: {topic}")
    content = generate_content(topic)

    if "Error:" in content:
        logger.error(f"Failed to generate content for channel {channel_id}: {content}")
        # Maybe send a notification to the admin
        return

    full_post = content
    if signature:
        full_post += f"\n\n{signature}"

    try:
        await application.bot.send_message(chat_id=channel_id, text=full_post)
        logger.info(f"Successfully posted to channel {channel_id}.")
    except Exception as e:
        logger.error(f"Failed to post to channel {channel_id}: {e}")

def parse_schedule(schedule_str: str) -> CronTrigger:
    """
    Parses a simple schedule string like 'daily at HH:MM' into a CronTrigger.
    Returns None if the format is unrecognized.
    """
    try:
        parts = schedule_str.lower().split()
        if len(parts) == 3 and parts[0] == 'daily' and parts[1] == 'at':
            time_parts = parts[2].split(':')
            hour = int(time_parts[0])
            minute = int(time_parts[1])
            return CronTrigger(hour=hour, minute=minute)
    except (ValueError, IndexError) as e:
        logger.warning(f"Could not parse schedule string '{schedule_str}': {e}")

    logger.warning(f"Unrecognized schedule format: '{schedule_str}'")
    return None

def schedule_channel_jobs(application: Application):
    """Clears existing jobs and schedules all channel posts from the database."""
    scheduler.remove_all_jobs()
    logger.info("Cleared all existing scheduled jobs.")

    all_channels = db.get_all_channels()

    for channel in all_channels:
        channel_db_id, channel_id_str, schedule_str, topic, signature = channel

        trigger = parse_schedule(schedule_str)
        if trigger:
            job_id = f"channel_post_{channel_db_id}"
            scheduler.add_job(
                post_to_channel,
                trigger=trigger,
                id=job_id,
                name=f"Post to {channel_id_str}",
                args=[application, channel_id_str, topic, signature],
                replace_existing=True
            )
            logger.info(f"Scheduled job '{job_id}' for channel {channel_id_str} with schedule: {schedule_str}")
        else:
            logger.warning(f"Could not schedule job for channel {channel_id_str} due to invalid schedule format.")

def setup_scheduler(application: Application):
    """Initializes and starts the scheduler."""
    if not scheduler.running:
        schedule_channel_jobs(application)
        scheduler.start()
        logger.info("Scheduler started.")
    else:
        logger.info("Scheduler already running. Rescheduling jobs.")
        schedule_channel_jobs(application)
