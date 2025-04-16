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

def process_date(date_str):
    """
    Process data for a specific date

    Args:
        date_str (str): Date in format YYYY-MM-DD

    Returns:
        dict: Processed data
    """
    # Check if data already exists
    existing_data = load_data(date_str)
    if existing_data:
        logger.info(f"Data for {date_str} already exists")
        return existing_data

    # Scrape the data
    logger.info(f"Scraping data for {date_str}")
    scraped_data = scrape_spaceweather(date_str)

    if not scraped_data:
        logger.warning(f"No data found for {date_str}")
        return None

    # Extract sections
    sections = extract_spaceweather_sections(scraped_data)

    # Analyze with LLM
    logger.info(f"Analyzing data for {date_str} with LLM")
    analyzed_data = analyze_spaceweather_data(sections)

    if analyzed_data:
        # Save the data
        save_data(analyzed_data, date_str)
        logger.info(f"Data for {date_str} processed and saved")

    return analyzed_data

def process_date_range(start_date=None, end_date=None, days=30):
    """
    Process data for a range of dates

    Args:
        start_date (str, optional): Start date in format YYYY-MM-DD
        end_date (str, optional): End date in format YYYY-MM-DD
        days (int, optional): Number of days to process if start_date is not provided

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
        result = process_date(date_str)
        if result:
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
        date = data.get("date")
        events = data.get("events", {})

        significant_count = 0

        # Count significant events in each category
        for _, category_events in events.items():
            for event in category_events:
                if event.get("tone") == "Significant":
                    significant_count += 1

        if significant_count > 0:
            significant_events[date] = significant_count

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
        date = data.get("date")
        events = data.get("events", {})

        counts = {
            "cme": len(events.get("cme", [])),
            "sunspot": len(events.get("sunspot", [])),
            "flares": len(events.get("flares", [])),
            "coronal_holes": len(events.get("coronal_holes", [])),
            "total": 0
        }

        counts["total"] = counts["cme"] + counts["sunspot"] + counts["flares"] + counts["coronal_holes"]

        event_counts[date] = counts

    return event_counts
