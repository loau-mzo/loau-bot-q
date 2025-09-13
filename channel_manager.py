from database import db

def add_channel(user_id: int, channel_name: str, schedule: str, signature: str, topic: str):
    """Adds a channel for a user."""
    db.add_channel(user_id, channel_name, schedule, signature, topic)
    return True, "Channel added successfully."

def get_user_channels(user_id: int):
    """Gets all channels for a user."""
    return db.get_user_channels(user_id)

def get_channel_details(channel_id: int):
    """Gets details for a specific channel."""
    # This function might need a direct DB implementation if not already present
    try:
        db.cursor.execute("SELECT * FROM channels WHERE id = ?", (channel_id,))
        return db.cursor.fetchone()
    except Exception as e:
        return None

def update_channel(channel_id: int, schedule: str, signature: str, topic: str):
    """Updates a channel's settings."""
    db.update_channel(channel_id, schedule, signature, topic)
    return True, "Channel updated successfully."

def delete_channel(channel_id: int):
    """Deletes a channel."""
    db.delete_channel(channel_id)
    return True, "Channel deleted successfully."
