"""
Database manager for the spaceweather app
"""
import os
import sqlite3
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Database file path
DB_PATH = "data/spaceweather.db"

def ensure_db_dir():
    """Ensure the data directory exists"""
    os.makedirs("data", exist_ok=True)

def get_db_connection():
    """Get a connection to the SQLite database"""
    ensure_db_dir()
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # This enables column access by name
    return conn

def init_db():
    """Initialize the database with the required tables"""
    conn = get_db_connection()
    cursor = conn.cursor()

    # Create tables
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS dates (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date TEXT UNIQUE NOT NULL,
        url TEXT,
        error TEXT,
        last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        synced BOOLEAN DEFAULT 0
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS events (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date_id INTEGER NOT NULL,
        category TEXT NOT NULL,
        tone TEXT,
        event_date TEXT,
        predicted_arrival TEXT,
        detail TEXT,
        image_url TEXT,
        is_significant BOOLEAN DEFAULT 0,
        synced BOOLEAN DEFAULT 0,
        FOREIGN KEY (date_id) REFERENCES dates (id)
    )
    ''')

    # Create settings table for app configuration
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS settings (
        key TEXT PRIMARY KEY,
        value TEXT,
        description TEXT,
        last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')

    # Create indexes for faster queries
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_dates_date ON dates (date)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_events_date_id ON events (date_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_events_category ON events (category)')

    # Initialize default settings if they don't exist
    cursor.execute("SELECT value FROM settings WHERE key = 'default_days_to_show'")
    if not cursor.fetchone():
        cursor.execute(
            "INSERT INTO settings (key, value, description) VALUES (?, ?, ?)",
            ("default_days_to_show", "14", "Default number of days to show in the timeline")
        )

    conn.commit()
    conn.close()
    logger.info("Database initialized")

def save_data_to_db(data):
    """
    Save data to the SQLite database

    Args:
        data (dict): Data to save

    Returns:
        int: ID of the date record
    """
    if not data or "date" not in data:
        logger.error("Invalid data provided to save_data_to_db")
        return None

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # Insert or update the date record
        date_str = data.get("date")
        url = data.get("url")
        error = data.get("error")

        # Check if the date already exists
        cursor.execute("SELECT id FROM dates WHERE date = ?", (date_str,))
        date_record = cursor.fetchone()

        if date_record:
            # Update existing record
            date_id = date_record["id"]
            cursor.execute(
                "UPDATE dates SET url = ?, error = ?, last_updated = CURRENT_TIMESTAMP, synced = 0 WHERE id = ?",
                (url, error, date_id)
            )
            # Delete existing events for this date
            cursor.execute("DELETE FROM events WHERE date_id = ?", (date_id,))
        else:
            # Insert new record
            cursor.execute(
                "INSERT INTO dates (date, url, error) VALUES (?, ?, ?)",
                (date_str, url, error)
            )
            date_id = cursor.lastrowid

        # Insert events
        events = data.get("events", {})
        for category in ["cme", "sunspot", "flares", "coronal_holes"]:
            category_events = events.get(category, [])
            for event in category_events:
                tone = event.get("tone")
                event_date = event.get("date")
                predicted_arrival = event.get("predicted_arrival")
                detail = event.get("detail")
                image_url = event.get("image_url")
                is_significant = 1 if tone and tone.lower() == "significant" else 0

                cursor.execute(
                    """
                    INSERT INTO events
                    (date_id, category, tone, event_date, predicted_arrival, detail, image_url, is_significant)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (date_id, category, tone, event_date, predicted_arrival, detail, image_url, is_significant)
                )

        conn.commit()
        logger.info(f"Data for {date_str} saved to database")
        return date_id

    except Exception as e:
        conn.rollback()
        logger.error(f"Error saving data to database: {e}")
        return None

    finally:
        conn.close()

def load_data_from_db(date_str):
    """
    Load data from the SQLite database for a specific date

    Args:
        date_str (str): Date in format YYYY-MM-DD

    Returns:
        dict: Data for the specified date
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # Get the date record
        cursor.execute("SELECT * FROM dates WHERE date = ?", (date_str,))
        date_record = cursor.fetchone()

        if not date_record:
            logger.info(f"No data found in database for {date_str}")
            return None

        # Get all events for this date
        cursor.execute(
            "SELECT * FROM events WHERE date_id = ? ORDER BY category, is_significant DESC",
            (date_record["id"],)
        )
        events = cursor.fetchall()

        # Convert to the expected format
        result = {
            "date": date_record["date"],
            "url": date_record["url"],
            "events": {
                "cme": [],
                "sunspot": [],
                "flares": [],
                "coronal_holes": []
            }
        }

        if date_record["error"]:
            result["error"] = date_record["error"]

        # Group events by category
        for event in events:
            category = event["category"]
            event_data = {
                "tone": event["tone"],
                "date": event["event_date"],
                "predicted_arrival": event["predicted_arrival"],
                "detail": event["detail"],
                "image_url": event["image_url"]
            }
            result["events"][category].append(event_data)

        logger.info(f"Data for {date_str} loaded from database")
        return result

    except Exception as e:
        logger.error(f"Error loading data from database: {e}")
        return None

    finally:
        conn.close()

def get_all_data_from_db():
    """
    Get all data from the SQLite database

    Returns:
        list: List of all data
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # Get all date records
        cursor.execute("SELECT * FROM dates ORDER BY date DESC")
        date_records = cursor.fetchall()

        all_data = []

        for date_record in date_records:
            date_id = date_record["id"]

            # Get all events for this date
            cursor.execute(
                "SELECT * FROM events WHERE date_id = ? ORDER BY category, is_significant DESC",
                (date_id,)
            )
            events = cursor.fetchall()

            # Convert to the expected format
            result = {
                "date": date_record["date"],
                "url": date_record["url"],
                "events": {
                    "cme": [],
                    "sunspot": [],
                    "flares": [],
                    "coronal_holes": []
                }
            }

            if date_record["error"]:
                result["error"] = date_record["error"]

            # Group events by category
            for event in events:
                category = event["category"]
                event_data = {
                    "tone": event["tone"],
                    "date": event["event_date"],
                    "predicted_arrival": event["predicted_arrival"],
                    "detail": event["detail"],
                    "image_url": event["image_url"]
                }
                result["events"][category].append(event_data)

            all_data.append(result)

        logger.info(f"Retrieved {len(all_data)} records from database")
        return all_data

    except Exception as e:
        logger.error(f"Error getting all data from database: {e}")
        return []

    finally:
        conn.close()

def import_json_to_db():
    """
    Import all JSON files to the SQLite database

    Returns:
        int: Number of files imported
    """
    import os
    from utils import get_all_data

    # Get all data from JSON files
    all_data = get_all_data()

    count = 0
    for data in all_data:
        if save_data_to_db(data):
            count += 1

    logger.info(f"Imported {count} JSON files to database")
    return count

def mark_as_synced(date_id):
    """
    Mark a date record and its events as synced

    Args:
        date_id (int): ID of the date record
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("UPDATE dates SET synced = 1 WHERE id = ?", (date_id,))
        cursor.execute("UPDATE events SET synced = 1 WHERE date_id = ?", (date_id,))
        conn.commit()
        logger.info(f"Date ID {date_id} marked as synced")

    except Exception as e:
        conn.rollback()
        logger.error(f"Error marking date as synced: {e}")

    finally:
        conn.close()

def get_unsynced_data():
    """
    Get all unsynced data from the SQLite database

    Returns:
        list: List of unsynced data
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # Get all unsynced date records
        cursor.execute("SELECT * FROM dates WHERE synced = 0 ORDER BY date")
        date_records = cursor.fetchall()

        unsynced_data = []

        for date_record in date_records:
            date_id = date_record["id"]

            # Get all events for this date
            cursor.execute(
                "SELECT * FROM events WHERE date_id = ? ORDER BY category, is_significant DESC",
                (date_id,)
            )
            events = cursor.fetchall()

            # Convert to the expected format
            result = {
                "id": date_id,
                "date": date_record["date"],
                "url": date_record["url"],
                "events": {
                    "cme": [],
                    "sunspot": [],
                    "flares": [],
                    "coronal_holes": []
                }
            }

            if date_record["error"]:
                result["error"] = date_record["error"]

            # Group events by category
            for event in events:
                category = event["category"]
                event_data = {
                    "tone": event["tone"],
                    "date": event["event_date"],
                    "predicted_arrival": event["predicted_arrival"],
                    "detail": event["detail"],
                    "image_url": event["image_url"]
                }
                result["events"][category].append(event_data)

            unsynced_data.append(result)

        logger.info(f"Retrieved {len(unsynced_data)} unsynced records from database")
        return unsynced_data

    except Exception as e:
        logger.error(f"Error getting unsynced data from database: {e}")
        return []

    finally:
        conn.close()

def save_setting(key, value, description=None, sync_to_supabase=True):
    """
    Save a setting to the database

    Args:
        key (str): Setting key
        value (str): Setting value
        description (str, optional): Setting description
        sync_to_supabase (bool, optional): Whether to sync the setting to Supabase. Defaults to True.

    Returns:
        bool: True if successful, False otherwise
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # Check if the setting already exists
        cursor.execute("SELECT value FROM settings WHERE key = ?", (key,))
        if cursor.fetchone():
            # Update existing setting
            if description:
                cursor.execute(
                    "UPDATE settings SET value = ?, description = ?, last_updated = CURRENT_TIMESTAMP WHERE key = ?",
                    (value, description, key)
                )
            else:
                cursor.execute(
                    "UPDATE settings SET value = ?, last_updated = CURRENT_TIMESTAMP WHERE key = ?",
                    (value, key)
                )
        else:
            # Insert new setting
            cursor.execute(
                "INSERT INTO settings (key, value, description) VALUES (?, ?, ?)",
                (key, value, description)
            )

        conn.commit()
        logger.info(f"Setting {key} saved with value {value}")

        # Sync to Supabase if requested
        if sync_to_supabase:
            try:
                from supabase_sync import get_supabase_client
                supabase = get_supabase_client()
                if supabase:
                    supabase.sync_setting(key, value, description)
            except Exception as e:
                logger.error(f"Error syncing setting {key} to Supabase: {e}")

        return True

    except Exception as e:
        conn.rollback()
        logger.error(f"Error saving setting {key}: {e}")
        return False

    finally:
        conn.close()

def get_setting(key, default=None):
    """
    Get a setting from the database

    Args:
        key (str): Setting key
        default: Default value to return if the setting doesn't exist

    Returns:
        str: Setting value or default if not found
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("SELECT value FROM settings WHERE key = ?", (key,))
        result = cursor.fetchone()

        if result:
            return result["value"]
        else:
            return default

    except Exception as e:
        logger.error(f"Error getting setting {key}: {e}")
        return default

    finally:
        conn.close()

def get_all_settings():
    """
    Get all settings from the database

    Returns:
        dict: Dictionary of all settings
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("SELECT key, value, description FROM settings")
        results = cursor.fetchall()

        settings = {}
        for row in results:
            settings[row["key"]] = {
                "value": row["value"],
                "description": row["description"]
            }

        return settings

    except Exception as e:
        logger.error(f"Error getting all settings: {e}")
        return {}

    finally:
        conn.close()
