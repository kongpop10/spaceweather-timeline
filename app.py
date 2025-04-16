"""
Streamlit app for spaceweather.com data visualization
"""
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta

from utils import get_date_range
from data_manager import process_date, process_date_range, get_significant_events, count_events_by_category, get_all_data

# Set page config
st.set_page_config(
    page_title="Space Weather Timeline",
    page_icon="☀️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .event-card {
        border: 1px solid #ddd;
        border-radius: 5px;
        padding: 10px;
        margin-bottom: 10px;
        background-color: white;
    }
    .event-card.significant {
        border-left: 5px solid #ff4b4b;
    }
    .event-card h4 {
        margin-top: 0;
    }
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
</style>
""", unsafe_allow_html=True)

# Title
st.title("☀️ Space Weather Timeline")
st.markdown("Tracking solar events from spaceweather.com")

# Sidebar
st.sidebar.header("Controls")

# Date range selection
days_to_show = st.sidebar.slider("Days to display", 1, 30, 7)
end_date = datetime.now()
start_date = end_date - timedelta(days=days_to_show)

st.sidebar.markdown(f"**Date Range:** {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")

# Category filters
st.sidebar.header("Event Categories")
show_cme = st.sidebar.checkbox("Coronal Mass Ejections (CME)", value=True)
show_sunspot = st.sidebar.checkbox("Sunspots", value=True)
show_flares = st.sidebar.checkbox("Solar Flares", value=True)
show_coronal_holes = st.sidebar.checkbox("Coronal Holes", value=True)

# Significance filter
show_significant_only = st.sidebar.checkbox("Show Significant Events Only", value=False)

# Refresh data
if st.sidebar.button("Refresh Data"):
    with st.spinner("Fetching latest data..."):
        process_date_range(
            start_date=start_date.strftime("%Y-%m-%d"),
            end_date=end_date.strftime("%Y-%m-%d")
        )
    st.sidebar.success("Data refreshed!")

# Process data for selected date range
@st.cache_data(ttl=3600)  # Cache for 1 hour
def load_timeline_data():
    # Use the global days_to_show variable
    date_range = get_date_range(days=days_to_show)

    # Check if we need to process any dates
    existing_data = get_all_data()
    existing_dates = [data.get("date") for data in existing_data]

    dates_to_process = [date for date in date_range if date not in existing_dates]

    if dates_to_process:
        with st.spinner(f"Processing {len(dates_to_process)} new dates..."):
            for date in dates_to_process:
                process_date(date)

    # Get all data again after processing
    all_data = get_all_data()

    # Filter by date range
    filtered_data = [data for data in all_data if data.get("date") in date_range]

    return filtered_data

# Load data
timeline_data = load_timeline_data()

# Get event counts and significant events
event_counts = count_events_by_category(timeline_data)
significant_events = get_significant_events(timeline_data)

# Create timeline visualization
st.header("Timeline of Space Weather Events")

# Convert to DataFrame for plotting
if event_counts:
    data_list = [
        {
            "date": date,
            "cme": counts["cme"],
            "sunspot": counts["sunspot"],
            "flares": counts["flares"],
            "coronal_holes": counts["coronal_holes"],
            "total": counts["total"],
            "significant": significant_events.get(date, 0)
        }
        for date, counts in event_counts.items()
    ]
    if data_list:
        timeline_df = pd.DataFrame(data_list).sort_values("date")
    else:
        timeline_df = pd.DataFrame(columns=["date", "cme", "sunspot", "flares", "coronal_holes", "total", "significant"])
else:
    timeline_df = pd.DataFrame(columns=["date", "cme", "sunspot", "flares", "coronal_holes", "total", "significant"])

# Create a color scale for significant events
max_significant = timeline_df["significant"].max() if not timeline_df.empty and timeline_df["significant"].max() > 0 else 1
timeline_df["color"] = timeline_df["significant"].apply(lambda x: f"rgba(255, 75, 75, {min(0.3 + (x / max_significant * 0.7), 1)})" if x > 0 else "rgba(100, 149, 237, 0.7)")

# Create the timeline visualization with Plotly
if not timeline_df.empty:
    fig = go.Figure()

    # Add bars for each category if selected
    if show_cme:
        fig.add_trace(go.Bar(
            x=timeline_df["date"],
            y=timeline_df["cme"],
            name="CME",
            marker_color="rgba(255, 165, 0, 0.7)"
        ))

    if show_sunspot:
        fig.add_trace(go.Bar(
            x=timeline_df["date"],
            y=timeline_df["sunspot"],
            name="Sunspots",
            marker_color="rgba(255, 215, 0, 0.7)"
        ))

    if show_flares:
        fig.add_trace(go.Bar(
            x=timeline_df["date"],
            y=timeline_df["flares"],
            name="Solar Flares",
            marker_color="rgba(255, 69, 0, 0.7)"
        ))

    if show_coronal_holes:
        fig.add_trace(go.Bar(
            x=timeline_df["date"],
            y=timeline_df["coronal_holes"],
            name="Coronal Holes",
            marker_color="rgba(75, 0, 130, 0.7)"
        ))

    # Add markers for significant events if there are any
    if not timeline_df[timeline_df["significant"] > 0].empty:
        fig.add_trace(go.Scatter(
            x=timeline_df[timeline_df["significant"] > 0]["date"],
            y=timeline_df[timeline_df["significant"] > 0]["total"] + 1,  # Position above the bars
            mode="markers",
            name="Significant Events",
            marker=dict(
                symbol="star",
                size=timeline_df[timeline_df["significant"] > 0]["significant"] * 10,
                color="rgba(255, 0, 0, 0.8)",
                line=dict(width=1, color="rgba(255, 255, 255, 0.8)")
            ),
            hovertemplate="Date: %{x}<br>Significant Events: %{text}<extra></extra>",
            text=timeline_df[timeline_df["significant"] > 0]["significant"]
        ))

    # Update layout
    fig.update_layout(
        title="Space Weather Events Timeline",
        xaxis_title="Date",
        yaxis_title="Number of Events",
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

# Add date selector
st.markdown("### 📅 Select a date to view details")

# Create a row of date buttons
selected_date = None

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
            if st.button(
                f"**{date_display}**" if is_significant else date_display,
                key=f"date_{date}",
                help=f"{date}: {event_counts.get(date, {}).get('total', 0)} events, {significant_events.get(date, 0)} significant"
            ):
                selected_date = date

# Display events for selected date
if selected_date:
    st.markdown(f"## Events on {selected_date}")

    # Find the data for the selected date
    selected_data = next((data for data in timeline_data if data.get("date") == selected_date), None)

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

                        st.markdown(f"""
                        <div class="event-card {'significant' if event.get('tone') == 'Significant' else ''}">
                            <h4>{'🚨 ' if event.get('tone') == 'Significant' else ''}Coronal Mass Ejection</h4>
                            <p><strong>Tone:</strong> {event.get('tone', 'Unknown')}</p>
                            <p><strong>Date:</strong> {event.get('date', 'Unknown')}</p>
                            {f"<p><strong>Predicted Arrival:</strong> {event.get('predicted_arrival')}</p>" if event.get('predicted_arrival') else ""}
                            <p><strong>Details:</strong> {event.get('detail', 'No details available')}</p>
                            {f'<img src="{event.get("image_url")}" width="100%" />' if event.get('image_url') else ""}
                        </div>
                        """, unsafe_allow_html=True)
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

                        st.markdown(f"""
                        <div class="event-card {'significant' if event.get('tone') == 'Significant' else ''}">
                            <h4>{'🚨 ' if event.get('tone') == 'Significant' else ''}Sunspot Activity</h4>
                            <p><strong>Tone:</strong> {event.get('tone', 'Unknown')}</p>
                            <p><strong>Date:</strong> {event.get('date', 'Unknown')}</p>
                            <p><strong>Details:</strong> {event.get('detail', 'No details available')}</p>
                            {f'<img src="{event.get("image_url")}" width="100%" />' if event.get('image_url') else ""}
                        </div>
                        """, unsafe_allow_html=True)
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

                        st.markdown(f"""
                        <div class="event-card {'significant' if event.get('tone') == 'Significant' else ''}">
                            <h4>{'🚨 ' if event.get('tone') == 'Significant' else ''}Solar Flare</h4>
                            <p><strong>Tone:</strong> {event.get('tone', 'Unknown')}</p>
                            <p><strong>Date:</strong> {event.get('date', 'Unknown')}</p>
                            <p><strong>Details:</strong> {event.get('detail', 'No details available')}</p>
                            {f'<img src="{event.get("image_url")}" width="100%" />' if event.get('image_url') else ""}
                        </div>
                        """, unsafe_allow_html=True)
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

                        st.markdown(f"""
                        <div class="event-card {'significant' if event.get('tone') == 'Significant' else ''}">
                            <h4>{'🚨 ' if event.get('tone') == 'Significant' else ''}Coronal Hole</h4>
                            <p><strong>Tone:</strong> {event.get('tone', 'Unknown')}</p>
                            <p><strong>Date:</strong> {event.get('date', 'Unknown')}</p>
                            {f"<p><strong>Predicted Arrival:</strong> {event.get('predicted_arrival')}</p>" if event.get('predicted_arrival') else ""}
                            <p><strong>Details:</strong> {event.get('detail', 'No details available')}</p>
                            {f'<img src="{event.get("image_url")}" width="100%" />' if event.get('image_url') else ""}
                        </div>
                        """, unsafe_allow_html=True)
                else:
                    st.info("No coronal hole events recorded for this date.")
            else:
                st.info("Coronal hole events are filtered out.")

        # Link to original source
        st.markdown(f"[View original source]({selected_data.get('url', 'https://spaceweather.com')})")
    else:
        st.warning("No data available for the selected date.")

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
st.markdown("Powered by Groq LLM (meta-llama/llama-4-maverick-17b-128e-instruct)")

# Add information about the app
with st.expander("About this app"):
    st.markdown("""
    This app scrapes data from spaceweather.com and uses the Groq LLM API to categorize space weather events into four main categories:

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
