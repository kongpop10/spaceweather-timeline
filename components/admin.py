"""
Admin panel components for the Space Weather Timeline app
"""
import streamlit as st
from datetime import datetime, timedelta
import logging
from data_manager import (
    process_date_range, import_all_json_to_db, sync_with_supabase
)
from db_manager import get_all_data_from_db
from utils import get_date_range

# Configure logging
logger = logging.getLogger(__name__)

def render_admin_panel(days_to_show):
    """
    Render the admin panel

    Args:
        days_to_show (int): Current number of days to show

    Returns:
        int: Updated days_to_show value
    """
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
            days_to_show = render_llm_config()

            # Data Management
            render_data_management(days_to_show)

            # Date Display Controls
            render_date_controls(days_to_show)

            # Controls section
            days_to_show = render_controls(days_to_show)

            # Logout button
            if st.button("Logout"):
                st.session_state.admin_authenticated = False
                st.rerun()

    return days_to_show

def render_llm_config():
    """
    Render the LLM configuration section
    """
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

def render_data_management(days_to_show):
    """
    Render the data management section

    Args:
        days_to_show (int): Current number of days to show
    """
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
                                    from data_manager import process_date
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

def render_date_controls(days_to_show):
    """
    Render the date display controls section

    Args:
        days_to_show (int): Current number of days to show
    """
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

def render_controls(days_to_show):
    """
    Render the controls section

    Args:
        days_to_show (int): Current number of days to show

    Returns:
        int: Updated days_to_show value
    """
    st.subheader("📊 Controls")

    # Note: Days to display slider has been removed as requested
    # Display current days setting as information
    if st.session_state.admin_days_to_show is not None:
        st.info(f"Using admin setting: {days_to_show} days to display")

    # Category filters
    st.markdown("**Event Categories**")
    st.session_state.show_cme = st.checkbox("Coronal Mass Ejections (CME)", value=st.session_state.show_cme)
    st.session_state.show_sunspot = st.checkbox("Sunspots", value=st.session_state.show_sunspot)
    st.session_state.show_flares = st.checkbox("Solar Flares", value=st.session_state.show_flares)
    st.session_state.show_coronal_holes = st.checkbox("Coronal Holes", value=st.session_state.show_coronal_holes)

    return days_to_show
