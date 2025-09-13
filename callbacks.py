from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler, CallbackQueryHandler, CommandHandler, MessageHandler, filters
from channel_manager import delete_channel as delete_channel_logic, get_channel_details, update_channel as update_channel_logic
from scheduler import schedule_channel_jobs
from admin_manager import get_admins, add_admin as add_admin_logic, remove_admin as remove_admin_logic
from ban_manager import get_banned_users, ban_user, unban_user
from ads_manager import view_ad, delete_ad, add_ad
from database import db
from admin import get_backup, start_broadcast_flow, broadcast_receive_message, cancel_broadcast, BROADCAST_WAIT_MESSAGE

# States
(EDIT_SCHEDULE, EDIT_SIGNATURE, EDIT_TOPIC) = range(10, 13)
(
    WAIT_ADMIN_ID,
    WAIT_REMOVE_ADMIN_ID,
    WAIT_APPROVE_USER_ID,
    WAIT_BAN_USER_ID,
    WAIT_UNBAN_USER_ID,
    WAIT_AD_TEXT
) = range(13, 19)

# Channel Management Callbacks
async def main_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data.split('_')
    action = data[0]
    channel_id = int(data[1])

    if action == "delete":
        keyboard = [[InlineKeyboardButton("Yes, delete it", callback_data=f"confirmdelete_{channel_id}")], [InlineKeyboardButton("No, cancel", callback_data=f"canceldelete_{channel_id}")]]
        await query.edit_message_text(text=f"Are you sure you want to delete channel {channel_id}?", reply_markup=InlineKeyboardMarkup(keyboard))
    elif action == "confirmdelete":
        success, message = delete_channel_logic(channel_id)
        if success:
            schedule_channel_jobs(context.application)
            await query.edit_message_text(text="Channel deleted and schedule updated.")
        else:
            await query.edit_message_text(text=message)
    elif action == "canceldelete":
        await query.edit_message_text(text="Deletion canceled.")
    elif action == "edit":
        context.user_data['editing_channel_id'] = channel_id
        channel_info = get_channel_details(channel_id)
        if channel_info:
            await query.edit_message_text(text=f"Editing Channel: {channel_info[2]}\n" f"Current schedule: {channel_info[3]}\n\n" f"Please reply with the new schedule.")
            return EDIT_SCHEDULE
        else:
            await query.edit_message_text(text="Error: Channel not found.")
            return ConversationHandler.END

# Edit Channel Conversation
async def receive_new_schedule(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['new_schedule'] = update.message.text
    channel_id = context.user_data['editing_channel_id']
    channel_info = get_channel_details(channel_id)
    await update.message.reply_text(f"Current signature: {channel_info[4]}\n\nPlease enter the new signature (or send /skip).")
    return EDIT_SIGNATURE
async def receive_new_signature(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['new_signature'] = update.message.text
    channel_id = context.user_data['editing_channel_id']
    channel_info = get_channel_details(channel_id)
    await update.message.reply_text(f"Current topic: {channel_info[5]}\n\nPlease enter the new topic.")
    return EDIT_TOPIC
async def skip_new_signature(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    channel_id = context.user_data['editing_channel_id']
    channel_info = get_channel_details(channel_id)
    context.user_data['new_signature'] = channel_info[4]
    await update.message.reply_text(f"Signature kept. Current topic: {channel_info[5]}\n\nPlease enter the new topic.")
    return EDIT_TOPIC
async def receive_new_topic_and_update(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    topic = update.message.text
    channel_id = context.user_data['editing_channel_id']
    update_channel_logic(channel_id=channel_id, schedule=context.user_data['new_schedule'], signature=context.user_data['new_signature'], topic=topic)
    schedule_channel_jobs(context.application)
    await update.message.reply_text("Channel updated successfully! The schedule has been reloaded.")
    context.user_data.clear()
    return ConversationHandler.END
async def cancel_edit(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("Edit process canceled.")
    context.user_data.clear()
    return ConversationHandler.END

# Admin Panel Callbacks
async def admin_panel_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    if data == 'admin_panel_main':
        keyboard = [[InlineKeyboardButton("إدارة المستخدمين (User Management)", callback_data='admin_panel_users')], [InlineKeyboardButton("إدارة المحتوى (Content Management)", callback_data='admin_panel_content')], [InlineKeyboardButton("إدارة النظام (System Management)", callback_data='admin_panel_system')]]
        await query.edit_message_text('لوحة تحكم المسؤول (Admin Panel):', reply_markup=InlineKeyboardMarkup(keyboard))
    elif data == 'admin_panel_users':
        keyboard = [[InlineKeyboardButton("Approve User", callback_data='users_approve'), InlineKeyboardButton("Ban User", callback_data='users_ban')], [InlineKeyboardButton("Unban User", callback_data='users_unban'), InlineKeyboardButton("View Banned", callback_data='users_view_banned')], [InlineKeyboardButton("⬅️ Back", callback_data='admin_panel_main')]]
        await query.edit_message_text('User Management:', reply_markup=InlineKeyboardMarkup(keyboard))
    elif data == 'admin_panel_content':
        keyboard = [[InlineKeyboardButton("Broadcast", callback_data='content_broadcast'), InlineKeyboardButton("Add Ad", callback_data='content_add_ad')], [InlineKeyboardButton("View Ad", callback_data='content_view_ad'), InlineKeyboardButton("Delete Ad", callback_data='content_delete_ad')], [InlineKeyboardButton("⬅️ Back", callback_data='admin_panel_main')]]
        await query.edit_message_text('Content Management:', reply_markup=InlineKeyboardMarkup(keyboard))
    elif data == 'admin_panel_system':
        keyboard = [[InlineKeyboardButton("Add Admin", callback_data='system_add_admin'), InlineKeyboardButton("Remove Admin", callback_data='system_remove_admin')], [InlineKeyboardButton("View Admins", callback_data='system_view_admins')], [InlineKeyboardButton("Get Backup", callback_data='system_backup'), InlineKeyboardButton("Restore Backup", callback_data='system_restore')], [InlineKeyboardButton("⬅️ Back", callback_data='admin_panel_main')]]
        await query.edit_message_text('System Management:', reply_markup=InlineKeyboardMarkup(keyboard))

# System Management
async def system_management_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    if data == 'system_view_admins':
        admins = get_admins()
        text = "Current Admins:\n" + "\n".join(f"- `{admin[0]}`" for admin in admins) if admins else "No admins found."
        await query.edit_message_text(text=text, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Back", callback_data='admin_panel_system')]]), parse_mode='Markdown')
    elif data == 'system_backup':
        await query.edit_message_text("Generating backup...")
        class MockUpdate:
            message = type("MockMessage", (), {"reply_text": query.edit_message_text, "chat": query.message.chat})()
            effective_chat = query.message.chat
        await get_backup(MockUpdate(), context)
        await query.message.reply_text("Backup process finished.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Back", callback_data='admin_panel_system')]]))

# User Management
async def user_management_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    if data == 'users_view_banned':
        banned_users = get_banned_users()
        text = "Banned Users:\n" + "\n".join(f"- ID: {u[0]}, User: {u[1]}, Date: {u[2]}" for u in banned_users) if banned_users else "No banned users found."
        await query.edit_message_text(text=text, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Back", callback_data='admin_panel_users')]]))

# Generic User ID Conversation
async def start_user_id_convo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    action = query.data.split('_')[1]
    context.user_data['action'] = action
    prompts = {'approve': "Please send the User ID to approve.", 'ban': "Please send the User ID to ban.", 'unban': "Please send the User ID to unban.", 'removeadmin': "Please send the User ID to demote."}
    await query.answer()
    await query.edit_message_text(f"{prompts.get(action, 'Please send a User ID.')}\nSend /cancel to abort.")
    states = {'approve': WAIT_APPROVE_USER_ID, 'ban': WAIT_BAN_USER_ID, 'unban': WAIT_UNBAN_USER_ID, 'removeadmin': WAIT_REMOVE_ADMIN_ID}
    context.user_data['current_state'] = states.get(action)
    return context.user_data['current_state']
async def receive_user_id_and_act(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    action = context.user_data.get('action')
    try:
        user_id = int(update.message.text)
        message = ""
        if action == 'approve': db.approve_user(user_id); message = f"User {user_id} approved."
        elif action == 'ban': _, message = ban_user(user_id)
        elif action == 'unban': _, message = unban_user(user_id)
        elif action == 'removeadmin': _, message = remove_admin_logic(user_id)
        await update.message.reply_text(message)
    except (ValueError):
        await update.message.reply_text("Invalid User ID.")
        return context.user_data['current_state']
    context.user_data.clear()
    back_button = 'admin_panel_users' if action != 'removeadmin' else 'admin_panel_system'
    await update.message.reply_text("Action complete.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Back", callback_data=back_button)]]))
    return ConversationHandler.END
async def cancel_convo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("Process canceled.")
    context.user_data.clear()
    return ConversationHandler.END

# Content Management
async def content_management_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    if data == 'content_view_ad':
        ad_text = view_ad()
        await query.edit_message_text(text=f"Current Ad:\n\n{ad_text}", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Back", callback_data='admin_panel_content')]]))
    elif data == 'content_delete_ad':
        _, message = delete_ad()
        await query.edit_message_text(text=message, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Back", callback_data='admin_panel_content')]]))

async def start_add_ad_convo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("Please send the text for the advertisement.\nSend /cancel to abort.")
    return WAIT_AD_TEXT
async def receive_ad_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    ad_text = update.message.text
    _, message = add_ad(ad_text)
    await update.message.reply_text(message)
    await update.message.reply_text("Action complete.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Back", callback_data='admin_panel_content')]]))
    return ConversationHandler.END

async def broadcast_start_from_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    keyboard = [[InlineKeyboardButton("To All Users", callback_data='broadcast_all')], [InlineKeyboardButton("To Approved Users", callback_data='broadcast_approved')], [InlineKeyboardButton("⬅️ Back", callback_data='admin_panel_content')]]
    await query.edit_message_text("Choose broadcast audience:", reply_markup=InlineKeyboardMarkup(keyboard))

# Registration
def register_callback_handlers(application):
    application.add_handler(CallbackQueryHandler(main_callback_handler, pattern="^(delete|confirmdelete|canceldelete)_"))
    application.add_handler(CallbackQueryHandler(admin_panel_callback_handler, pattern="^admin_panel_"))
    application.add_handler(CallbackQueryHandler(system_management_callback_handler, pattern="^system_(view_admins|backup|restore)$"))
    application.add_handler(CallbackQueryHandler(user_management_callback_handler, pattern="^users_view_banned$"))
    application.add_handler(CallbackQueryHandler(content_management_callback_handler, pattern="^content_(view_ad|delete_ad)$"))
    application.add_handler(CallbackQueryHandler(broadcast_start_from_panel, pattern="^content_broadcast$"))

    application.add_handler(ConversationHandler(
        entry_points=[CallbackQueryHandler(main_callback_handler, pattern="^edit_")],
        states={
            EDIT_SCHEDULE: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_new_schedule)],
            EDIT_SIGNATURE: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_new_signature), CommandHandler("skip", skip_new_signature)],
            EDIT_TOPIC: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_new_topic_and_update)],
        },
        fallbacks=[CommandHandler("cancel", cancel_edit)], per_message=False))

    application.add_handler(ConversationHandler(
        entry_points=[
            CallbackQueryHandler(start_user_id_convo, pattern="^users_(approve|ban|unban)$"),
            CallbackQueryHandler(start_user_id_convo, pattern="^system_add_admin$"),
            CallbackQueryHandler(start_user_id_convo, pattern="^system_remove_admin$")
        ],
        states={
            WAIT_APPROVE_USER_ID: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_user_id_and_act)],
            WAIT_BAN_USER_ID: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_user_id_and_act)],
            WAIT_UNBAN_USER_ID: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_user_id_and_act)],
            WAIT_ADMIN_ID: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_user_id_and_act)],
            WAIT_REMOVE_ADMIN_ID: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_user_id_and_act)],
        },
        fallbacks=[CommandHandler("cancel", cancel_convo)]))

    application.add_handler(ConversationHandler(
        entry_points=[CallbackQueryHandler(start_add_ad_convo, pattern="^content_add_ad$")],
        states={WAIT_AD_TEXT: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_ad_text)]},
        fallbacks=[CommandHandler("cancel", cancel_convo)]))

    async def start_broadcast_from_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        query = update.callback_query
        audience = 'all' if query.data == 'broadcast_all' else 'approved'
        return await start_broadcast_flow(update, context, audience)

    application.add_handler(ConversationHandler(
        entry_points=[CallbackQueryHandler(start_broadcast_from_callback, pattern="^broadcast_(all|approved)$")],
        states={BROADCAST_WAIT_MESSAGE: [MessageHandler(filters.ALL & ~filters.COMMAND, broadcast_receive_message)]},
        fallbacks=[CommandHandler("cancel", cancel_broadcast)]))
