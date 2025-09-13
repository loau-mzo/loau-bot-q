from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CommandHandler, ConversationHandler, MessageHandler, filters
from database import db
from ai import generate_content
from channel_manager import add_channel as add_channel_logic, get_user_channels
from scheduler import schedule_channel_jobs

# --- Conversation States ---
WAIT_TOPIC = 0
# Channel Conversation States
(WAIT_CHANNEL_NAME, WAIT_SCHEDULE, WAIT_SIGNATURE, WAIT_TOPIC_CHANNEL) = range(1, 5)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles the /start command."""
    user = update.effective_user
    # Assuming new users are not approved by default
    db.add_or_update_user(user_id=user.id, username=user.username, is_approved=False)
    await update.message.reply_text(
        "Welcome to ContentGenBot! I can help you generate content for your Telegram channels. "
        "Use /help to see the available commands."
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Displays a help message."""
    help_text = (
        "Here are the available commands:\n"
        "/start - Start the bot\n"
        "/help - Show this help message\n"
        "/generate - Generate content on a topic\n"
        "/check_subs - Check your subscription status"
        # More commands will be added here
    )
    await update.message.reply_text(help_text)

async def check_subs(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Checks if the user's subscription is active."""
    user_id = update.effective_user.id
    user_record = db.get_user(user_id)
    if user_record and user_record[2]:  # is_approved column
        await update.message.reply_text("Your subscription is active.")
    else:
        await update.message.reply_text(
            "Your subscription is not active. "
            "Please contact an admin for approval."
        )

# --- Generate Content Conversation ---
async def generate_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Starts the content generation conversation."""
    user_id = update.effective_user.id
    user_record = db.get_user(user_id)
    if not user_record or not user_record[2]: # Not approved
        await update.message.reply_text(
            "You need an active subscription to generate content. "
            "Please use /check_subs to see your status."
        )
        return ConversationHandler.END

    await update.message.reply_text("What topic would you like to generate content about?")
    return WAIT_TOPIC

async def receive_topic(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Receives the topic and generates content."""
    topic = update.message.text
    await update.message.reply_text(f"Generating content for '{topic}'... Please wait.")

    content = generate_content(topic)

    await update.message.reply_text(content)
    return ConversationHandler.END

async def cancel_generation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancels the content generation conversation."""
    await update.message.reply_text("Content generation canceled.")
    return ConversationHandler.END

# --- Add Channel Conversation ---
async def add_channel_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Starts the add channel conversation."""
    await update.message.reply_text("Please enter the channel username (e.g., @mychannel).")
    return WAIT_CHANNEL_NAME

async def receive_channel_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Receives the channel name and asks for the schedule."""
    channel_name = update.message.text
    if not channel_name.startswith('@'):
        await update.message.reply_text("Invalid format. The channel username must start with '@'. Please try again.")
        return WAIT_CHANNEL_NAME # Stay in the same state

    context.user_data['channel_name'] = channel_name
    await update.message.reply_text("Great. Now, please enter the posting schedule (e.g., 'daily at 14:30', 'every monday at 10:00').")
    return WAIT_SCHEDULE

async def receive_schedule(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Receives the schedule and asks for the signature."""
    context.user_data['schedule'] = update.message.text
    await update.message.reply_text("Got it. Now, enter a signature to be appended to each post (or send /skip).")
    return WAIT_SIGNATURE

async def receive_signature(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Receives the signature and asks for the topic."""
    context.user_data['signature'] = update.message.text
    await update.message.reply_text("Excellent. Finally, what is the general topic for the content in this channel?")
    return WAIT_TOPIC_CHANNEL

async def skip_signature(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Skips the signature and asks for the topic."""
    context.user_data['signature'] = ""
    await update.message.reply_text("No signature will be used. Finally, what is the general topic for the content in this channel?")
    return WAIT_TOPIC_CHANNEL

async def receive_channel_topic(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Receives the topic and saves the channel."""
    topic = update.message.text
    user_id = update.effective_user.id

    add_channel_logic(
        user_id=user_id,
        channel_name=context.user_data['channel_name'],
        schedule=context.user_data['schedule'],
        signature=context.user_data['signature'],
        topic=topic
    )

    # Reschedule jobs
    schedule_channel_jobs(context.application)

    await update.message.reply_text("Channel added successfully! The schedule is now active.")
    context.user_data.clear()
    return ConversationHandler.END

async def cancel_channel_add(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancels the add channel conversation."""
    await update.message.reply_text("Add channel process canceled.")
    context.user_data.clear()
    return ConversationHandler.END

async def my_channels(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Displays a list of the user's channels with edit and delete buttons."""
    user_id = update.effective_user.id
    channels = get_user_channels(user_id)

    if not channels:
        await update.message.reply_text("You haven't added any channels yet. Use /add_channel to add one.")
        return

    message_text = "Your Channels:\n\n"
    for channel in channels:
        channel_id, _, channel_name, schedule, _, _ = channel
        message_text += f"**{channel_name}** (ID: {channel_id})\n"
        message_text += f"Schedule: {schedule}\n"
        keyboard = [
            [
                InlineKeyboardButton("Edit", callback_data=f"edit_{channel_id}"),
                InlineKeyboardButton("Delete", callback_data=f"delete_{channel_id}"),
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        # Send a separate message for each channel to have its own keyboard
        await update.message.reply_text(f"Channel: {channel_name}\nSchedule: {schedule}", reply_markup=reply_markup)

def register_user_handlers(application):
    # Content Generation Conversation
    gen_conv_handler = ConversationHandler(
        entry_points=[CommandHandler("generate", generate_start)],
        states={
            WAIT_TOPIC: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_topic)],
        },
        fallbacks=[CommandHandler("cancel", cancel_generation)],
    )

    # Add Channel Conversation
    add_channel_conv_handler = ConversationHandler(
        entry_points=[CommandHandler("add_channel", add_channel_start)],
        states={
            WAIT_CHANNEL_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_channel_name)],
            WAIT_SCHEDULE: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_schedule)],
            WAIT_SIGNATURE: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_signature), CommandHandler("skip", skip_signature)],
            WAIT_TOPIC_CHANNEL: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_channel_topic)],
        },
        fallbacks=[CommandHandler("cancel", cancel_channel_add)],
    )

    application.add_handler(gen_conv_handler)
    application.add_handler(add_channel_conv_handler)

    # Regular commands
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("check_subs", check_subs))
    application.add_handler(CommandHandler("my_channels", my_channels))
