"""
Event display components for the Space Weather Timeline app
"""
import streamlit as st
import html

def display_events(timeline_data, show_cme, show_sunspot, show_flares, show_coronal_holes, show_significant_only):
    """
    Display events for the selected date
    
    Args:
        timeline_data (list): List of data for each date
        show_cme (bool): Whether to show CME events
        show_sunspot (bool): Whether to show sunspot events
        show_flares (bool): Whether to show flare events
        show_coronal_holes (bool): Whether to show coronal hole events
        show_significant_only (bool): Whether to show only significant events
    """
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
                display_cme_events(events, show_cme, show_significant_only)

            with tab2:
                display_sunspot_events(events, show_sunspot, show_significant_only)

            with tab3:
                display_flare_events(events, show_flares, show_significant_only)

            with tab4:
                display_coronal_hole_events(events, show_coronal_holes, show_significant_only)

            # Link to original source
            st.markdown(f"[View original source]({selected_data.get('url', 'https://spaceweather.com')})")
        else:
            st.warning("No data available for the selected date.")

def display_cme_events(events, show_cme, show_significant_only):
    """
    Display CME events
    
    Args:
        events (dict): Dictionary of events by category
        show_cme (bool): Whether to show CME events
        show_significant_only (bool): Whether to show only significant events
    """
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

def display_sunspot_events(events, show_sunspot, show_significant_only):
    """
    Display sunspot events
    
    Args:
        events (dict): Dictionary of events by category
        show_sunspot (bool): Whether to show sunspot events
        show_significant_only (bool): Whether to show only significant events
    """
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

def display_flare_events(events, show_flares, show_significant_only):
    """
    Display solar flare events
    
    Args:
        events (dict): Dictionary of events by category
        show_flares (bool): Whether to show flare events
        show_significant_only (bool): Whether to show only significant events
    """
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

def display_coronal_hole_events(events, show_coronal_holes, show_significant_only):
    """
    Display coronal hole events
    
    Args:
        events (dict): Dictionary of events by category
        show_coronal_holes (bool): Whether to show coronal hole events
        show_significant_only (bool): Whether to show only significant events
    """
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

def display_significant_events_section(timeline_data, timeline_df):
    """
    Display the significant events section
    
    Args:
        timeline_data (list): List of data for each date
        timeline_df (pd.DataFrame): DataFrame with timeline data
    """
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
