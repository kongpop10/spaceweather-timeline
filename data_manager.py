"""
Functions to store and retrieve data
"""
import os
import json
from datetime import datetime, timedelta
import logging
import streamlit as st
from utils import save_data, load_data, get_all_data, get_date_range
from scraper import scrape_spaceweather, extract_spaceweather_sections
from llm_processor import analyze_spaceweather_data
from db_manager import (
    init_db, save_data_to_db, load_data_from_db,
    get_all_data_from_db, import_json_to_db,
    get_unsynced_data, mark_as_synced
)
from supabase_sync import SupabaseClient

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Initialize database
init_db()

# Initialize Supabase client
def get_supabase_client():
    """Get a Supabase client"""
    if not hasattr(st.session_state, 'supabase_client'):
        url = st.secrets.get('SUPABASE_URL', '')
        api_key = st.secrets.get('SUPABASE_API_KEY', '')
        if url and api_key:
            st.session_state.supabase_client = SupabaseClient(url, api_key)
        else:
            st.session_state.supabase_client = None
    return st.session_state.supabase_client

def check_supabase_for_data(date_str):
    """
    Check Supabase for data for a specific date

    Args:
        date_str (str): Date in format YYYY-MM-DD

    Returns:
        dict: Data from Supabase or None if not found
    """
    supabase_client = get_supabase_client()
    if not supabase_client:
        logger.info("Supabase client not available")
        return None

    try:
        # Try to get data from Supabase
        supabase_data = supabase_client.get_date(date_str)
        if supabase_data:
            # Check if the data has events
            events = supabase_data.get("events", {})
            total_events = sum(len(events.get(cat, [])) for cat in ["cme", "sunspot", "flares", "coronal_holes"])

            if total_events > 0 and "error" not in supabase_data:
                logger.info(f"Data for {date_str} found in Supabase with {total_events} events")
                # Save to local database for future use
                save_data_to_db(supabase_data)
                return supabase_data
            else:
                logger.info(f"Data for {date_str} found in Supabase but has no events")
        else:
            logger.info(f"No data found in Supabase for {date_str}")

        return None
    except Exception as e:
        logger.error(f"Error checking Supabase for data: {e}")
        return None

def process_date(date_str, force_refresh=False, max_retries=2):
    """
    Process data for a specific date

    Args:
        date_str (str): Date in format YYYY-MM-DD
        force_refresh (bool): Whether to force refresh the data even if it exists
        max_retries (int): Maximum number of retries for LLM analysis

    Returns:
        dict: Processed data
    """
    # Check if data already exists and we're not forcing a refresh
    existing_data = load_data_from_db(date_str)

    # If not in SQLite, try JSON files as fallback
    if not existing_data:
        existing_data = load_data(date_str)
        # If found in JSON, import to SQLite
        if existing_data:
            save_data_to_db(existing_data)
            logger.info(f"Imported data for {date_str} from JSON to SQLite")

    # If still no data, check Supabase
    if not existing_data and not force_refresh:
        existing_data = check_supabase_for_data(date_str)
        if existing_data:
            logger.info(f"Data for {date_str} retrieved from Supabase and saved to local database")

    # Check if existing data is empty and we're forcing a refresh
    if existing_data and not force_refresh:
        # Check if the existing data has events
        events = existing_data.get("events", {})
        total_events = sum(len(events.get(cat, [])) for cat in ["cme", "sunspot", "flares", "coronal_holes"])

        if total_events > 0 and "error" not in existing_data:
            logger.info(f"Data for {date_str} already exists with {total_events} events")
            return existing_data
        elif not force_refresh:
            # If data exists but has no events, check Supabase before returning
            if total_events == 0 or "error" in existing_data:
                supabase_data = check_supabase_for_data(date_str)
                if supabase_data:
                    # If Supabase has data with events, use that instead
                    events = supabase_data.get("events", {})
                    total_events = sum(len(events.get(cat, [])) for cat in ["cme", "sunspot", "flares", "coronal_holes"])
                    if total_events > 0 and "error" not in supabase_data:
                        logger.info(f"Using Supabase data for {date_str} which has {total_events} events")
                        return supabase_data

            logger.info(f"Data for {date_str} exists but has no events. Use force_refresh=True to reprocess.")
            return existing_data
        else:
            logger.info(f"Forcing refresh for {date_str} which has {total_events} events")

    # Scrape the data
    logger.info(f"Scraping data for {date_str}")
    scraped_data = scrape_spaceweather(date_str)

    # If no scraped data, create a minimal structure for the LLM to work with
    if not scraped_data:
        logger.warning(f"No data found for {date_str}. Creating minimal data structure.")
        # Format date as YYYY-MM-DD for consistency
        formatted_date = date_str
        url = f"https://spaceweather.com/archive.php?view=1&day={date_str[8:10]}&month={date_str[5:7]}&year={date_str[0:4]}"

        # Create minimal data structure
        scraped_data = {
            'date': formatted_date,
            'url': url,
            'html': "",
            'text': f"No data available for {formatted_date}",
            'images': []
        }

    # Extract sections
    sections = extract_spaceweather_sections(scraped_data)

    # Try to analyze with LLM, with retries
    analyzed_data = None
    retries = 0

    while retries <= max_retries:
        # Analyze with LLM
        logger.info(f"Analyzing data for {date_str} with LLM (attempt {retries + 1}/{max_retries + 1})")
        analyzed_data = analyze_spaceweather_data(sections)

        # Check if we got valid data
        if analyzed_data and analyzed_data.get("events") and "error" not in analyzed_data:
            # Check if there are any events
            events = analyzed_data.get("events", {})
            total_events = sum(len(events.get(cat, [])) for cat in ["cme", "sunspot", "flares", "coronal_holes"])

            if total_events > 0:
                logger.info(f"Successfully analyzed data for {date_str} with {total_events} events")
                break
            else:
                logger.warning(f"LLM analysis returned no events for {date_str}. Retrying...")
        else:
            logger.warning(f"LLM analysis failed for {date_str}. Retrying...")

        retries += 1
        if retries > max_retries:
            logger.error(f"Failed to analyze data for {date_str} after {max_retries + 1} attempts")

    # If LLM analysis failed or returned an empty structure, create a basic structure
    if not analyzed_data or not analyzed_data.get("events") or "error" in analyzed_data:
        logger.warning(f"LLM analysis failed or returned empty data for {date_str}. Creating basic data structure.")
        analyzed_data = {
            "date": date_str,
            "url": scraped_data.get('url'),
            "events": {
                "cme": [],
                "sunspot": [],
                "flares": [],
                "coronal_holes": []
            },
            "error": analyzed_data.get("error", "LLM analysis failed") if analyzed_data else "LLM analysis failed"
        }

    # Save the data to SQLite
    save_data_to_db(analyzed_data)
    logger.info(f"Data for {date_str} processed and saved to SQLite")

    # Also save to JSON for backward compatibility
    save_data(analyzed_data, date_str)

    # Try to sync with Supabase if client is available
    supabase_client = get_supabase_client()
    if supabase_client:
        try:
            if supabase_client.sync_date(analyzed_data):
                logger.info(f"Data for {date_str} synced to Supabase")
            else:
                logger.warning(f"Failed to sync data for {date_str} to Supabase")
        except Exception as e:
            logger.error(f"Error syncing data to Supabase: {e}")

    return analyzed_data

def process_date_range(start_date=None, end_date=None, days=30, force_refresh=False):
    """
    Process data for a range of dates

    Args:
        start_date (str, optional): Start date in format YYYY-MM-DD
        end_date (str, optional): End date in format YYYY-MM-DD
        days (int, optional): Number of days to process if start_date is not provided
        force_refresh (bool): Whether to force refresh the data even if it exists

    Returns:
        list: List of processed data
    """
    # If end_date is not provided, use today
    today = datetime.now()
    if end_date is None:
        end_date = today.strftime("%Y-%m-%d")

    # If start_date is not provided, calculate based on days
    if start_date is None:
        end_date_obj = datetime.strptime(end_date, "%Y-%m-%d")
        start_date_obj = end_date_obj - timedelta(days=days)
        start_date = start_date_obj.strftime("%Y-%m-%d")

    # Parse date strings to datetime objects
    current_date_obj = datetime.strptime(start_date, "%Y-%m-%d")
    end_date_obj = datetime.strptime(end_date, "%Y-%m-%d")

    # Ensure we don't try to scrape future dates
    if end_date_obj > today:
        end_date_obj = today
        logger.warning(f"Adjusted end date to today ({today.strftime('%Y-%m-%d')}) to avoid scraping future dates")

    # Adjust start date to be no more than 'days' days before today
    earliest_date = today - timedelta(days=days)
    if current_date_obj < earliest_date:
        current_date_obj = earliest_date
        logger.warning(f"Adjusted start date to {earliest_date.strftime('%Y-%m-%d')} to avoid scraping too far in the past")

    # Generate date range (only include dates up to today)
    date_range = []
    temp_date_obj = current_date_obj
    today_obj = datetime.now()
    while temp_date_obj <= end_date_obj:
        # Only include dates up to today for scraping
        if temp_date_obj <= today_obj:
            date_range.append(temp_date_obj.strftime("%Y-%m-%d"))
        temp_date_obj += timedelta(days=1)

    # If not forcing refresh, try to get data from Supabase for the entire date range
    if not force_refresh:
        # Try to get data from Supabase for all dates at once
        supabase_client = get_supabase_client()
        if supabase_client:
            try:
                logger.info(f"Checking Supabase for data in date range {start_date} to {end_date}")
                supabase_data = supabase_client.get_all_dates()
                if supabase_data:
                    # Filter to only include dates in our range
                    supabase_data = [data for data in supabase_data if data.get("date") in date_range]

                    # Save all valid data to local database
                    for data in supabase_data:
                        # Check if the data has events
                        events = data.get("events", {})
                        total_events = sum(len(events.get(cat, [])) for cat in ["cme", "sunspot", "flares", "coronal_holes"])

                        if total_events > 0 and "error" not in data:
                            save_data_to_db(data)
                            logger.info(f"Data for {data.get('date')} retrieved from Supabase and saved to local database")

                    logger.info(f"Retrieved {len(supabase_data)} dates from Supabase")
            except Exception as e:
                logger.error(f"Error retrieving data from Supabase: {e}")

    # Process each date
    results = []
    for date_str in date_range:
        result = process_date(date_str, force_refresh=force_refresh)
        # Always add the result, even if it's a minimal structure
        results.append(result)

    return results

def get_significant_events(data_list):
    """
    Get significant events from a list of data

    Args:
        data_list (list): List of processed data

    Returns:
        dict: Dictionary with dates as keys and counts of significant events as values
    """
    significant_events = {}

    for data in data_list:
        if not data:  # Skip None values
            continue

        date = data.get("date")
        if not date:  # Skip entries without a date
            continue

        events = data.get("events", {})

        # Ensure we have a valid events dictionary
        if not isinstance(events, dict):
            logger.warning(f"Invalid events data for date {date}: {events}")
            continue

        significant_count = 0

        # Count significant events in each category
        for category, category_events in events.items():
            # Skip if category_events is not a list
            if not isinstance(category_events, list):
                logger.warning(f"Invalid category events for {date}, {category}: {category_events}")
                continue

            for event in category_events:
                # Skip if event is not a dictionary
                if not isinstance(event, dict):
                    logger.warning(f"Invalid event for {date}, {category}: {event}")
                    continue

                if event.get("tone") == "Significant":
                    significant_count += 1

        if significant_count > 0:
            significant_events[date] = significant_count
            logger.debug(f"Found {significant_count} significant events for {date}")

    return significant_events

def sync_with_supabase():
    """
    Sync unsynced data with Supabase

    Returns:
        tuple: (success_count, total_count)
    """
    supabase_client = get_supabase_client()
    if not supabase_client:
        logger.warning("Supabase client not available")
        return 0, 0

    # Get unsynced data
    unsynced_data = get_unsynced_data()
    total_count = len(unsynced_data)
    success_count = 0

    for data in unsynced_data:
        date_id = data.pop('id', None)  # Remove id from data before syncing
        if supabase_client.sync_date(data):
            mark_as_synced(date_id)
            success_count += 1
            logger.info(f"Data for {data.get('date')} synced to Supabase")
        else:
            logger.warning(f"Failed to sync data for {data.get('date')} to Supabase")

    return success_count, total_count

def import_all_json_to_db():
    """
    Import all JSON files to the SQLite database

    Returns:
        int: Number of files imported
    """
    return import_json_to_db()

def generate_forecast_data(data_list, date_range):
    """
    Generate forecast data based on predicted arrival times in the data

    Args:
        data_list (list): List of processed data
        date_range (list): List of dates in the range

    Returns:
        dict: Dictionary with forecast data by date
    """
    forecast_data = {}
    today = datetime.now().strftime("%Y-%m-%d")

    # Identify which dates in the date_range are in the future
    future_dates = [date for date in date_range if date > today]

    if not future_dates:
        return forecast_data

    # Look through all data for predicted arrival times
    for data in data_list:
        if not data or "events" not in data:
            continue

        events = data.get("events", {})

        # Check each category for events with predicted_arrival dates
        for category, category_events in events.items():
            if not isinstance(category_events, list):
                continue

            for event in category_events:
                if not isinstance(event, dict):
                    continue

                predicted_arrival = event.get("predicted_arrival")
                if not predicted_arrival or predicted_arrival not in future_dates:
                    continue

                # Create forecast entry for this date if it doesn't exist
                if predicted_arrival not in forecast_data:
                    forecast_data[predicted_arrival] = {
                        "date": predicted_arrival,
                        "is_forecast": True,
                        "events": {
                            "cme": [],
                            "sunspot": [],
                            "flares": [],
                            "coronal_holes": []
                        }
                    }

                # Add this event to the forecast
                forecast_event = {
                    "tone": event.get("tone", "Normal"),
                    "date": data.get("date"),  # Original observation date
                    "predicted_arrival": predicted_arrival,
                    "detail": f"<p><strong>Forecast:</strong> {event.get('detail', '')}</p>",
                    "image_url": event.get("image_url"),
                    "is_forecast": True
                }

                forecast_data[predicted_arrival]["events"][category].append(forecast_event)

    logger.info(f"Generated forecast data for {len(forecast_data)} future dates")
    return forecast_data

def count_events_by_category(data_list):
    """
    Count events by category

    Args:
        data_list (list): List of processed data

    Returns:
        dict: Dictionary with dates as keys and counts of events by category as values
    """
    event_counts = {}

    for data in data_list:
        if not data:  # Skip None values
            continue

        date = data.get("date")
        if not date:  # Skip entries without a date
            continue

        events = data.get("events", {})

        # Ensure we have a valid events dictionary
        if not isinstance(events, dict):
            logger.warning(f"Invalid events data for date {date}: {events}")
            events = {}

        # Create a default count structure even if there are no events
        counts = {
            "cme": len(events.get("cme", [])) if isinstance(events.get("cme"), list) else 0,
            "sunspot": len(events.get("sunspot", [])) if isinstance(events.get("sunspot"), list) else 0,
            "flares": len(events.get("flares", [])) if isinstance(events.get("flares"), list) else 0,
            "coronal_holes": len(events.get("coronal_holes", [])) if isinstance(events.get("coronal_holes"), list) else 0,
            "total": 0
        }

        counts["total"] = counts["cme"] + counts["sunspot"] + counts["flares"] + counts["coronal_holes"]

        # Add the counts to the dictionary even if total is 0
        event_counts[date] = counts

        # Log the counts for debugging
        logger.debug(f"Event counts for {date}: {counts}")

    return event_counts
