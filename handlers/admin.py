import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CommandHandler, ConversationHandler, MessageHandler, filters
from utils.validators import admin_only
from modules.admin_manager import add_admin as add_admin_logic, remove_admin as remove_admin_logic, get_admins as get_admins_logic
from modules.ban_manager import ban_user as ban_user_logic, unban_user as unban_user_logic, get_banned_users as get_banned_users_logic
from modules.ads_manager import add_ad as add_ad_logic, view_ad as view_ad_logic, delete_ad as delete_ad_logic
from modules.broadcast_manager import broadcast_logic, BROADCAST_WAIT_MESSAGE
from modules.backup_manager import get_backup as get_backup_logic, restore_backup as restore_backup_logic
from database import db

@admin_only
async def add_admin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Adds a new admin."""
    try:
        user_id = int(context.args[0])
        success, message = add_admin_logic(user_id)
        await update.message.reply_text(message)
    except (IndexError, ValueError):
        await update.message.reply_text("Usage: /add_admin <user_id>")

@admin_only
async def remove_admin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Removes an admin."""
    try:
        user_id = int(context.args[0])
        success, message = remove_admin_logic(user_id)
        await update.message.reply_text(message)
    except (IndexError, ValueError):
        await update.message.reply_text("Usage: /remove_admin <user_id>")

@admin_only
async def view_admins(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Views all admins."""
    admins = get_admins_logic()
    if not admins:
        await update.message.reply_text("No admins found.")
        return

    admin_list = "Current Admins:\n"
    for admin in admins:
        admin_list += f"- {admin[0]}\n"
    await update.message.reply_text(admin_list)

@admin_only
async def ban_user(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Bans a user."""
    try:
        user_id = int(context.args[0])
        success, message = ban_user_logic(user_id)
        await update.message.reply_text(message)
    except (IndexError, ValueError):
        await update.message.reply_text("Usage: /ban_user <user_id>")

@admin_only
async def unban_user(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Unbans a user."""
    try:
        user_id = int(context.args[0])
        success, message = unban_user_logic(user_id)
        await update.message.reply_text(message)
    except (IndexError, ValueError):
        await update.message.reply_text("Usage: /unban_user <user_id>")

@admin_only
async def view_banned_users(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Views all banned users."""
    banned_users = get_banned_users_logic()
    if not banned_users:
        await update.message.reply_text("No banned users found.")
        return

    banned_list = "Banned Users:\n"
    for user in banned_users:
        banned_list += f"- ID: {user[0]}, Username: {user[1]}, Ban Date: {user[2]}\n"
    await update.message.reply_text(banned_list)

@admin_only
async def add_ad(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Sets the advertisement text."""
    ad_text = " ".join(context.args)
    if not ad_text:
        await update.message.reply_text("Usage: /add_ad <advertisement_text>")
        return
    success, message = add_ad_logic(ad_text)
    await update.message.reply_text(message)

@admin_only
async def view_ad(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Views the current advertisement."""
    ad_text = view_ad_logic()
    await update.message.reply_text(ad_text)

@admin_only
async def delete_ad(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Deletes the current advertisement."""
    success, message = delete_ad_logic()
    await update.message.reply_text(message)

# --- Broadcast Conversation ---

async def start_broadcast_flow(update: Update, context: ContextTypes.DEFAULT_TYPE, audience_type: str) -> int:
    """Sets up user_data and prompts for the broadcast message."""
    if audience_type == 'all':
        context.user_data['broadcast_list'] = db.get_all_users()
        context.user_data['broadcast_type'] = 'all'
    elif audience_type == 'approved':
        context.user_data['broadcast_list'] = db.get_approved_users()
        context.user_data['broadcast_type'] = 'approved'
    else:
        # This case should ideally not be reached if called correctly
        await update.message.reply_text("Invalid broadcast audience.")
        return ConversationHandler.END

    prompt_message = (
        "Please send the message you want to broadcast. "
        "This can be text, an image, a video, or a document.\n\n"
        "Send /cancel to abort."
    )

    # If called from a callback, edit the message. If from a command, reply.
    if update.callback_query:
        await update.callback_query.edit_message_text(prompt_message)
    else:
        await update.message.reply_text(prompt_message)

    return BROADCAST_WAIT_MESSAGE

@admin_only
async def broadcast_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Starts the broadcast conversation from a command."""
    command = update.message.text.split()[0]
    audience = 'all' if command == '/broadcast_all' else 'approved'
    return await start_broadcast_flow(update, context, audience)

async def broadcast_receive_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Receives the message to broadcast and starts the process."""
    message_to_broadcast = update.message
    users_to_broadcast = context.user_data.get('broadcast_list', [])
    broadcast_type = context.user_data.get('broadcast_type', 'unknown')

    if not users_to_broadcast:
        await update.message.reply_text("No users to broadcast to. Aborting.")
        return ConversationHandler.END

    await update.message.reply_text(f"Starting broadcast to {len(users_to_broadcast)} users. This may take a while.")

    success_count, failure_count = await broadcast_logic(context.bot, users_to_broadcast, message_to_broadcast)

    # Log the broadcast
    message_summary = message_to_broadcast.text or message_to_broadcast.caption or f"Media message ({message_to_broadcast.effective_attachment.mime_type})"
    db.log_broadcast_message(message_summary[:200], broadcast_type, success_count, failure_count)

    await update.message.reply_text(
        f"Broadcast finished.\n"
        f"Successfully sent to: {success_count} users.\n"
        f"Failed to send to: {failure_count} users."
    )
    context.user_data.clear()
    return ConversationHandler.END

async def cancel_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancels the broadcast conversation."""
    await update.message.reply_text("Broadcast canceled.")
    context.user_data.clear()
    return ConversationHandler.END

# --- Backup and Restore ---

@admin_only
async def get_backup(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Creates a backup and sends it to the admin."""
    await update.message.reply_text("Creating backup...")
    success, filepath_or_error = get_backup_logic()
    if success:
        await context.bot.send_document(
            chat_id=update.effective_chat.id,
            document=open(filepath_or_error, 'rb'),
            caption="Here is the database backup."
        )
        os.remove(filepath_or_error) # Clean up the file after sending
    else:
        await update.message.reply_text(f"Backup failed: {filepath_or_error}")

# Restore Conversation States
WAIT_BACKUP_FILE, WAIT_CONFIRMATION = range(2)

@admin_only
async def restore_backup_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Starts the restore conversation."""
    await update.message.reply_text(
        "Please upload the `backup.json` file to restore the database.\n"
        "Send /cancel to abort."
    )
    return WAIT_BACKUP_FILE

async def restore_receive_file(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Receives the backup file and asks for confirmation."""
    document = update.message.document
    if not document or document.file_name != 'backup.json':
        await update.message.reply_text("Please upload a valid `backup.json` file.")
        return WAIT_BACKUP_FILE

    backup_file = await document.get_file()
    filepath = f"restore_{update.effective_user.id}.json"
    await backup_file.download_to_drive(filepath)
    context.user_data['restore_filepath'] = filepath

    await update.message.reply_text(
        "Backup file received. "
        "**WARNING:** Restoring will overwrite all current data. This cannot be undone.\n\n"
        "Please type `CONFIRM` to proceed."
    )
    return WAIT_CONFIRMATION

async def restore_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Performs the restore after confirmation."""
    if update.message.text.strip() != 'CONFIRM':
        await update.message.reply_text("Invalid confirmation. Restore aborted.")
        if os.path.exists(context.user_data.get('restore_filepath', '')):
            os.remove(context.user_data['restore_filepath'])
        context.user_data.clear()
        return ConversationHandler.END

    filepath = context.user_data.get('restore_filepath')
    await update.message.reply_text("Restoring database... This may take a moment.")

    success, message = restore_backup_logic(filepath)
    await update.message.reply_text(message)

    if os.path.exists(filepath):
        os.remove(filepath)
    context.user_data.clear()
    return ConversationHandler.END

async def cancel_restore(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancels the restore conversation."""
    if os.path.exists(context.user_data.get('restore_filepath', '')):
        os.remove(context.user_data['restore_filepath'])
    context.user_data.clear()
    await update.message.reply_text("Restore process canceled.")
    return ConversationHandler.END

@admin_only
async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Displays the main admin panel."""
    keyboard = [
        [InlineKeyboardButton("إدارة المستخدمين (User Management)", callback_data='admin_panel_users')],
        [InlineKeyboardButton("إدارة المحتوى (Content Management)", callback_data='admin_panel_content')],
        [InlineKeyboardButton("إدارة النظام (System Management)", callback_data='admin_panel_system')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text('لوحة تحكم المسؤول (Admin Panel):', reply_markup=reply_markup)

@admin_only
async def approve_user(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Approves a user to use the bot's features."""
    try:
        user_id = int(context.args[0])
        if db.get_user(user_id):
            db.approve_user(user_id)
            await update.message.reply_text(f"User {user_id} has been approved.")
        else:
            await update.message.reply_text(f"User {user_id} not found.")
    except (IndexError, ValueError):
        await update.message.reply_text("Usage: /approve_user <user_id>")

def register_admin_handlers(application):
    application.add_handler(CommandHandler("admin", admin_panel))
    # Add conversation handler for broadcasting
    broadcast_conv_handler = ConversationHandler(
        entry_points=[
            CommandHandler("broadcast_all", broadcast_start),
            CommandHandler("broadcast_approved", broadcast_start)
        ],
        states={
            BROADCAST_WAIT_MESSAGE: [MessageHandler(filters.ALL & ~filters.COMMAND, broadcast_receive_message)],
        },
        fallbacks=[CommandHandler("cancel", cancel_broadcast)],
    )

    # Add conversation handler for restoring
    restore_conv_handler = ConversationHandler(
        entry_points=[CommandHandler("restore_backup", restore_backup_start)],
        states={
            WAIT_BACKUP_FILE: [MessageHandler(filters.Document.ALL, restore_receive_file)],
            WAIT_CONFIRMATION: [MessageHandler(filters.TEXT & ~filters.COMMAND, restore_confirm)],
        },
        fallbacks=[CommandHandler("cancel", cancel_restore)],
    )

    application.add_handler(broadcast_conv_handler)
    application.add_handler(restore_conv_handler)
    application.add_handler(CommandHandler("get_backup", get_backup))
    application.add_handler(CommandHandler("approve_user", approve_user))

    # Regular admin commands
    application.add_handler(CommandHandler("add_admin", add_admin))
    application.add_handler(CommandHandler("remove_admin", remove_admin))
    application.add_handler(CommandHandler("view_admins", view_admins))
    application.add_handler(CommandHandler("ban_user", ban_user))
    application.add_handler(CommandHandler("unban_user", unban_user))
    application.add_handler(CommandHandler("view_banned", view_banned_users))
    application.add_handler(CommandHandler("add_ad", add_ad))
    application.add_handler(CommandHandler("view_ad", view_ad))
    application.add_handler(CommandHandler("delete_ad", delete_ad))
