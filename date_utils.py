"""
Date utility functions for the Space Weather Timeline app
"""
from datetime import datetime, timedelta
import logging

# Configure logging
logger = logging.getLogger(__name__)

def calculate_date_range(admin_selected_date=None, days_to_show=14):
    """
    Calculate the date range based on admin_selected_date and days_to_show

    Args:
        admin_selected_date (str): Admin selected date in format YYYY-MM-DD
        days_to_show (int): Number of days to show

    Returns:
        tuple: (start_date, end_date, date_range)
    """
    # Ensure days_to_show is a valid integer
    if days_to_show is None or not isinstance(days_to_show, int) or days_to_show <= 0:
        logger.warning(f"Invalid days_to_show value: {days_to_show}. Using default of 14 days.")
        days_to_show = 14

    # Get today's date
    today = datetime.now()

    # If admin_selected_date is provided, use it as the center date
    if admin_selected_date is not None:
        try:
            # Use the admin selected date as the center date
            center_date = datetime.strptime(admin_selected_date, "%Y-%m-%d")
            # Make sure center_date is not in the future
            if center_date > today:
                center_date = today
                logger.warning(f"Adjusted center date to today ({today.strftime('%Y-%m-%d')}) to avoid future dates")

            # Calculate half the days to show on each side of the center date
            half_days = days_to_show // 2

            # Calculate start and end dates centered around the selected date
            start_date = center_date - timedelta(days=half_days)
            end_date = center_date + timedelta(days=half_days)

            # Adjust if end_date is in the future
            if end_date > today:
                end_date = today
                # Shift start date to maintain the requested number of days if possible
                start_date = end_date - timedelta(days=days_to_show - 1)  # -1 because we want to include the end date
        except Exception as e:
            # If there's any error parsing the admin_selected_date, fall back to default behavior
            logger.error(f"Error processing admin_selected_date: {e}. Using default date range.")
            end_date = today
            start_date = end_date - timedelta(days=days_to_show - 1)
    else:
        # Use today as the end date
        end_date = today
        # Calculate start date based on days_to_show
        start_date = end_date - timedelta(days=days_to_show - 1)  # -1 because we want to include the end date

    # Generate date range
    date_range = []
    current_date = start_date
    while current_date <= end_date:
        date_range.append(current_date.strftime("%Y-%m-%d"))
        current_date += timedelta(days=1)

    return start_date, end_date, date_range
