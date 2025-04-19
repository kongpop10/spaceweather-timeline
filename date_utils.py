"""
Date utility functions for the Space Weather Timeline app
"""
from datetime import datetime, timedelta
import logging

# Configure logging
logger = logging.getLogger(__name__)

def calculate_date_range(admin_selected_date=None, days_to_show=14, forecast_days=3):
    """
    Calculate the date range based on admin_selected_date and days_to_show

    Args:
        admin_selected_date (str): Admin selected date in format YYYY-MM-DD
        days_to_show (int): Number of days to show
        forecast_days (int): Number of days to forecast into the future

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
            # Allow center_date to be in the future for forecast purposes
            # but limit it to today + forecast_days
            max_future_date = today + timedelta(days=forecast_days)
            if center_date > max_future_date:
                center_date = max_future_date
                logger.warning(f"Adjusted center date to max future date ({max_future_date.strftime('%Y-%m-%d')})")

            # Calculate half the days to show on each side of the center date
            half_days = days_to_show // 2

            # Calculate start and end dates centered around the selected date
            start_date = center_date - timedelta(days=half_days)
            end_date = center_date + timedelta(days=half_days)

            # Adjust if end_date is too far in the future
            max_end_date = today + timedelta(days=forecast_days)
            if end_date > max_end_date:
                end_date = max_end_date
                # Shift start date to maintain the requested number of days if possible
                start_date = end_date - timedelta(days=days_to_show - 1)  # -1 because we want to include the end date
        except Exception as e:
            # If there's any error parsing the admin_selected_date, fall back to default behavior
            logger.error(f"Error processing admin_selected_date: {e}. Using default date range.")
            end_date = today + timedelta(days=forecast_days)
            start_date = today - timedelta(days=days_to_show - forecast_days - 1)
    else:
        # Use today + forecast_days as the end date
        end_date = today + timedelta(days=forecast_days)
        # Calculate start date based on days_to_show
        start_date = today - timedelta(days=days_to_show - forecast_days - 1)  # -1 because we want to include the end date

    # Generate date range including future dates for forecast
    date_range = []
    current_date = start_date
    while current_date <= end_date:
        date_str = current_date.strftime("%Y-%m-%d")
        date_range.append(date_str)
        current_date += timedelta(days=1)

    # Log the date range
    logger.info(f"Date range: {date_range[0]} to {date_range[-1]} ({len(date_range)} days)")

    return start_date, end_date, date_range
