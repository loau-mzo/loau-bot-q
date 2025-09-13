import sqlite3
import logging
from config import DB_NAME

logger = logging.getLogger(__name__)

class Database:
    def __init__(self, db_name=DB_NAME):
        try:
            self.conn = sqlite3.connect(db_name, check_same_thread=False)
            self.cursor = self.conn.cursor()
            self.create_tables()
        except sqlite3.Error as e:
            logger.error(f"Database connection error: {e}")
            raise

    def create_tables(self):
        """Create database tables if they don't exist."""
        try:
            self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                is_approved BOOLEAN DEFAULT FALSE,
                is_banned BOOLEAN DEFAULT FALSE
            )''')

            self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS channels (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                channel_name TEXT NOT NULL,
                schedule TEXT,
                signature TEXT,
                topic TEXT,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )''')

            self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS bot_settings (
                key TEXT PRIMARY KEY,
                value TEXT
            )''')

            self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS admins (
                user_id INTEGER PRIMARY KEY
            )''')

            self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS banned_users (
                user_id INTEGER PRIMARY KEY,
                ban_date TEXT,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )''')

            self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS broadcast_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                message_content TEXT,
                sent_to TEXT,
                success_count INTEGER,
                failure_count INTEGER,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )''')
            self.conn.commit()
            logger.info("Database tables created or already exist.")
        except sqlite3.Error as e:
            logger.error(f"Error creating tables: {e}")
            self.conn.rollback()

    def add_or_update_user(self, user_id, username, is_approved=False):
        """Add a new user or update their username if they already exist."""
        try:
            self.cursor.execute('''
                INSERT INTO users (user_id, username, is_approved)
                VALUES (?, ?, ?)
                ON CONFLICT(user_id) DO UPDATE SET username=excluded.username
            ''', (user_id, username, is_approved))
            self.conn.commit()
            logger.info(f"User {user_id} ({username}) added or updated.")
        except sqlite3.Error as e:
            logger.error(f"Error adding or updating user {user_id}: {e}")
            self.conn.rollback()

    def get_user(self, user_id):
        """Get user details by user_id."""
        try:
            self.cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
            return self.cursor.fetchone()
        except sqlite3.Error as e:
            logger.error(f"Error fetching user {user_id}: {e}")
            return None

    def get_all_users(self):
        """Get all users from the database."""
        try:
            self.cursor.execute("SELECT user_id FROM users")
            return self.cursor.fetchall()
        except sqlite3.Error as e:
            logger.error(f"Error fetching all users: {e}")
            return []

    def get_approved_users(self):
        """Get all approved users from the database."""
        try:
            self.cursor.execute("SELECT user_id FROM users WHERE is_approved = TRUE")
            return self.cursor.fetchall()
        except sqlite3.Error as e:
            logger.error(f"Error fetching approved users: {e}")
            return []

    def approve_user(self, user_id):
        """Approve a user."""
        try:
            self.cursor.execute("UPDATE users SET is_approved = TRUE WHERE user_id = ?", (user_id,))
            self.conn.commit()
            logger.info(f"User {user_id} approved.")
        except sqlite3.Error as e:
            logger.error(f"Error approving user {user_id}: {e}")
            self.conn.rollback()

    def ban_user(self, user_id):
        """Ban a user."""
        try:
            # Add to banned_users table
            from datetime import datetime
            ban_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self.cursor.execute("INSERT OR IGNORE INTO banned_users (user_id, ban_date) VALUES (?, ?)", (user_id, ban_date))
            # Update users table
            self.cursor.execute("UPDATE users SET is_banned = TRUE WHERE user_id = ?", (user_id,))
            self.conn.commit()
            logger.info(f"User {user_id} has been banned.")
        except sqlite3.Error as e:
            logger.error(f"Error banning user {user_id}: {e}")
            self.conn.rollback()

    def unban_user(self, user_id):
        """Unban a user."""
        try:
            self.cursor.execute("DELETE FROM banned_users WHERE user_id = ?", (user_id,))
            self.cursor.execute("UPDATE users SET is_banned = FALSE WHERE user_id = ?", (user_id,))
            self.conn.commit()
            logger.info(f"User {user_id} has been unbanned.")
        except sqlite3.Error as e:
            logger.error(f"Error unbanning user {user_id}: {e}")
            self.conn.rollback()

    def is_user_banned(self, user_id):
        """Check if a user is banned."""
        try:
            self.cursor.execute("SELECT 1 FROM banned_users WHERE user_id = ?", (user_id,))
            return self.cursor.fetchone() is not None
        except sqlite3.Error as e:
            logger.error(f"Error checking ban status for user {user_id}: {e}")
            return False

    def get_banned_users(self):
        """Get all banned users."""
        try:
            self.cursor.execute("SELECT u.user_id, u.username, b.ban_date FROM users u JOIN banned_users b ON u.user_id = b.user_id")
            return self.cursor.fetchall()
        except sqlite3.Error as e:
            logger.error(f"Error fetching banned users: {e}")
            return []

    def add_admin(self, user_id):
        """Promote a user to admin."""
        try:
            self.cursor.execute("INSERT OR IGNORE INTO admins (user_id) VALUES (?)", (user_id,))
            self.conn.commit()
            logger.info(f"User {user_id} promoted to admin.")
        except sqlite3.Error as e:
            logger.error(f"Error adding admin {user_id}: {e}")
            self.conn.rollback()

    def remove_admin(self, user_id):
        """Demote an admin."""
        try:
            self.cursor.execute("DELETE FROM admins WHERE user_id = ?", (user_id,))
            self.conn.commit()
            logger.info(f"User {user_id} demoted from admin.")
        except sqlite3.Error as e:
            logger.error(f"Error removing admin {user_id}: {e}")
            self.conn.rollback()

    def is_admin(self, user_id):
        """Check if a user is an admin."""
        try:
            self.cursor.execute("SELECT 1 FROM admins WHERE user_id = ?", (user_id,))
            return self.cursor.fetchone() is not None
        except sqlite3.Error as e:
            logger.error(f"Error checking admin status for user {user_id}: {e}")
            return False

    def get_admins(self):
        """Get all admin users."""
        try:
            self.cursor.execute("SELECT user_id FROM admins")
            return self.cursor.fetchall()
        except sqlite3.Error as e:
            logger.error(f"Error fetching admins: {e}")
            return []

    def set_setting(self, key, value):
        """Set a value in the bot_settings table."""
        try:
            self.cursor.execute("INSERT OR REPLACE INTO bot_settings (key, value) VALUES (?, ?)", (key, value))
            self.conn.commit()
            logger.info(f"Setting '{key}' updated.")
        except sqlite3.Error as e:
            logger.error(f"Error setting '{key}': {e}")
            self.conn.rollback()

    def get_setting(self, key):
        """Get a value from the bot_settings table."""
        try:
            self.cursor.execute("SELECT value FROM bot_settings WHERE key = ?", (key,))
            result = self.cursor.fetchone()
            return result[0] if result else None
        except sqlite3.Error as e:
            logger.error(f"Error getting setting '{key}': {e}")
            return None

    def delete_setting(self, key):
        """Delete a key from the bot_settings table."""
        try:
            self.cursor.execute("DELETE FROM bot_settings WHERE key = ?", (key,))
            self.conn.commit()
            logger.info(f"Setting '{key}' deleted.")
        except sqlite3.Error as e:
            logger.error(f"Error deleting setting '{key}': {e}")
            self.conn.rollback()

    def add_channel(self, user_id, channel_name, schedule, signature, topic):
        """Add a new channel for a user."""
        try:
            self.cursor.execute('''
                INSERT INTO channels (user_id, channel_name, schedule, signature, topic)
                VALUES (?, ?, ?, ?, ?)
            ''', (user_id, channel_name, schedule, signature, topic))
            self.conn.commit()
            logger.info(f"Channel '{channel_name}' added for user {user_id}.")
        except sqlite3.Error as e:
            logger.error(f"Error adding channel for user {user_id}: {e}")
            self.conn.rollback()

    def get_user_channels(self, user_id):
        """Get all channels for a specific user."""
        try:
            self.cursor.execute("SELECT * FROM channels WHERE user_id = ?", (user_id,))
            return self.cursor.fetchall()
        except sqlite3.Error as e:
            logger.error(f"Error fetching channels for user {user_id}: {e}")
            return []

    def update_channel(self, channel_id, schedule, signature, topic):
        """Update a channel's settings."""
        try:
            self.cursor.execute('''
                UPDATE channels
                SET schedule = ?, signature = ?, topic = ?
                WHERE id = ?
            ''', (schedule, signature, topic, channel_id))
            self.conn.commit()
            logger.info(f"Channel {channel_id} updated.")
        except sqlite3.Error as e:
            logger.error(f"Error updating channel {channel_id}: {e}")
            self.conn.rollback()

    def delete_channel(self, channel_id):
        """Delete a channel."""
        try:
            self.cursor.execute("DELETE FROM channels WHERE id = ?", (channel_id,))
            self.conn.commit()
            logger.info(f"Channel {channel_id} deleted.")
        except sqlite3.Error as e:
            logger.error(f"Error deleting channel {channel_id}: {e}")
            self.conn.rollback()

    def get_all_channels(self):
        """Get all channels from the database for the scheduler."""
        try:
            self.cursor.execute("SELECT id, channel_name, schedule, topic, signature FROM channels")
            return self.cursor.fetchall()
        except sqlite3.Error as e:
            logger.error(f"Error fetching all channels: {e}")
            return []

    def log_broadcast_message(self, message_content, sent_to, success_count, failure_count):
        """Log a broadcast message summary."""
        try:
            self.cursor.execute('''
                INSERT INTO broadcast_messages (message_content, sent_to, success_count, failure_count)
                VALUES (?, ?, ?, ?)
            ''', (message_content, sent_to, success_count, failure_count))
            self.conn.commit()
            logger.info("Broadcast message logged.")
        except sqlite3.Error as e:
            logger.error(f"Error logging broadcast message: {e}")
            self.conn.rollback()

    def close(self):
        """Close the database connection."""
        if self.conn:
            self.conn.close()
            logger.info("Database connection closed.")

# Instantiate the database
db = Database()
