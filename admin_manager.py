from database import db

def add_admin(user_id: int):
    """Promotes a user to admin."""
    if not db.get_user(user_id):
        return False, "User not found."
    if db.is_admin(user_id):
        return False, "User is already an admin."
    db.add_admin(user_id)
    return True, "User promoted to admin."

def remove_admin(user_id: int):
    """Demotes an admin."""
    if not db.is_admin(user_id):
        return False, "User is not an admin."
    db.remove_admin(user_id)
    return True, "User demoted from admin."

def get_admins():
    """Returns a list of all admins."""
    return db.get_admins()
