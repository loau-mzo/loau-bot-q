from database import db

def ban_user(user_id: int):
    """Bans a user."""
    if not db.get_user(user_id):
        return False, "User not found."
    if db.is_user_banned(user_id):
        return False, "User is already banned."
    db.ban_user(user_id)
    return True, "User has been banned."

def unban_user(user_id: int):
    """Unbans a user."""
    if not db.is_user_banned(user_id):
        return False, "User is not banned."
    db.unban_user(user_id)
    return True, "User has been unbanned."

def get_banned_users():
    """Returns a list of all banned users."""
    return db.get_banned_users()
