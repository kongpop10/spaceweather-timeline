"""
Utility functions for the spaceweather app
"""
import os
import json
from datetime import datetime, timedelta
import pandas as pd

def ensure_data_dir():
    """Ensure the data directory exists"""
    os.makedirs("data", exist_ok=True)

def get_data_file_path(date_str=None):
    """Get the path to the data file for a specific date"""
    if date_str is None:
        date_str = datetime.now().strftime("%Y-%m-%d")
    return f"data/spaceweather_{date_str}.json"

def save_data(data, date_str=None):
    """Save data to a JSON file"""
    ensure_data_dir()
    file_path = get_data_file_path(date_str)
    with open(file_path, 'w') as f:
        json.dump(data, f, indent=2)
    return file_path

def load_data(date_str=None):
    """Load data from a JSON file"""
    file_path = get_data_file_path(date_str)
    if os.path.exists(file_path):
        with open(file_path, 'r') as f:
            return json.load(f)
    return None

def get_all_data():
    """Get all data from all JSON files"""
    ensure_data_dir()
    all_data = []
    for file in os.listdir("data"):
        if file.startswith("spaceweather_") and file.endswith(".json"):
            with open(os.path.join("data", file), 'r') as f:
                try:
                    data = json.load(f)
                    all_data.append(data)
                except json.JSONDecodeError:
                    continue
    return all_data

def get_date_range(days=14):
    """
    Get a range of dates

    Args:
        days (int): Number of days to include in the range

    Returns:
        list: List of date strings in format YYYY-MM-DD
    """
    # Use current date for real usage
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days-1)

    date_range = []
    current_date = start_date
    while current_date <= end_date:
        date_range.append(current_date.strftime("%Y-%m-%d"))
        current_date += timedelta(days=1)
    return date_range

def events_to_dataframe(events):
    """Convert events to a pandas DataFrame"""
    if not events:
        return pd.DataFrame()

    flat_events = []
    for event in events:
        for category, category_events in event.get("events", {}).items():
            for cat_event in category_events:
                flat_event = {
                    "date": event.get("date"),
                    "category": category,
                    "tone": cat_event.get("tone"),
                    "detail": cat_event.get("detail"),
                    "predicted_arrival": cat_event.get("predicted_arrival"),
                    "image_url": cat_event.get("image_url")
                }
                flat_events.append(flat_event)

    return pd.DataFrame(flat_events)
