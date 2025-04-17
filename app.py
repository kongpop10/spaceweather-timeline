"""
Streamlit app for spaceweather.com data visualization
"""
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import logging
import html

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

from utils import get_date_range
from data_manager import (
    process_date, process_date_range, get_significant_events,
    count_events_by_category, import_all_json_to_db, sync_with_supabase
)
from db_manager import get_all_data_from_db

# Set page config
st.set_page_config(
    page_title="Space Weather Timeline",
    page_icon="☀️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS
st.markdown("""
<style>
    /* Dark mode compatible event cards */
    .event-card {
        border: 1px solid rgba(221, 221, 221, 0.3);
        border-radius: 5px;
        padding: 10px;
        margin-bottom: 10px;
        background-color: rgba(255, 255, 255, 0.05);
        color: inherit;
        transition: transform 0.2s, box-shadow 0.2s;
        position: relative;
    }
    .event-card:hover {
        transform: translateY(-2px);
    }
    .event-card.significant {
        border-left: 8px solid #ff4b4b;
        background: linear-gradient(90deg, rgba(255, 75, 75, 0.15) 0%, rgba(255, 255, 255, 0.05) 100%);
        box-shadow: 0 4px 8px rgba(255, 75, 75, 0.2);
    }
    .event-card.significant:hover {
        box-shadow: 0 6px 12px rgba(255, 75, 75, 0.3);
    }
    .event-card.significant::before {
        content: "SIGNIFICANT EVENT";
        position: absolute;
        top: -10px;
        right: 10px;
        background-color: #ff4b4b;
        color: white;
        font-size: 10px;
        font-weight: bold;
        padding: 2px 8px;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
    }
    .event-card h4 {
        margin-top: 0;
        color: inherit;
        font-size: 1.2em;
    }
    .event-card.significant h4 {
        color: #ff4b4b;
        font-weight: bold;
    }
    .event-card p {
        color: inherit;
        margin: 0.5em 0;
    }
    .event-card strong {
        color: inherit;
        font-weight: bold;
    }
    .event-card.significant strong {
        font-weight: bold;
    }
    /* Styling for event card details section */
    .event-card-details {
        margin: 0.5em 0;
        color: inherit;
    }
    .event-card-details p {
        color: inherit;
        margin: 0.5em 0;
    }
    .event-card-image {
        margin-top: 1em;
    }
    /* Ensure proper styling for HTML elements in event details */
    .event-card p strong, .event-card-details p strong {
        font-weight: bold;
    }
    .event-card em, .event-card-details em {
        font-style: italic;
    }
    .event-card ul, .event-card ol, .event-card-details ul, .event-card-details ol {
        margin-left: 1.5em;
        margin-top: 0.5em;
        margin-bottom: 0.5em;
    }
    .event-card li, .event-card-details li {
        margin-bottom: 0.25em;
    }
    .event-card img, .event-card-image img {
        max-width: 100%;
        max-height: 400px;
        height: auto;
        border-radius: 4px;
        margin-top: 10px;
        object-fit: contain;
    }
    /* Date selector styling */
    .timeline-day {
        cursor: pointer;
        transition: transform 0.2s;
    }
    .timeline-day:hover {
        transform: scale(1.05);
    }
    .significant-day {
        font-weight: bold;
        color: #ff4b4b;
    }
    /* Significant date button styling */
    .significant-date-btn {
        background-color: rgba(255, 75, 75, 0.2) !important;
        border: 2px solid #ff4b4b !important;
        color: #ff4b4b !important;
        font-weight: bold !important;
        box-shadow: 0 2px 4px rgba(255, 75, 75, 0.3) !important;
    }
    /* Selected date button styling */
    .selected-date-btn {
        background-color: rgba(75, 181, 255, 0.2) !important;
        border: 2px solid #4bb5ff !important;
        color: #4bb5ff !important;
        font-weight: bold !important;
        box-shadow: 0 2px 4px rgba(75, 181, 255, 0.3) !important;
    }
    /* Pulsing animation for significant events */
    @keyframes pulse {
        0% { transform: scale(1); opacity: 1; }
        50% { transform: scale(1.1); opacity: 0.8; }
        100% { transform: scale(1); opacity: 1; }
    }
    .pulse {
        animation: pulse 2s infinite;
    }

</style>
""", unsafe_allow_html=True)

# Title
st.title("☀️ Space Weather Timeline")

# Get current LLM provider
if "llm_provider" in st.session_state:
    provider = st.session_state.llm_provider
else:
    provider = st.secrets.get("LLM_PROVIDER", "grok")

# Display appropriate subtitle based on provider
st.markdown("Tracking solar events from spaceweather.com using AI")

# Sidebar

# Initialize session state for admin authentication
if "admin_authenticated" not in st.session_state:
    st.session_state.admin_authenticated = False

# Initialize session state for LLM configuration
if "llm_provider" not in st.session_state:
    st.session_state.llm_provider = st.secrets.get("LLM_PROVIDER", "grok")

if "llm_base_url" not in st.session_state:
    st.session_state.llm_base_url = st.secrets.get("LLM_BASE_URL", "https://api.x.ai/v1")

if "llm_model" not in st.session_state:
    st.session_state.llm_model = st.secrets.get("LLM_MODEL", "grok-3-mini-beta")

if "llm_reasoning_effort" not in st.session_state:
    st.session_state.llm_reasoning_effort = st.secrets.get("LLM_REASONING_EFFORT", "low")

# Initialize session state for OpenRouter site information
if "site_url" not in st.session_state:
    st.session_state.site_url = st.secrets.get("SITE_URL", "https://spaceweather-timeline.streamlit.app")

if "site_name" not in st.session_state:
    st.session_state.site_name = st.secrets.get("SITE_NAME", "Space Weather Timeline")

# Initialize session state for selected date (default to today's date)
if "selected_date" not in st.session_state:
    st.session_state.selected_date = datetime.now().strftime("%Y-%m-%d")

# Initialize session state for admin date picker and days to show
if "admin_selected_date" not in st.session_state:
    st.session_state.admin_selected_date = None

if "admin_days_to_show" not in st.session_state:
    st.session_state.admin_days_to_show = None

# Date range selection - define days_to_show variable for use throughout the app
# Use admin settings if they exist, otherwise use default value
if st.session_state.admin_days_to_show is not None:
    days_to_show = st.session_state.admin_days_to_show
else:
    days_to_show = 14  # Default value

# Admin section with password protection
with st.sidebar.expander("⚙️ Admin"):
    if not st.session_state.admin_authenticated:
        admin_password = st.text_input("Password", type="password")
        if st.button("Login"):
            if admin_password == st.secrets["password"]:
                st.session_state.admin_authenticated = True
                st.success("Authentication successful!")
                st.rerun()
            else:
                st.error("Incorrect password")
    else:
        st.success("Authenticated as Admin")

        # LLM Configuration
        st.subheader("LLM Configuration")

        # Get current provider
        current_provider = st.session_state.llm_provider

        # Display current LLM service
        if current_provider == "grok":
            st.markdown(f"**Current LLM Service:** Grok with {st.session_state.llm_model} model")
        else:
            st.markdown(f"**Current LLM Service:** OpenRouter with {st.session_state.llm_model} model")

        # LLM Provider selection
        new_provider = st.selectbox(
            "LLM Provider",
            options=["grok", "openrouter"],
            index=0 if current_provider == "grok" else 1,
            help="Select the LLM provider to use for analysis"
        )

        # Show appropriate configuration based on selected provider
        if new_provider == "grok":
            # Grok configuration
            new_base_url = st.text_input("LLM Base URL",
                                        value="https://api.x.ai/v1" if current_provider != "grok" else st.session_state.llm_base_url)
            new_model = st.text_input("LLM Model",
                                     value="grok-3-mini-beta" if current_provider != "grok" else st.session_state.llm_model)
            new_reasoning_effort = st.select_slider(
                "Reasoning Effort",
                options=["low", "medium", "high"],
                value=st.session_state.llm_reasoning_effort if current_provider == "grok" else "low",
                help="Higher reasoning effort may produce better results but takes longer"
            )

            # Hide OpenRouter specific fields
            site_url = st.session_state.site_url
            site_name = st.session_state.site_name

        else:  # openrouter
            # OpenRouter configuration
            new_base_url = st.text_input("LLM Base URL",
                                        value="https://openrouter.ai/api/v1" if current_provider != "openrouter" else st.session_state.llm_base_url)
            new_model = st.text_input("LLM Model",
                                     value="deepseek/deepseek-chat-v3-0324:free" if current_provider != "openrouter" else st.session_state.llm_model)
            new_reasoning_effort = "low"  # Not used for OpenRouter

            # Site information for OpenRouter
            st.markdown("**OpenRouter Site Information:**")
            site_url = st.text_input("Site URL", value=st.session_state.site_url)
            site_name = st.text_input("Site Name", value=st.session_state.site_name)

        if st.button("Update LLM Config"):
            # Update provider
            st.session_state.llm_provider = new_provider

            # Update common settings
            st.session_state.llm_base_url = new_base_url
            st.session_state.llm_model = new_model

            # Update provider-specific settings
            if new_provider == "grok":
                st.session_state.llm_reasoning_effort = new_reasoning_effort

            # Update site information in session state (used by OpenRouter)
            st.session_state.site_url = site_url
            st.session_state.site_name = site_name

            st.success(f"LLM configuration updated to {new_provider.capitalize()}!")
            st.rerun()

        # Data Management
        st.subheader("Data Management")

        # Show data cache status
        existing_data = get_all_data_from_db()
        if existing_data:
            st.info(f"Database contains data for {len(existing_data)} dates")

            # Display cached and processed dates info from the current session
            if "cached_dates_count" in st.session_state:
                st.success(f"✓ Using cached data for {st.session_state.cached_dates_count} dates in current view")

            if "processed_dates_count" in st.session_state:
                st.info(f"✓ Processed {st.session_state.processed_dates_count} new dates in current session")

            # Database management buttons
            col1, col2, col3 = st.columns(3)

            with col1:
                if st.button("Import JSON to DB"):
                    with st.spinner("Importing JSON files to database..."):
                        count = import_all_json_to_db()
                    if count > 0:
                        st.success(f"Imported {count} JSON files to database!")
                    else:
                        st.info("No JSON files to import.")
                    st.rerun()

            with col2:
                if st.button("Sync with Supabase"):
                    with st.spinner("Syncing data with Supabase..."):
                        success_count, total_count = sync_with_supabase()
                    if total_count > 0:
                        st.success(f"Synced {success_count}/{total_count} records with Supabase!")
                    else:
                        st.info("No data to sync.")

            with col3:
                # Initialize session state for refresh confirmation
                if "show_refresh_confirmation" not in st.session_state:
                    st.session_state.show_refresh_confirmation = False

                # Show either the initial button or the confirmation dialog
                if not st.session_state.show_refresh_confirmation:
                    if st.button("Refresh All Data"):
                        # Set the flag to show the confirmation dialog
                        st.session_state.show_refresh_confirmation = True
                        st.rerun()
                else:
                    # Show warning and confirmation buttons
                    st.warning("⚠️ **WARNING**: This will erase all existing data for the current date range and fetch it again. This action cannot be undone.")

                    # Create two columns for the confirm/cancel buttons
                    confirm_col1, confirm_col2 = st.columns(2)

                    with confirm_col1:
                        if st.button("✅ Yes, Refresh All Data"):
                            with st.spinner("Fetching latest data..."):
                                # Force re-processing of the date range
                                date_range = get_date_range(days=days_to_show)
                                process_date_range(
                                    start_date=date_range[0],
                                    end_date=date_range[-1],
                                    force_refresh=True
                                )
                            # Reset the confirmation flag
                            st.session_state.show_refresh_confirmation = False
                            st.success("All data refreshed!")
                            st.rerun()

                    with confirm_col2:
                        if st.button("❌ Cancel"):
                            # Reset the confirmation flag
                            st.session_state.show_refresh_confirmation = False
                            st.rerun()

            # Second row of buttons
            col4, col5 = st.columns(2)

            with col4:
                # Initialize session state for cache clear confirmation
                if "show_cache_clear_confirmation" not in st.session_state:
                    st.session_state.show_cache_clear_confirmation = False

                # Show either the initial button or the confirmation dialog
                if not st.session_state.show_cache_clear_confirmation:
                    if st.button("Clear Streamlit Cache"):
                        # Set the flag to show the confirmation dialog
                        st.session_state.show_cache_clear_confirmation = True
                        st.rerun()
                else:
                    # Show warning and confirmation buttons
                    st.warning("⚠️ **WARNING**: This will clear all cached data. You may need to reload some data.")
                    # Create two columns for the confirm/cancel buttons
                    cache_confirm_col1, cache_confirm_col2 = st.columns(2)

                    with cache_confirm_col1:
                        if st.button("✅ Yes, Clear Cache"):
                            st.cache_data.clear()
                            # Reset session state counters
                            if "cached_dates_count" in st.session_state:
                                del st.session_state.cached_dates_count
                            if "processed_dates_count" in st.session_state:
                                del st.session_state.processed_dates_count
                            # Reset the confirmation flag
                            st.session_state.show_cache_clear_confirmation = False
                            st.success("Streamlit cache cleared!")
                            st.rerun()

                    with cache_confirm_col2:
                        if st.button("❌ Cancel", key="cancel_cache_clear"):
                            # Reset the confirmation flag
                            st.session_state.show_cache_clear_confirmation = False
                            st.rerun()

            with col5:
                # Initialize session state for refresh empty data confirmation
                if "show_refresh_empty_confirmation" not in st.session_state:
                    st.session_state.show_refresh_empty_confirmation = False

                # Show either the initial button or the confirmation dialog
                if not st.session_state.show_refresh_empty_confirmation:
                    if st.button("Refresh Empty Data"):
                        # Set the flag to show the confirmation dialog
                        st.session_state.show_refresh_empty_confirmation = True
                        st.rerun()
                else:
                    # Show warning and confirmation buttons
                    st.warning("⚠️ **WARNING**: This will attempt to refresh all empty data entries using the LLM.")
                    # Create two columns for the confirm/cancel buttons
                    empty_confirm_col1, empty_confirm_col2 = st.columns(2)

                    with empty_confirm_col1:
                        if st.button("✅ Yes, Refresh Empty Data"):
                            # Set the flag to check for empty data
                            st.session_state.check_empty_data = True
                            # Clear the cache to force a refresh
                            st.cache_data.clear()

                            # Get the date range
                            date_range = get_date_range(days=days_to_show)

                            # Find dates with empty data
                            existing_data = get_all_data_from_db()
                            dates_with_empty_data = []
                            for data in existing_data:
                                if data.get("date") in date_range:
                                    events = data.get("events", {})
                                    total_events = sum(len(events.get(cat, [])) for cat in ["cme", "sunspot", "flares", "coronal_holes"])
                                    if total_events == 0 or "error" in data:
                                        dates_with_empty_data.append(data.get("date"))

                            # Process empty dates with force_refresh=True
                            if dates_with_empty_data:
                                with st.spinner(f"Refreshing {len(dates_with_empty_data)} dates with empty data..."):
                                    for date in dates_with_empty_data:
                                        process_date(date, force_refresh=True)
                                st.success(f"Refreshed {len(dates_with_empty_data)} dates with empty data!")
                            else:
                                st.info("No empty data found to refresh.")

                            # Reset the confirmation flag
                            st.session_state.show_refresh_empty_confirmation = False
                            st.rerun()

                    with empty_confirm_col2:
                        if st.button("❌ Cancel", key="cancel_refresh_empty"):
                            # Reset the confirmation flag
                            st.session_state.show_refresh_empty_confirmation = False
                            st.rerun()
        else:
            st.warning("No data available in database")

        # Date Display Controls
        st.subheader("📅 Date Display Controls")
        st.markdown("Use these controls to set a specific date and range to display in the main area.")

        # Show current settings if they exist
        if st.session_state.admin_selected_date is not None or st.session_state.admin_days_to_show is not None:
            settings_info = []
            if st.session_state.admin_selected_date is not None:
                settings_info.append(f"📌 Focus date: **{st.session_state.admin_selected_date}**")
            if st.session_state.admin_days_to_show is not None:
                settings_info.append(f"📏 Days to display: **{st.session_state.admin_days_to_show}**")

            st.info("\n\n".join(settings_info))

        # Create two columns for the date picker and days input
        col1, col2 = st.columns(2)

        with col1:
            # Date picker for selecting a specific date
            admin_date = st.date_input(
                "Select a date to display",
                value=datetime.strptime(st.session_state.selected_date, "%Y-%m-%d") if st.session_state.admin_selected_date is None else datetime.strptime(st.session_state.admin_selected_date, "%Y-%m-%d"),
                min_value=datetime.now() - timedelta(days=365),
                max_value=datetime.now(),
                help="This date will be the focus of the display and will be selected in the main area"
            )

        with col2:
            # Number input for days to display
            admin_days = st.number_input(
                "Days to display",
                min_value=1,
                max_value=30,
                value=days_to_show if st.session_state.admin_days_to_show is None else st.session_state.admin_days_to_show,
                help="Number of days to show in the timeline, centered around the selected date"
            )

        # Create two columns for the buttons
        button_col1, button_col2 = st.columns(2)

        with button_col1:
            # Button to apply the settings
            if st.button("✅ Apply Settings", help="Apply these date settings to the main display"):
                # Convert the date to string format
                admin_date_str = admin_date.strftime("%Y-%m-%d")

                # Update session state
                st.session_state.admin_selected_date = admin_date_str
                st.session_state.admin_days_to_show = admin_days

                # Also update the selected date to show in the main area
                st.session_state.selected_date = admin_date_str

                st.success(f"Date settings updated! Showing {admin_days} days with focus on {admin_date_str}")
                st.rerun()

        with button_col2:
            # Button to reset to default settings
            if st.button("🔄 Reset to Default", help="Reset to default date settings"):
                st.session_state.admin_selected_date = None
                st.session_state.admin_days_to_show = None
                st.success("Date settings reset to default!")
                st.rerun()

        # Controls section (moved from main sidebar)
        st.subheader("📊 Controls")

        # Days to display slider
        if st.session_state.admin_days_to_show is None:  # Only show if not using admin date settings
            new_days_to_show = st.slider("Days to display", 1, 30, 14)  # Default to 14 days
            if new_days_to_show != days_to_show:
                days_to_show = new_days_to_show
                st.rerun()
        else:
            st.info(f"Using admin setting: {days_to_show} days to display")

        # Category filters
        st.markdown("**Event Categories**")
        st.session_state.show_cme = st.checkbox("Coronal Mass Ejections (CME)", value=st.session_state.show_cme)
        st.session_state.show_sunspot = st.checkbox("Sunspots", value=st.session_state.show_sunspot)
        st.session_state.show_flares = st.checkbox("Solar Flares", value=st.session_state.show_flares)
        st.session_state.show_coronal_holes = st.checkbox("Coronal Holes", value=st.session_state.show_coronal_holes)

        # Update local variables
        show_cme = st.session_state.show_cme
        show_sunspot = st.session_state.show_sunspot
        show_flares = st.session_state.show_flares
        show_coronal_holes = st.session_state.show_coronal_holes

        # Logout button
        if st.button("Logout"):
            st.session_state.admin_authenticated = False
            st.rerun()

# Calculate date range based on days_to_show and admin_selected_date if set
if st.session_state.admin_selected_date is not None:
    # Use the admin selected date as the center date
    center_date = datetime.strptime(st.session_state.admin_selected_date, "%Y-%m-%d")
    # Make sure center_date is not in the future
    today = datetime.now()
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
else:
    # Use today as the end date
    end_date = datetime.now()
    # Calculate start date based on days_to_show
    start_date = end_date - timedelta(days=days_to_show - 1)  # -1 because we want to include the end date

# Display date range in the main area instead of sidebar
st.markdown(f"**Date Range:** {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")

# Initialize category filter variables
if "show_cme" not in st.session_state:
    st.session_state.show_cme = True
if "show_sunspot" not in st.session_state:
    st.session_state.show_sunspot = True
if "show_flares" not in st.session_state:
    st.session_state.show_flares = True
if "show_coronal_holes" not in st.session_state:
    st.session_state.show_coronal_holes = True

# Initialize show_significant_only variable (hidden feature, no longer in sidebar)
show_significant_only = st.session_state.get("show_significant_only", False)

# Set local variables from session state
show_cme = st.session_state.show_cme
show_sunspot = st.session_state.show_sunspot
show_flares = st.session_state.show_flares
show_coronal_holes = st.session_state.show_coronal_holes

# Process data for selected date range
@st.cache_data(ttl=3600)  # Cache for 1 hour
def load_timeline_data(force_refresh=False):
    """Load timeline data, using cached data when available

    Args:
        force_refresh (bool): Whether to force refresh the data even if it exists

    Returns:
        list: Filtered data for the selected date range
    """
    # Use the global days_to_show variable and admin_selected_date if set
    if st.session_state.admin_selected_date is not None:
        # Calculate a custom date range based on admin_selected_date and days_to_show
        center_date = datetime.strptime(st.session_state.admin_selected_date, "%Y-%m-%d")
        # Make sure center_date is not in the future
        today = datetime.now()
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

        # Generate date range
        date_range = []
        current_date = start_date
        while current_date <= end_date:
            date_range.append(current_date.strftime("%Y-%m-%d"))
            current_date += timedelta(days=1)
    else:
        # Use the standard get_date_range function
        date_range = get_date_range(days=days_to_show)

    # Check if we need to process any dates
    existing_data = get_all_data_from_db()
    existing_dates = [data.get("date") for data in existing_data]

    # Identify which dates need to be processed
    dates_to_process = [date for date in date_range if date not in existing_dates]
    dates_from_cache = [date for date in date_range if date in existing_dates]

    # Check for empty data structures (those with no events or error messages)
    dates_with_empty_data = []
    for data in existing_data:
        if data.get("date") in date_range:
            events = data.get("events", {})
            total_events = sum(len(events.get(cat, [])) for cat in ["cme", "sunspot", "flares", "coronal_holes"])
            if total_events == 0 or "error" in data:
                dates_with_empty_data.append(data.get("date"))

    # Add dates with empty data to the dates to process if not already forcing a refresh
    if dates_with_empty_data and not force_refresh:
        logger.info(f"Found {len(dates_with_empty_data)} dates with empty data. Will try to refresh them.")
        for date in dates_with_empty_data:
            if date not in dates_to_process:
                dates_to_process.append(date)

    # Process new dates if needed
    if dates_to_process or force_refresh:
        with st.spinner(f"Processing {len(dates_to_process) if not force_refresh else len(date_range)} dates..."):
            if force_refresh:
                # Process all dates with force_refresh=True
                for date in date_range:
                    process_date(date, force_refresh=True)
            else:
                # Process only new dates and dates with empty data
                for date in dates_to_process:
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
if "check_empty_data" not in st.session_state:
    st.session_state.check_empty_data = True

# Load data with auto-refresh for empty data on first load
if st.session_state.check_empty_data:
    with st.spinner("Checking for empty data and refreshing if needed..."):
        # Clear the cache to force a refresh of the data
        st.cache_data.clear()
        timeline_data = load_timeline_data(force_refresh=False)
    # Set the flag to false so we don't check on every rerun
    st.session_state.check_empty_data = False
    logger.info("Refreshed data with check_empty_data=True")
else:
    timeline_data = load_timeline_data(force_refresh=False)
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

# Get event counts and significant events
event_counts = count_events_by_category(timeline_data)
significant_events = get_significant_events(timeline_data)

# Create fallback data for empty dates
# Use the same date range logic as in load_timeline_data
if st.session_state.admin_selected_date is not None:
    # Calculate a custom date range based on admin_selected_date and days_to_show
    center_date = datetime.strptime(st.session_state.admin_selected_date, "%Y-%m-%d")
    # Make sure center_date is not in the future
    today = datetime.now()
    if center_date > today:
        center_date = today

    # Calculate half the days to show on each side of the center date
    half_days = days_to_show // 2

    # Calculate start and end dates centered around the selected date
    start_date_obj = center_date - timedelta(days=half_days)
    end_date_obj = center_date + timedelta(days=half_days)

    # Adjust if end_date is in the future
    if end_date_obj > today:
        end_date_obj = today
        # Shift start date to maintain the requested number of days if possible
        start_date_obj = end_date_obj - timedelta(days=days_to_show - 1)  # -1 because we want to include the end date

    # Generate date range
    date_range = []
    current_date = start_date_obj
    while current_date <= end_date_obj:
        date_range.append(current_date.strftime("%Y-%m-%d"))
        current_date += timedelta(days=1)
else:
    # Use the standard get_date_range function
    date_range = get_date_range(days=days_to_show)
for date in date_range:
    if date not in event_counts:
        # Add an empty entry for this date
        event_counts[date] = {
            "cme": 0,
            "sunspot": 0,
            "flares": 0,
            "coronal_holes": 0,
            "total": 0
        }
        logger.info(f"Added fallback empty data for date {date}")

# Ensure the selected date is in the current date range
# If not, set it to today's date or the most recent date in the range
if st.session_state.selected_date not in date_range:
    today = datetime.now().strftime("%Y-%m-%d")
    if today in date_range:
        st.session_state.selected_date = today
    else:
        # Use the most recent date in the range
        st.session_state.selected_date = sorted(date_range)[-1]

# Create timeline visualization
st.header("Timeline of Space Weather Events")

# Convert to DataFrame for plotting
if event_counts:
    # Log the event counts for debugging
    logger.info(f"Event counts: {len(event_counts)} dates with data")
    for date, counts in event_counts.items():
        if counts["total"] > 0:
            logger.debug(f"Date {date} has {counts['total']} events")

    # Create a list of dictionaries for the DataFrame
    data_list = []
    for date, counts in event_counts.items():
        # Get the number of significant events for this date
        sig_count = significant_events.get(date, 0)

        # Calculate weighted values for each category based on significance
        # For each category, we need to determine how many of its events are significant
        # This requires looking at the original data
        date_data = next((data for data in timeline_data if data.get("date") == date), None)

        # Initialize weighted counts
        weighted_cme = counts["cme"]
        weighted_sunspot = counts["sunspot"]
        weighted_flares = counts["flares"]
        weighted_coronal_holes = counts["coronal_holes"]

        # If we have data for this date, calculate weighted values
        if date_data and "events" in date_data:
            events = date_data.get("events", {})

            # Count significant events in each category and add extra weight
            sig_cme = sum(1 for event in events.get("cme", []) if event.get("tone") == "Significant")
            sig_sunspot = sum(1 for event in events.get("sunspot", []) if event.get("tone") == "Significant")
            sig_flares = sum(1 for event in events.get("flares", []) if event.get("tone") == "Significant")
            sig_coronal_holes = sum(1 for event in events.get("coronal_holes", []) if event.get("tone") == "Significant")

            # Add extra weight for significant events (making them count 3x)
            weighted_cme = counts["cme"] + (sig_cme * 2)  # 1x normal + 2x extra for significant = 3x total
            weighted_sunspot = counts["sunspot"] + (sig_sunspot * 2)
            weighted_flares = counts["flares"] + (sig_flares * 2)
            weighted_coronal_holes = counts["coronal_holes"] + (sig_coronal_holes * 2)

            # Store the significant counts for hover information
            sig_cme_count = sig_cme
            sig_sunspot_count = sig_sunspot
            sig_flares_count = sig_flares
            sig_coronal_holes_count = sig_coronal_holes

        # Create the data entry
        data_list.append({
            "date": date,
            "cme": counts["cme"],
            "sunspot": counts["sunspot"],
            "flares": counts["flares"],
            "coronal_holes": counts["coronal_holes"],
            "weighted_cme": weighted_cme,
            "weighted_sunspot": weighted_sunspot,
            "weighted_flares": weighted_flares,
            "weighted_coronal_holes": weighted_coronal_holes,
            "sig_cme": sig_cme_count if 'sig_cme_count' in locals() else 0,
            "sig_sunspot": sig_sunspot_count if 'sig_sunspot_count' in locals() else 0,
            "sig_flares": sig_flares_count if 'sig_flares_count' in locals() else 0,
            "sig_coronal_holes": sig_coronal_holes_count if 'sig_coronal_holes_count' in locals() else 0,
            "total": counts["total"],
            "significant": sig_count
        })

    # Create the DataFrame
    if data_list:
        timeline_df = pd.DataFrame(data_list).sort_values("date")
        logger.info(f"Created DataFrame with {len(timeline_df)} rows")
    else:
        timeline_df = pd.DataFrame(columns=["date", "cme", "sunspot", "flares", "coronal_holes", "total", "significant"])
        logger.warning("No data list created from event counts")
else:
    timeline_df = pd.DataFrame(columns=["date", "cme", "sunspot", "flares", "coronal_holes", "total", "significant"])
    logger.warning("No event counts available")

# Create a color scale for significant events
max_significant = timeline_df["significant"].max() if not timeline_df.empty and timeline_df["significant"].max() > 0 else 1
timeline_df["color"] = timeline_df["significant"].apply(lambda x: f"rgba(255, 75, 75, {min(0.3 + (x / max_significant * 0.7), 1)})" if x > 0 else "rgba(100, 149, 237, 0.7)")


# Create the timeline visualization with Plotly
if not timeline_df.empty:
    fig = go.Figure()

    # Add bars for each category if selected, using weighted values
    if show_cme:
        fig.add_trace(go.Bar(
            x=timeline_df["date"],
            y=timeline_df["weighted_cme"],
            name="CME",
            marker_color="rgba(255, 165, 0, 0.7)",
            hovertemplate="<b>CME</b><br>Date: %{x}<br>Count: %{customdata[0]}<br>Significant: %{customdata[1]}<br>Weight: %{y} (3x for significant)<extra></extra>",
            customdata=timeline_df[["cme", "sig_cme"]].values
        ))

    if show_sunspot:
        fig.add_trace(go.Bar(
            x=timeline_df["date"],
            y=timeline_df["weighted_sunspot"],
            name="Sunspots",
            marker_color="rgba(255, 215, 0, 0.7)",
            hovertemplate="<b>Sunspots</b><br>Date: %{x}<br>Count: %{customdata[0]}<br>Significant: %{customdata[1]}<br>Weight: %{y} (3x for significant)<extra></extra>",
            customdata=timeline_df[["sunspot", "sig_sunspot"]].values
        ))

    if show_flares:
        fig.add_trace(go.Bar(
            x=timeline_df["date"],
            y=timeline_df["weighted_flares"],
            name="Solar Flares",
            marker_color="rgba(255, 69, 0, 0.7)",
            hovertemplate="<b>Solar Flares</b><br>Date: %{x}<br>Count: %{customdata[0]}<br>Significant: %{customdata[1]}<br>Weight: %{y} (3x for significant)<extra></extra>",
            customdata=timeline_df[["flares", "sig_flares"]].values
        ))

    if show_coronal_holes:
        fig.add_trace(go.Bar(
            x=timeline_df["date"],
            y=timeline_df["weighted_coronal_holes"],
            name="Coronal Holes",
            marker_color="rgba(75, 0, 130, 0.7)",
            hovertemplate="<b>Coronal Holes</b><br>Date: %{x}<br>Count: %{customdata[0]}<br>Significant: %{customdata[1]}<br>Weight: %{y} (3x for significant)<extra></extra>",
            customdata=timeline_df[["coronal_holes", "sig_coronal_holes"]].values
        ))

    # No need for separate markers for significant events as they're now represented by taller bars

    # Update layout
    fig.update_layout(
        title="Space Weather Events Timeline",
        xaxis_title="Date",
        yaxis_title="Event Significance",
        barmode="stack",
        hovermode="x unified",
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        margin=dict(l=20, r=20, t=60, b=20),
        height=400
    )

    # Display the timeline
    st.plotly_chart(fig, use_container_width=True)

    # No need for pulsing animation since we've removed the star icons
else:
    st.info("No data available for the timeline. Try refreshing the data or selecting a different date range.")

# Add date selector
st.markdown("### 📅 Select a date to view details")

# Create a row of date buttons
# Use session state for selected_date instead of a local variable

# Only create columns if there's data
if not timeline_df.empty:
    cols = st.columns(min(10, len(timeline_df)))
else:
    st.info("No data available for date selection. Try refreshing the data or selecting a different date range.")

# Create date buttons in groups of 10
if not timeline_df.empty:
    date_groups = [timeline_df["date"].tolist()[i:i+10] for i in range(0, len(timeline_df), 10)]

    # Add a selector for date groups if there are multiple groups
    if len(date_groups) > 1:
        group_index = st.select_slider("Date Group", options=range(len(date_groups)),
                                      format_func=lambda i: f"{date_groups[i][0]} to {date_groups[i][-1]}")
        current_group = date_groups[group_index]
    else:
        current_group = date_groups[0] if date_groups else []
else:
    st.warning("No data available for the selected date range. Try refreshing the data or selecting a different date range.")
    current_group = []

# Display the current group of dates as buttons
if current_group:
    cols = st.columns(len(current_group))
    for i, date in enumerate(current_group):
        is_significant = date in significant_events
        date_display = date.split("-")[2]  # Just show the day

        with cols[i]:
            # Apply custom class to significant date buttons
            # Check if this date is the currently selected date
            is_selected = date == st.session_state.selected_date
            button_label = f"**{date_display}**" if is_significant else date_display

            # Add a visual indicator for the selected date
            if is_selected:
                button_label = f"🔍 {button_label}"

            if st.button(
                button_label,
                key=f"date_{date}",
                help=f"{date}: {event_counts.get(date, {}).get('total', 0)} events, {significant_events.get(date, 0)} significant"
            ):
                st.session_state.selected_date = date
                # Rerun the app to update the UI immediately
                st.rerun()

            # Add custom styling to significant date buttons using JavaScript
            js_code = """
            <script>
                document.querySelector('[data-testid="stButton"][key="date_{date}"] button').classList.add('{css_class}');
            </script>
            """

            if is_significant:
                st.markdown(js_code.format(date=date, css_class="significant-date-btn"), unsafe_allow_html=True)

            # Add selected styling if this is the selected date
            if is_selected:
                st.markdown(js_code.format(date=date, css_class="selected-date-btn"), unsafe_allow_html=True)

# Display events for selected date (using session state)
if st.session_state.selected_date:
    st.markdown(f"## Events on {st.session_state.selected_date}")

    # Find the data for the selected date
    selected_data = next((data for data in timeline_data if data.get("date") == st.session_state.selected_date), None)

    if selected_data:
        # Display the events
        events = selected_data.get("events", {})

        # Create tabs for each category
        tab1, tab2, tab3, tab4 = st.tabs(["CME", "Sunspots", "Solar Flares", "Coronal Holes"])

        with tab1:
            if show_cme:
                cme_events = events.get("cme", [])
                if cme_events:
                    for event in cme_events:
                        if show_significant_only and event.get("tone") != "Significant":
                            continue

                        # Get the event details
                        detail = event.get('detail', 'No details available')
                        # Ensure we have a string and unescape any HTML entities
                        detail = html.unescape(detail) if detail else 'No details available'

                        # Create the card header and metadata
                        card_html = f"""
                        <div class="event-card {'significant' if event.get('tone') == 'Significant' else ''}">
                            <h4>{'🚨 ' if event.get('tone') == 'Significant' else ''}Coronal Mass Ejection</h4>
                            <p><strong>Tone:</strong> {event.get('tone', 'Unknown')}</p>
                            <p><strong>Date:</strong> {event.get('date', 'Unknown')}</p>
                            {f"<p><strong>Predicted Arrival:</strong> {event.get('predicted_arrival')}</p>" if event.get('predicted_arrival') else ""}
                        """

                        # Render the card header
                        st.markdown(card_html, unsafe_allow_html=True)

                        # Render the details section separately
                        st.markdown(f"<div class='event-card-details'><p><strong>Details:</strong></p>{detail}</div>", unsafe_allow_html=True)

                        # Render the image if available
                        if event.get('image_url'):
                            st.markdown(f"<div class='event-card-image'><img src='{event.get('image_url')}' width='100%' /></div>", unsafe_allow_html=True)

                        # Close the card
                        st.markdown("</div>", unsafe_allow_html=True)
                else:
                    st.info("No CME events recorded for this date.")
            else:
                st.info("CME events are filtered out.")

        with tab2:
            if show_sunspot:
                sunspot_events = events.get("sunspot", [])
                if sunspot_events:
                    for event in sunspot_events:
                        if show_significant_only and event.get("tone") != "Significant":
                            continue

                        # Get the event details
                        detail = event.get('detail', 'No details available')
                        # Ensure we have a string and unescape any HTML entities
                        detail = html.unescape(detail) if detail else 'No details available'

                        # Create the card header and metadata
                        card_html = f"""
                        <div class="event-card {'significant' if event.get('tone') == 'Significant' else ''}">
                            <h4>{'🚨 ' if event.get('tone') == 'Significant' else ''}Sunspot Activity</h4>
                            <p><strong>Tone:</strong> {event.get('tone', 'Unknown')}</p>
                            <p><strong>Date:</strong> {event.get('date', 'Unknown')}</p>
                        """

                        # Render the card header
                        st.markdown(card_html, unsafe_allow_html=True)

                        # Render the details section separately
                        st.markdown(f"<div class='event-card-details'><p><strong>Details:</strong></p>{detail}</div>", unsafe_allow_html=True)

                        # Render the image if available
                        if event.get('image_url'):
                            st.markdown(f"<div class='event-card-image'><img src='{event.get('image_url')}' width='100%' /></div>", unsafe_allow_html=True)

                        # Close the card
                        st.markdown("</div>", unsafe_allow_html=True)
                else:
                    st.info("No sunspot events recorded for this date.")
            else:
                st.info("Sunspot events are filtered out.")

        with tab3:
            if show_flares:
                flare_events = events.get("flares", [])
                if flare_events:
                    for event in flare_events:
                        if show_significant_only and event.get("tone") != "Significant":
                            continue

                        # Get the event details
                        detail = event.get('detail', 'No details available')
                        # Ensure we have a string and unescape any HTML entities
                        detail = html.unescape(detail) if detail else 'No details available'

                        # Create the card header and metadata
                        card_html = f"""
                        <div class="event-card {'significant' if event.get('tone') == 'Significant' else ''}">
                            <h4>{'🚨 ' if event.get('tone') == 'Significant' else ''}Solar Flare</h4>
                            <p><strong>Tone:</strong> {event.get('tone', 'Unknown')}</p>
                            <p><strong>Date:</strong> {event.get('date', 'Unknown')}</p>
                        """

                        # Render the card header
                        st.markdown(card_html, unsafe_allow_html=True)

                        # Render the details section separately
                        st.markdown(f"<div class='event-card-details'><p><strong>Details:</strong></p>{detail}</div>", unsafe_allow_html=True)

                        # Render the image if available
                        if event.get('image_url'):
                            st.markdown(f"<div class='event-card-image'><img src='{event.get('image_url')}' width='100%' /></div>", unsafe_allow_html=True)

                        # Close the card
                        st.markdown("</div>", unsafe_allow_html=True)
                else:
                    st.info("No solar flare events recorded for this date.")
            else:
                st.info("Solar flare events are filtered out.")

        with tab4:
            if show_coronal_holes:
                ch_events = events.get("coronal_holes", [])
                if ch_events:
                    for event in ch_events:
                        if show_significant_only and event.get("tone") != "Significant":
                            continue

                        # Get the event details
                        detail = event.get('detail', 'No details available')
                        # Ensure we have a string and unescape any HTML entities
                        detail = html.unescape(detail) if detail else 'No details available'

                        # Create the card header and metadata
                        card_html = f"""
                        <div class="event-card {'significant' if event.get('tone') == 'Significant' else ''}">
                            <h4>{'🚨 ' if event.get('tone') == 'Significant' else ''}Coronal Hole</h4>
                            <p><strong>Tone:</strong> {event.get('tone', 'Unknown')}</p>
                            <p><strong>Date:</strong> {event.get('date', 'Unknown')}</p>
                            {f"<p><strong>Predicted Arrival:</strong> {event.get('predicted_arrival')}</p>" if event.get('predicted_arrival') else ""}
                        """

                        # Render the card header
                        st.markdown(card_html, unsafe_allow_html=True)

                        # Render the details section separately
                        st.markdown(f"<div class='event-card-details'><p><strong>Details:</strong></p>{detail}</div>", unsafe_allow_html=True)

                        # Render the image if available
                        if event.get('image_url'):
                            st.markdown(f"<div class='event-card-image'><img src='{event.get('image_url')}' width='100%' /></div>", unsafe_allow_html=True)

                        # Close the card
                        st.markdown("</div>", unsafe_allow_html=True)
                else:
                    st.info("No coronal hole events recorded for this date.")
            else:
                st.info("Coronal hole events are filtered out.")

        # Link to original source
        st.markdown(f"[View original source]({selected_data.get('url', 'https://spaceweather.com')})")
    else:
        st.warning("No data available for the selected date.")

# Add a dedicated section for significant events if there are any
if not timeline_df.empty and timeline_df["significant"].sum() > 0:
    # Count the total number of significant events
    total_significant = timeline_df["significant"].sum()

    # Create a collapsible section that's collapsed by default
    with st.expander(f"🚨 Significant Events ({int(total_significant)})", expanded=False):
        # Collect all significant events from the timeline data
        for data in timeline_data:
            date = data.get("date")
            events = data.get("events", {})

            for category, category_events in events.items():
                for event in category_events:
                    if event.get("tone") == "Significant":
                        # Get the event details
                        detail = event.get('detail', 'No details available')
                        # Ensure we have a string and unescape any HTML entities
                        detail = html.unescape(detail) if detail else 'No details available'

                        # Create the card header
                        card_html = f"""
                        <div class="event-card significant">
                            <h4>🚨 Significant {category.upper()} Event on {date}</h4>
                        """

                        # Render the card header
                        st.markdown(card_html, unsafe_allow_html=True)

                        # Render the details section separately
                        st.markdown(f"<div class='event-card-details'><p><strong>Details:</strong></p>{detail}</div>", unsafe_allow_html=True)

                        # Render the image if available
                        if event.get('image_url'):
                            st.markdown(f"<div class='event-card-image'><img src='{event.get('image_url')}' width='100%' /></div>", unsafe_allow_html=True)

                        # Close the card
                        st.markdown("</div>", unsafe_allow_html=True)

    # Add a separator
    st.markdown("---")

# Add statistics section
st.header("📊 Space Weather Statistics")

if not timeline_df.empty:
    # Create two columns for statistics
    col1, col2 = st.columns(2)

    with col1:
        # Total events by category
        st.subheader("Events by Category")

        category_totals = {
            "CME": timeline_df["cme"].sum(),
            "Sunspots": timeline_df["sunspot"].sum(),
            "Solar Flares": timeline_df["flares"].sum(),
            "Coronal Holes": timeline_df["coronal_holes"].sum()
        }

        # Only create pie chart if there's data
        if sum(category_totals.values()) > 0:
            fig_pie = px.pie(
                values=list(category_totals.values()),
                names=list(category_totals.keys()),
                title="Distribution of Events",
                color_discrete_sequence=px.colors.sequential.Plasma_r
            )

            st.plotly_chart(fig_pie, use_container_width=True)
        else:
            st.info("No events data available for the selected date range.")

    with col2:
        # Significant events over time
        st.subheader("Significant Events Over Time")

        # Only create line chart if there's data
        if timeline_df["significant"].sum() > 0:
            fig_line = px.line(
                timeline_df,
                x="date",
                y="significant",
                markers=True,
                title="Significant Events by Date",
                color_discrete_sequence=["red"]
            )

            fig_line.update_layout(
                xaxis_title="Date",
                yaxis_title="Number of Significant Events"
            )

            st.plotly_chart(fig_line, use_container_width=True)
        else:
            st.info("No significant events data available for the selected date range.")
else:
    st.info("No data available for statistics. Try refreshing the data or selecting a different date range.")

# Footer
st.markdown("---")
st.markdown("Data source: [spaceweather.com](https://spaceweather.com)")

# Display current LLM provider and model
if "llm_provider" in st.session_state and "llm_model" in st.session_state:
    provider = st.session_state.llm_provider
    model_name = st.session_state.llm_model
else:
    provider = st.secrets.get("LLM_PROVIDER", "grok")
    model_name = st.secrets.get("LLM_MODEL", "grok-3-mini-beta")

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
    """)

# Run the app
if __name__ == "__main__":
    # This code is executed when the script is run directly
    pass
