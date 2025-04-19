"""
Timeline visualization components for the Space Weather Timeline app
"""
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import logging
from datetime import datetime

# Configure logging
logger = logging.getLogger(__name__)

def create_timeline_visualization(timeline_df, show_cme, show_sunspot, show_flares, show_coronal_holes):
    """
    Create the timeline visualization

    Args:
        timeline_df (pd.DataFrame): DataFrame with timeline data
        show_cme (bool): Whether to show CME events
        show_sunspot (bool): Whether to show sunspot events
        show_flares (bool): Whether to show flare events
        show_coronal_holes (bool): Whether to show coronal hole events
    """

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

        # Add forecast indicators if there are any forecast dates
        if "is_forecast" in timeline_df.columns and timeline_df["is_forecast"].any():
            # Add a vertical line at today's date to separate historical from forecast
            today = datetime.now().strftime("%Y-%m-%d")

            # Add a shape instead of vline to avoid type errors
            fig.add_shape(
                type="line",
                x0=today,
                x1=today,
                y0=0,
                y1=1,
                yref="paper",
                line=dict(color="rgba(0, 0, 0, 0.5)", width=2),  # Solid line instead of dashed
            )

            # Add annotation for today's line
            fig.add_annotation(
                x=today,
                y=1,
                yref="paper",
                text="Today",
                showarrow=False,
                xanchor="right",
                yanchor="top",
                bgcolor="rgba(255, 255, 255, 0.5)",
                bordercolor="rgba(0, 0, 0, 0.5)",
                borderwidth=1,
                borderpad=4,
                font=dict(size=10)
            )

            # Add patterns to forecast bars
            for trace in fig.data:
                # Apply pattern to all bars but make it visible only for forecast dates
                dates = timeline_df["date"].tolist()
                is_forecast = timeline_df["is_forecast"].tolist()

                # Create a list of patterns for each date
                patterns = []
                for idx in range(len(dates)):
                    if idx < len(is_forecast) and is_forecast[idx]:
                        patterns.append("/")
                    else:
                        patterns.append("")

                trace.marker.pattern = {
                    "shape": patterns,
                    "solidity": 0.5,
                    "fgopacity": 0.5
                }

        # Update layout
        fig.update_layout(
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
    else:
        st.info("No data available for the timeline. Try refreshing the data or selecting a different date range.")

def create_date_selector(timeline_df, significant_events, event_counts, days_to_show=14):
    """
    Create the date selector

    Args:
        timeline_df (pd.DataFrame): DataFrame with timeline data
        significant_events (dict): Dictionary of significant events by date
        event_counts (dict): Dictionary of event counts by date
        days_to_show (int, optional): Number of days to show in the date selector. Defaults to 14.
    """
    # Add date selector - different headings for mobile and desktop
    st.markdown("<div class='date-selector-heading desktop-date-buttons'><h3>📅 Select a date to view details</h3></div>", unsafe_allow_html=True)
    st.markdown("<div class='date-selector-heading mobile-date-selector'><h3>📅 Date Selection</h3></div>", unsafe_allow_html=True)

    if not timeline_df.empty:
        # Show up to days_to_show dates at once
        max_dates_to_show = min(days_to_show, len(timeline_df))
        date_groups = [timeline_df["date"].tolist()[0:max_dates_to_show]]

        # Use the first group of dates by default
        # No date group selector - simplified UI
        if date_groups:
            # Always use the first group of dates
            current_group = date_groups[0]

            # Add a hidden element to maintain spacing
            st.markdown('<div style="height: 0; overflow: hidden;"></div>', unsafe_allow_html=True)
        else:
            current_group = []

        # Mobile date selector (dropdown) - make it more compact
        st.markdown('<div class="mobile-date-selector date-selector date-selector-dropdown">', unsafe_allow_html=True)

        # Create a dictionary of dates with formatting for significant events
        date_options = {}
        # Use all dates from timeline_df, not just the current group
        for date in timeline_df["date"].tolist():
            is_significant = date in significant_events
            is_forecast = False
            if "is_forecast" in timeline_df.columns:
                is_forecast = timeline_df.loc[timeline_df["date"] == date, "is_forecast"].iloc[0]

            # More concise format for mobile
            date_display = f"{date.split('-')[2]} {date.split('-')[1]}/{date.split('-')[0][2:]}"
            if is_significant:
                date_display += " 🚨"
            if is_forecast:
                date_display += " 📊"

            date_options[date] = date_display

        # Create a selectbox for mobile view
        selected_date = st.selectbox(
            "Select date",
            options=list(date_options.keys()),
            format_func=lambda x: date_options[x],
            index=list(date_options.keys()).index(st.session_state.selected_date) if st.session_state.selected_date in date_options else 0
        )

        if selected_date != st.session_state.selected_date:
            st.session_state.selected_date = selected_date
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

        # Desktop date buttons - add a special class to help with CSS targeting
        st.markdown('<div class="desktop-date-buttons" id="desktop-date-section">', unsafe_allow_html=True)
        if current_group:
            cols = st.columns(len(current_group))
            for i, date in enumerate(current_group):
                is_significant = date in significant_events
                date_display = date.split("-")[2]  # Just show the day

                # Check if this date is a forecast
                is_forecast = False
                if "is_forecast" in timeline_df.columns:
                    is_forecast = timeline_df.loc[timeline_df["date"] == date, "is_forecast"].iloc[0]

                if is_forecast:
                    date_display += " 📊"

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
                        help=f"{date}: {event_counts.get(date, {}).get('total', 0)} events, {significant_events.get(date, 0)} significant" + (" (Forecast)" if is_forecast else "")
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

                    # Add forecast styling if this is a forecast date
                    if is_forecast:
                        st.markdown(js_code.format(date=date, css_class="forecast-date-btn"), unsafe_allow_html=True)

                    # Add selected styling if this is the selected date
                    if is_selected:
                        st.markdown(js_code.format(date=date, css_class="selected-date-btn"), unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
    else:
        st.warning("No data available for the selected date range. Try refreshing the data or selecting a different date range.")

def prepare_timeline_data(timeline_data, date_range, include_forecast=True):
    """
    Prepare timeline data for visualization

    Args:
        timeline_data (list): List of data for each date
        date_range (list): List of dates in the range
        include_forecast (bool): Whether to include forecast data

    Returns:
        tuple: (event_counts, significant_events, timeline_df)
    """
    from data_manager import count_events_by_category, get_significant_events, generate_forecast_data

    # Get event counts and significant events
    event_counts = count_events_by_category(timeline_data)
    significant_events = get_significant_events(timeline_data)

    # Generate forecast data if requested
    forecast_data = {}
    if include_forecast:
        forecast_data = generate_forecast_data(timeline_data, date_range)

        # Add forecast data to timeline_data
        for date, data in forecast_data.items():
            timeline_data.append(data)

        # Update event counts and significant events with forecast data
        forecast_event_counts = count_events_by_category(list(forecast_data.values()))
        event_counts.update(forecast_event_counts)

        forecast_significant_events = get_significant_events(list(forecast_data.values()))
        significant_events.update(forecast_significant_events)

    # Create fallback data for empty dates
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
        from datetime import datetime
        today = datetime.now().strftime("%Y-%m-%d")
        if today in date_range:
            st.session_state.selected_date = today
        else:
            # Use the most recent date in the range
            st.session_state.selected_date = sorted(date_range)[-1]

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

            # Initialize significant counts
            sig_cme_count = 0
            sig_sunspot_count = 0
            sig_flares_count = 0
            sig_coronal_holes_count = 0

            # Check if this is a forecast date
            is_forecast = False
            if date_data and date_data.get("is_forecast", False):
                is_forecast = True

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
                "sig_cme": sig_cme_count,
                "sig_sunspot": sig_sunspot_count,
                "sig_flares": sig_flares_count,
                "sig_coronal_holes": sig_coronal_holes_count,
                "total": counts["total"],
                "significant": sig_count,
                "is_forecast": is_forecast
            })

        # Create the DataFrame
        if data_list:
            timeline_df = pd.DataFrame(data_list).sort_values("date")
            logger.info(f"Created DataFrame with {len(timeline_df)} rows")
        else:
            timeline_df = pd.DataFrame(columns=["date", "cme", "sunspot", "flares", "coronal_holes", "total", "significant", "is_forecast"])
            logger.warning("No data list created from event counts")
    else:
        timeline_df = pd.DataFrame(columns=["date", "cme", "sunspot", "flares", "coronal_holes", "total", "significant", "is_forecast"])
        logger.warning("No event counts available")

    # Create a color scale for significant events
    max_significant = timeline_df["significant"].max() if not timeline_df.empty and timeline_df["significant"].max() > 0 else 1
    timeline_df["color"] = timeline_df["significant"].apply(lambda x: f"rgba(255, 75, 75, {min(0.3 + (x / max_significant * 0.7), 1)})" if x > 0 else "rgba(100, 149, 237, 0.7)")

    return event_counts, significant_events, timeline_df
