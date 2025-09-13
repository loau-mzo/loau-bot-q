import json
import logging
from database import db

logger = logging.getLogger(__name__)

TABLES_TO_BACKUP = ['users', 'channels', 'admins', 'banned_users', 'bot_settings']

def get_backup():
    """Dumps all crucial tables into a structured JSON file."""
    backup_data = {}
    try:
        for table in TABLES_TO_BACKUP:
            db.cursor.execute(f"SELECT * FROM {table}")
            rows = db.cursor.fetchall()
            # Get column names
            column_names = [description[0] for description in db.cursor.description]
            backup_data[table] = [dict(zip(column_names, row)) for row in rows]

        backup_filepath = 'backup.json'
        with open(backup_filepath, 'w') as f:
            json.dump(backup_data, f, indent=4)

        logger.info(f"Database backup created successfully at {backup_filepath}")
        return True, backup_filepath
    except Exception as e:
        logger.error(f"Error creating backup: {e}")
        return False, str(e)

def restore_backup(backup_filepath: str):
    """Restores the database from a backup JSON file."""
    try:
        with open(backup_filepath, 'r') as f:
            backup_data = json.load(f)

        # Clear existing data and restore
        for table, data in backup_data.items():
            db.cursor.execute(f"DELETE FROM {table}")
            for row in data:
                columns = ', '.join(row.keys())
                placeholders = ', '.join(['?'] * len(row))
                values = list(row.values())
                db.cursor.execute(f"INSERT INTO {table} ({columns}) VALUES ({placeholders})", values)

        db.conn.commit()
        logger.info("Database restored successfully from backup.")
        return True, "Database restored successfully."
    except Exception as e:
        logger.error(f"Error restoring backup: {e}")
        db.conn.rollback()
        return False, str(e)
