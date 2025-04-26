"""
Streamlit app for spaceweather.com data visualization
"""
import streamlit as st
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Import utility modules
from utils import get_date_range
from data_manager import process_date, process_date_range
from db_manager import get_all_data_from_db

# Import refactored modules
from styles import get_app_styles, get_mobile_detection_js
from session_state import initialize_session_state, get_current_llm_info
from date_utils import calculate_date_range
from components.admin import render_admin_panel
from components.timeline import create_timeline_visualization, create_date_selector, prepare_timeline_data
from components.event_display import display_events, display_significant_events_section
from components.statistics import display_statistics

# Set page config
st.set_page_config(
    page_title="Space Weather Timeline",
    page_icon="☀️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Apply custom CSS
st.markdown(get_app_styles(), unsafe_allow_html=True)

# Add JavaScript for mobile detection
st.markdown(get_mobile_detection_js(), unsafe_allow_html=True)

# Initialize session state
initialize_session_state()

# Title
st.title("☀️ Space Weather Timeline")

# Get current LLM provider
provider, model_name = get_current_llm_info()

# Display appropriate subtitle based on provider
st.markdown("Tracking solar events from spaceweather.com using AI")

# Render admin panel in sidebar
# Get days_to_show from session state or use default from database
from db_manager import get_setting
default_days = int(get_setting('default_days_to_show', '14'))
days_to_show = st.session_state.admin_days_to_show if st.session_state.admin_days_to_show is not None else default_days
# Render admin panel and get updated days_to_show from the slider in the admin panel
days_to_show = render_admin_panel(days_to_show)

# Calculate date range with forecast days
forecast_days = 3  # Number of days to forecast into the future
start_date, end_date, date_range = calculate_date_range(
    admin_selected_date=st.session_state.admin_selected_date,
    days_to_show=days_to_show,
    forecast_days=forecast_days
)

# Display date range in the main area
st.markdown(f"**Date Range:** {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")

# Set local variables from session state
show_cme = st.session_state.show_cme
show_sunspot = st.session_state.show_sunspot
show_flares = st.session_state.show_flares
show_coronal_holes = st.session_state.show_coronal_holes
show_significant_only = st.session_state.get("show_significant_only", False)

# Process data for selected date range
@st.cache_data(ttl=3600, show_spinner=False)  # Cache for 1 hour
def load_timeline_data(force_refresh=False, days_to_show_param=None):
    """Load timeline data, using cached data when available

    Args:
        force_refresh (bool): Whether to force refresh the data even if it exists
        days_to_show_param (int, optional): Number of days to show. Defaults to None.

    Returns:
        list: Filtered data for the selected date range
    """
    # Use the passed days_to_show parameter if provided, otherwise use the global one
    # This ensures the cache is invalidated when days_to_show changes
    current_days_to_show = days_to_show_param if days_to_show_param is not None else days_to_show
    # Calculate date range with forecast days
    forecast_days = 3  # Number of days to forecast into the future
    _, _, date_range = calculate_date_range(
        admin_selected_date=st.session_state.admin_selected_date,
        days_to_show=current_days_to_show,
        forecast_days=forecast_days
    )

    # Check if we need to process any dates
    existing_data = get_all_data_from_db()
    existing_dates = [data.get("date") for data in existing_data]

    # Identify which dates need to be processed (only process dates up to today)
    today = datetime.now().strftime("%Y-%m-%d")
    dates_to_process = [date for date in date_range if date not in existing_dates and date <= today]
    dates_from_cache = [date for date in date_range if date in existing_dates]

    # If we have dates to process, check Supabase first
    if dates_to_process and not force_refresh:
        from data_manager import get_supabase_client

        # Try to get data from Supabase only for the dates we need to process
        supabase_client = get_supabase_client()
        if supabase_client:
            try:
                # Get the earliest and latest dates we need to process
                if dates_to_process:
                    # Sort dates to ensure we get the correct range
                    sorted_dates = sorted(dates_to_process)
                    earliest_date = sorted_dates[0]
                    latest_date = sorted_dates[-1]

                    logger.info(f"Checking Supabase for data in date range {earliest_date} to {latest_date}")

                    # Use the new method to get only the dates in our range
                    supabase_data = supabase_client.get_dates_in_range(earliest_date, latest_date)

                    if supabase_data:
                        # Filter to only include dates we need to process
                        supabase_data = [data for data in supabase_data if data.get("date") in dates_to_process]

                        # Save all valid data to local database
                        for data in supabase_data:
                            # Check if the data has events
                            events = data.get("events", {})
                            total_events = sum(len(events.get(cat, [])) for cat in ["cme", "sunspot", "flares", "coronal_holes"])

                            if total_events > 0 and "error" not in data:
                                # Save to local database
                                from db_manager import save_data_to_db
                                save_data_to_db(data)
                                logger.info(f"Data for {data.get('date')} retrieved from Supabase and saved to local database")

                                # Add a flag to indicate this data came from Supabase
                                if "from_supabase" not in st.session_state:
                                    st.session_state.from_supabase = []
                                st.session_state.from_supabase.append(data.get("date"))

                                # Remove from dates_to_process
                                if data.get("date") in dates_to_process:
                                    dates_to_process.remove(data.get("date"))
                                    dates_from_cache.append(data.get("date"))

                        logger.info(f"Retrieved {len(supabase_data)} dates from Supabase")
            except Exception as e:
                logger.error(f"Error retrieving data from Supabase: {e}")

    # Check for empty data structures (those with no events or error messages)
    dates_with_empty_data = []
    for data in existing_data:
        if data.get("date") in date_range:
            # Skip future dates by comparing datetime objects
            try:
                date_str = data.get("date")
                date_obj = datetime.strptime(date_str, "%Y-%m-%d")
                today_obj = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

                if date_obj > today_obj:
                    # Check if we're dealing with a date from a different year
                    # If the date is from a past year, we should process it as a historical date
                    if date_str.startswith("2025-") or date_str.startswith("2024-"):
                        continue
                    # Otherwise, it's a historical date from a past year, so we should process it
            except (ValueError, TypeError):
                # If we can't parse the date, skip this entry
                continue

            # Skip dates marked as forecasts
            if data.get("is_forecast", False):
                continue

            events = data.get("events", {})
            total_events = sum(len(events.get(cat, [])) for cat in ["cme", "sunspot", "flares", "coronal_holes"])
            if total_events == 0 or "error" in data:
                dates_with_empty_data.append(data.get("date"))

    # For dates with empty data, check Supabase first before adding to dates_to_process
    if dates_with_empty_data and not force_refresh:
        logger.info(f"Found {len(dates_with_empty_data)} dates with empty data. Checking Supabase first.")

        # Try to get data from Supabase for empty dates
        supabase_client = get_supabase_client() if 'get_supabase_client' in locals() else None
        if not supabase_client:
            from data_manager import get_supabase_client
            supabase_client = get_supabase_client()

        if supabase_client:
            try:
                if dates_with_empty_data:
                    # Sort dates to ensure we get the correct range
                    sorted_empty_dates = sorted(dates_with_empty_data)
                    earliest_date = sorted_empty_dates[0]
                    latest_date = sorted_empty_dates[-1]

                    logger.info(f"Checking Supabase for empty data in date range {earliest_date} to {latest_date}")

                    # Use the new method to get only the dates in our range
                    supabase_data = supabase_client.get_dates_in_range(earliest_date, latest_date)

                    if supabase_data:
                        # Process each date that was found in Supabase
                        for data in supabase_data:
                            date = data.get("date")
                            if date in dates_with_empty_data:
                                # Check if the data has events
                                events = data.get("events", {})
                                total_events = sum(len(events.get(cat, [])) for cat in ["cme", "sunspot", "flares", "coronal_holes"])

                                if total_events > 0 and "error" not in data:
                                    # Save to local database
                                    from db_manager import save_data_to_db
                                    save_data_to_db(data)
                                    logger.info(f"Data for {date} retrieved from Supabase and saved to local database")

                                    # Add a flag to indicate this data came from Supabase
                                    if "from_supabase" not in st.session_state:
                                        st.session_state.from_supabase = []
                                    st.session_state.from_supabase.append(date)

                                    # Remove from dates_with_empty_data
                                    dates_with_empty_data.remove(date)

                # For any remaining dates that weren't found in the batch request, try individual requests
                for date in list(dates_with_empty_data):  # Use list() to create a copy we can modify while iterating
                    # Try to get data from Supabase for this date
                    supabase_data = supabase_client.get_date(date)
                    if supabase_data:
                        # Check if the data has events
                        events = supabase_data.get("events", {})
                        total_events = sum(len(events.get(cat, [])) for cat in ["cme", "sunspot", "flares", "coronal_holes"])

                        if total_events > 0 and "error" not in supabase_data:
                            # Save to local database
                            from db_manager import save_data_to_db
                            save_data_to_db(supabase_data)
                            logger.info(f"Data for {date} retrieved from Supabase and saved to local database")

                            # Add a flag to indicate this data came from Supabase
                            if "from_supabase" not in st.session_state:
                                st.session_state.from_supabase = []
                            st.session_state.from_supabase.append(date)

                            # Remove from dates_with_empty_data
                            dates_with_empty_data.remove(date)
            except Exception as e:
                logger.error(f"Error retrieving data from Supabase for empty dates: {e}")

        # Add remaining dates with empty data to the dates to process
        logger.info(f"After checking Supabase, {len(dates_with_empty_data)} dates still have empty data. Will try to refresh them.")
        for date in dates_with_empty_data:
            if date not in dates_to_process:
                dates_to_process.append(date)

    # Process new dates if needed
    if dates_to_process or force_refresh:
        with st.spinner(f"Processing {len(dates_to_process) if not force_refresh else len(date_range)} dates..."):
            if force_refresh:
                # Process all dates with force_refresh=True (except future dates)
                for date in date_range:
                    # Skip future dates by comparing datetime objects
                    try:
                        date_obj = datetime.strptime(date, "%Y-%m-%d")
                        today_obj = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

                        if date_obj > today_obj:
                            # Check if we're dealing with a date from a different year
                            # If the date is from a past year, we should process it as a historical date
                            if date.startswith("2025-") or date.startswith("2024-"):
                                logger.info(f"Skipping future date {date} during force refresh")
                                continue
                            # Otherwise, it's a historical date from a past year, so we should process it
                            logger.info(f"Processing historical date {date} from a past year during force refresh")
                    except ValueError:
                        logger.error(f"Error parsing date {date}")
                        continue
                    process_date(date, force_refresh=True)
            else:
                # Process only new dates and dates with empty data (except future dates)
                for date in dates_to_process:
                    # Skip future dates by comparing datetime objects
                    try:
                        date_obj = datetime.strptime(date, "%Y-%m-%d")
                        today_obj = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

                        if date_obj > today_obj:
                            # Check if we're dealing with a date from a different year
                            # If the date is from a past year, we should process it as a historical date
                            if date.startswith("2025-") or date.startswith("2024-"):
                                logger.info(f"Skipping future date {date} during processing")
                                continue
                            # Otherwise, it's a historical date from a past year, so we should process it
                            logger.info(f"Processing historical date {date} from a past year during processing")
                    except ValueError:
                        logger.error(f"Error parsing date {date}")
                        continue
                    process_date(date, force_refresh=True)  # Force refresh for empty data too

        # Store the processed dates info in session state for admin panel
        processed_count = len(dates_to_process) if not force_refresh else len(date_range)
        if "processed_dates_count" not in st.session_state:
            st.session_state.processed_dates_count = processed_count
        else:
            st.session_state.processed_dates_count += processed_count

    # Store the cached dates info in session state for admin panel
    if dates_from_cache and not force_refresh:
        st.session_state.cached_dates_count = len(dates_from_cache)

    # Get all data again after processing
    all_data = get_all_data_from_db()

    # Filter by date range
    filtered_data = [data for data in all_data if data.get("date") in date_range]

    return filtered_data

# Check if we need to refresh data on page load
if st.session_state.check_empty_data:
    with st.spinner("Checking for empty data and refreshing if needed..."):
        # Clear the cache to force a refresh of the data
        st.cache_data.clear()
        timeline_data = load_timeline_data(force_refresh=False, days_to_show_param=days_to_show)
    # Set the flag to false so we don't check on every rerun
    st.session_state.check_empty_data = False
    logger.info("Refreshed data with check_empty_data=True")
else:
    # Always pass the current days_to_show to ensure cache is properly keyed
    timeline_data = load_timeline_data(force_refresh=False, days_to_show_param=days_to_show)
    logger.debug("Loaded data from cache or processed new dates")

# Check if there are any empty data entries
empty_data_count = 0
for data in timeline_data:
    events = data.get("events", {})
    total_events = sum(len(events.get(cat, [])) for cat in ["cme", "sunspot", "flares", "coronal_holes"])
    if total_events == 0 or "error" in data:
        empty_data_count += 1

# Show a message if there are empty data entries
if empty_data_count > 0:
    st.warning(f"Found {empty_data_count} dates with no events data. You can use the 'Refresh Empty Data' button in the Admin panel to try to fill in the missing data using the LLM.")

# Show a message if data was retrieved from Supabase
if "from_supabase" in st.session_state and st.session_state.from_supabase:
    supabase_count = len(st.session_state.from_supabase)
    st.success(f"Retrieved data for {supabase_count} date(s) from Supabase: {', '.join(st.session_state.from_supabase)}")
    # Clear the flag after displaying the message
    st.session_state.from_supabase = []

# Prepare timeline data with forecasts
show_forecasts = True  # Set to False to disable forecasts
event_counts, significant_events, timeline_df = prepare_timeline_data(timeline_data, date_range, include_forecast=show_forecasts)

# Create timeline visualization
create_timeline_visualization(timeline_df, show_cme, show_sunspot, show_flares, show_coronal_holes)

# Create date selector
create_date_selector(timeline_df, significant_events, event_counts, days_to_show)

# Display events for selected date
display_events(timeline_data, show_cme, show_sunspot, show_flares, show_coronal_holes, show_significant_only)

# Display significant events section
display_significant_events_section(timeline_data, timeline_df)

# Display statistics
display_statistics(timeline_df)

# Footer
st.markdown("---")
st.markdown("Data source: [spaceweather.com](https://spaceweather.com)")

# Display current LLM provider and model
provider, model_name = get_current_llm_info()
if provider == "grok":
    st.markdown(f"Powered by xAI: {model_name}")
else:
    st.markdown(f"Powered by OpenRouter: {model_name}")

# Add information about the app
with st.expander("About this app"):
    st.markdown("""
    This app scrapes data from spaceweather.com and uses the OpenRouter API with the deepseek/deepseek-chat-v3-0324:free model to categorize space weather events into four main categories:

    1. **Coronal Mass Ejections (CME)** - Including filament eruptions, their size, and whether they are Earth-facing
    2. **Sunspot Activity** - Including expansion, creation, extreme maximum or minimum
    3. **Solar Flares** - Including C, M, and X class flares
    4. **Coronal Holes** - Including coronal holes facing Earth or high-speed solar winds

    For each event, the app determines:
    - The tone (Normal or Significant)
    - Date of observation
    - Predicted arrival time at Earth (if applicable)
    - Detailed description
    - Associated images or links

    The timeline visualization highlights dates with significant events, and you can click on any date to view detailed information about the events on that day.

    **Forecast Feature:**
    The timeline also extends into the future to show forecasted space weather events based on predicted arrival times. These forecast events are displayed with a dashed pattern and are based on the predicted arrival data processed by the LLM from historical observations.
    """)

# Run the app
if __name__ == "__main__":
    # This code is executed when the script is run directly
    pass
