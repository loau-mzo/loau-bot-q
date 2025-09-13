from functools import wraps
from telegram import Update
from telegram.ext import ContextTypes
from database import db
from config import ADMIN_ID

def is_admin(user_id: int) -> bool:
    """Check if a user is an admin."""
    # The main admin from config is always an admin
    if user_id == int(ADMIN_ID):
        return True
    # Check the database for other admins
    return db.is_admin(user_id)

def admin_only(func):
    """Decorator to restrict access to admins only."""
    @wraps(func)
    async def wrapped(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        user_id = update.effective_user.id
        if not is_admin(user_id):
            await update.message.reply_text("You are not authorized to use this command.")
            return
        return await func(update, context, *args, **kwargs)
    return wrapped
