"""
Statistics visualization components for the Space Weather Timeline app
"""
import streamlit as st
import plotly.express as px

def display_statistics(timeline_df):
    """
    Display statistics visualizations
    
    Args:
        timeline_df (pd.DataFrame): DataFrame with timeline data
    """
    st.header("📊 Space Weather Statistics")
    
    if not timeline_df.empty:
        # Create two columns for statistics
        col1, col2 = st.columns(2)
        
        with col1:
            display_category_distribution(timeline_df)
            
        with col2:
            display_significant_events_over_time(timeline_df)
    else:
        st.info("No data available for statistics. Try refreshing the data or selecting a different date range.")

def display_category_distribution(timeline_df):
    """
    Display the category distribution pie chart
    
    Args:
        timeline_df (pd.DataFrame): DataFrame with timeline data
    """
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

def display_significant_events_over_time(timeline_df):
    """
    Display the significant events over time chart
    
    Args:
        timeline_df (pd.DataFrame): DataFrame with timeline data
    """
    # Significant events over time with chart style toggle
    st.subheader("Significant Events Over Time")
    
    # Add a toggle for chart style
    chart_style = st.radio(
        "Chart Style",
        options=["Bar", "Curved"],
        horizontal=True,
        index=0,
        key="chart_style"
    )
    
    # Only create chart if there's data
    if timeline_df["significant"].sum() > 0:
        # Auto-scale y-axis for better visualization
        max_value = timeline_df["significant"].max()
        # Add a small buffer to the top of the chart (10% above max value)
        y_max = max_value * 1.1 if max_value > 0 else 1
        
        if chart_style == "Bar":
            # Create a bar chart
            fig = px.bar(
                timeline_df,
                x="date",
                y="significant",
                title="Significant Events by Date",
                color_discrete_sequence=["red"]
            )
            
            # Update layout with improved styling for bar chart
            fig.update_layout(
                xaxis_title="Date",
                yaxis_title="Number of Significant Events",
                yaxis=dict(
                    range=[0, y_max],  # Set y-axis range from 0 to max+10%
                    dtick=1 if max_value <= 5 else None  # Use integer ticks for small values
                ),
                bargap=0.2,  # Adjust gap between bars
                plot_bgcolor="rgba(0,0,0,0)",  # Transparent background
                hoverlabel=dict(bgcolor="white", font_size=12)  # Improve hover label
            )
        else:  # Curved style
            # Create a line chart with curved lines and area fill
            fig = px.area(
                timeline_df,
                x="date",
                y="significant",
                title="Significant Events by Date",
                color_discrete_sequence=["red"],
                line_shape="spline"  # Use spline for curved lines
            )
            
            # Update layout with improved styling for curved chart
            fig.update_layout(
                xaxis_title="Date",
                yaxis_title="Number of Significant Events",
                yaxis=dict(
                    range=[0, y_max],  # Set y-axis range from 0 to max+10%
                    dtick=1 if max_value <= 5 else None  # Use integer ticks for small values
                ),
                plot_bgcolor="rgba(0,0,0,0)",  # Transparent background
                hoverlabel=dict(bgcolor="white", font_size=12)  # Improve hover label
            )
            
            # Add markers to the line
            fig.update_traces(
                mode="lines+markers",
                marker=dict(size=8, color="red"),
                line=dict(width=3),
                fillcolor="rgba(255, 0, 0, 0.2)"  # Light red fill
            )
        
        # Add grid lines for better readability (common to both styles)
        fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor="rgba(211,211,211,0.3)")
        
        # Display the chart
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No significant events data available for the selected date range.")
