"""
Functions to store and retrieve data
"""
import os
import json
from datetime import datetime, timedelta
import logging
from utils import save_data, load_data, get_all_data, get_date_range
from scraper import scrape_spaceweather, extract_spaceweather_sections
from llm_processor import analyze_spaceweather_data

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

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
    existing_data = load_data(date_str)

    # Check if existing data is empty and we're forcing a refresh
    if existing_data and not force_refresh:
        # Check if the existing data has events
        events = existing_data.get("events", {})
        total_events = sum(len(events.get(cat, [])) for cat in ["cme", "sunspot", "flares", "coronal_holes"])

        if total_events > 0 and "error" not in existing_data:
            logger.info(f"Data for {date_str} already exists with {total_events} events")
            return existing_data
        elif not force_refresh:
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

    # Save the data
    save_data(analyzed_data, date_str)
    logger.info(f"Data for {date_str} processed and saved")

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

    # Generate date range
    date_range = []
    temp_date_obj = current_date_obj
    while temp_date_obj <= end_date_obj:
        date_range.append(temp_date_obj.strftime("%Y-%m-%d"))
        temp_date_obj += timedelta(days=1)

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
