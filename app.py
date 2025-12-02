"""
Streamlit GMR Analysis Tool
Upload and analyze Global Movement Records (GMR) data for zone conversion and customer flow analysis.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from analysis import (
    calculate_conversion_rates,
    calculate_zone_frequency,
    calculate_missing_zone1_percentage,
    get_summary_statistics,
    calculate_records_distribution,
    calculate_enter_exit_analysis,
    get_group_size_histogram_data
)

# Page configuration
st.set_page_config(
    page_title="GMR Analysis Tool",
    page_icon="📊",
    layout="wide"
)

# Title and description
st.title("GMR Analysis Tool")
st.markdown("""
Upload your Global Movement Records (GMR) CSV file to analyze customer zone movements and conversions.
The tool provides comprehensive analysis of entrance patterns, zone conversions, and customer flow metrics.
""")

# File uploader
uploaded_file = st.file_uploader(
    "Upload your GMR CSV file",
    type=['csv'],
    help="Upload a CSV file containing GMR data with columns: global_object_id, zone_id, zone_entry_time, zone_exit_time, dwell_time"
)

if uploaded_file is not None:
    try:
        # Load the data
        df = pd.read_csv(uploaded_file)
        
        # Validate required columns
        required_columns = ['global_object_id', 'zone_id', 'zone_entry_time', 'zone_exit_time', 'dwell_time']
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        if missing_columns:
            st.error(f"Missing required columns: {', '.join(missing_columns)}")
            st.info(f"Available columns: {', '.join(df.columns)}")
            st.stop()
        
        # Show success message
        st.success(f"Successfully loaded {len(df)} records")
        
        # Summary statistics section
        st.header("Summary Statistics")
        stats = get_summary_statistics(df)
        
        col1, col2, col3, col4, col5 = st.columns(5)
        with col1:
            st.metric("Total Records", f"{stats['total_records']:,}")
        with col2:
            st.metric("Unique Objects", f"{stats['unique_objects']:,}")
        with col3:
            st.metric("Unique Property Enter", f"{stats['unique_property_enter']:,}")
        with col4:
            st.metric("Zones", f"{stats['unique_zones']:,}")
        with col5:
            if stats['date_range']:
                date_str = f"{stats['date_range'][0].strftime('%Y-%m-%d')}"
                st.metric("Date", date_str)
            else:
                st.metric("Date", "N/A")
        
        # Data preview section (expandable)
        with st.expander("Data Preview (First 10 rows)"):
            st.dataframe(df.head(10), use_container_width=True)
        
        st.divider()
        
        # Analysis Section 1: Conversion from Zone 1 to other zones
        st.header("1. Unique Conversion from Entrance (Zone 1) to Other Zones")
        st.markdown("""
        This table shows the number of people who visited **both Zone 1 (entrance) and each specific zone**.
        Only counts customers who started their journey from the entrance.
        """)
        
        conversion_df = calculate_conversion_rates(df)
        
        if len(conversion_df) > 0:
            col1, col2 = st.columns([0.6, 2.4])
            
            with col1:
                # Add custom CSS for center alignment and compact spacing
                st.markdown("""
                    <style>
                    [data-testid="stDataFrame"] {
                        text-align: center;
                    }
                    [data-testid="stDataFrame"] td, [data-testid="stDataFrame"] th {
                        text-align: center !important;
                    }
                    </style>
                """, unsafe_allow_html=True)
                
                st.dataframe(
                    conversion_df,
                    use_container_width=True,
                    height=280,
                    hide_index=True
                )
            
            with col2:
                # Create bar chart for conversions
                fig = px.bar(
                    conversion_df,
                    x='Zone ID',
                    y='Unique Conversion Count',
                    title='Unique Conversion Counts by Zone',
                    labels={'Unique Conversion Count': 'Number of People', 'Zone ID': 'Zone ID'},
                    color='Unique Conversion Count',
                    color_continuous_scale='Blues'
                )
                fig.update_layout(
                    xaxis_type='category',
                    showlegend=False,
                    height=280,
                    margin=dict(t=50, b=50, l=50, r=50)
                )
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("No conversion data available.")
        
        st.divider()
        
        # Analysis Section 2: Zone frequency analysis
        st.header("2. Zone Analysis: Number of Zones Visited")
        st.markdown("""
        This shows how many people visited different numbers of zones (including Zone 1).
        Only includes customers who entered through Zone 1.
        - **1+**: People who visited at least 1 zone
        - **2+**: People who visited at least 2 zones
        - **3+**: People who visited at least 3 zones, etc.
        """)
        
        frequency_df = calculate_zone_frequency(df)
        
        if len(frequency_df) > 0:
            col1, col2 = st.columns([0.6, 2.4])
            
            with col1:
                st.dataframe(
                    frequency_df,
                    use_container_width=True,
                    height=280,
                    hide_index=True
                )
            
            with col2:
                # Create bar chart for zone frequency
                fig = px.bar(
                    frequency_df,
                    x='Number of Zones',
                    y='Count',
                    title='Number of People by Zones Visited',
                    labels={'Count': 'Number of People', 'Number of Zones': 'Zones Visited'},
                    color='Count',
                    color_continuous_scale='Greens'
                )
                fig.update_layout(
                    showlegend=False,
                    height=280,
                    margin=dict(t=50, b=50, l=50, r=50)
                )
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("No zone frequency data available.")
        
        st.divider()
        
        # Analysis Section 3: Missing Zone 1 analysis
        st.header("3. Percentage of Customers with Missing Zone 1 (Entrance)")
        st.markdown("""
        This metric shows the percentage of unique customers whose journey did not include Zone 1.
        These customers appeared directly in the middle of the store without passing through the entrance zone.
        """)
        
        percentage, missing_count, total_people = calculate_missing_zone1_percentage(df)
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric(
                "Missing Zone 1",
                f"{percentage:.2f}%",
                delta=None,
                help="Percentage of unique customers who never visited Zone 1"
            )
        with col2:
            st.metric(
                "People Without Zone 1",
                f"{missing_count:,}",
                help="Number of unique customers who never visited Zone 1"
            )
        with col3:
            st.metric(
                "Total Unique Objects",
                f"{total_people:,}",
                help="Total number of unique customers in the dataset"
            )
        
        # Visual representation
        fig = go.Figure(data=[go.Pie(
            labels=['With Zone 1', 'Without Zone 1'],
            values=[total_people - missing_count, missing_count],
            marker=dict(colors=['#00cc96', '#ef553b']),
            hole=.3
        )])
        fig.update_layout(
            title='Distribution of Customers by Zone 1 Visit',
            height=400
        )
        st.plotly_chart(fig, use_container_width=True)
        
        st.divider()
        
        # Analysis Section 4: Records Distribution per Object
        st.header("4. Distribution of Records per Object")
        st.markdown("""
        This analysis shows how many zone records each unique object has in the dataset.
        Objects with more records indicate longer customer journeys through multiple zones.
        """)
        
        distribution_df, dist_stats = calculate_records_distribution(df)
        
        col1, col2 = st.columns([1.2, 1.8])
        
        with col1:
            # Display statistics
            st.subheader("Statistics")
            metric_col1, metric_col2 = st.columns(2)
            with metric_col1:
                st.metric("Mean", f"{dist_stats['mean']:.2f}")
                st.metric("Min", f"{dist_stats['min']}")
                st.metric("Std Dev", f"{dist_stats['std']:.2f}")
            with metric_col2:
                st.metric("Median", f"{dist_stats['median']:.2f}")
                st.metric("Max", f"{dist_stats['max']}")
            
            st.write("")  # Spacing
            
            # Display distribution table
            st.dataframe(
                distribution_df.style.format({
                    'Number of Objects': '{:,}',
                    'Percentage': '{:.2f}%'
                }),
                use_container_width=True,
                hide_index=True,
                height=250
            )
        
        with col2:
            # Create pie chart for distribution
            fig = go.Figure(data=[go.Pie(
                labels=distribution_df['Records per Object'],
                values=distribution_df['Number of Objects'],
                hole=.3,
                marker=dict(colors=px.colors.qualitative.Set3)
            )])
            fig.update_layout(
                title='Objects by Record Count Categories',
                height=400
            )
            st.plotly_chart(fig, use_container_width=True)
        
        # Histogram visualization
        st.subheader("Detailed Histogram: Records per Object (1-50)")
        hist_data = get_group_size_histogram_data(df, max_value=50)
        
        if len(hist_data) > 0:
            fig = px.bar(
                hist_data,
                x='Records',
                y='Frequency',
                title='Frequency Distribution of Records per Object',
                labels={'Frequency': 'Number of Objects', 'Records': 'Number of Records per Object'},
                color='Frequency',
                color_continuous_scale='Viridis'
            )
            fig.update_layout(
                showlegend=False,
                height=400,
                xaxis_type='category'
            )
            st.plotly_chart(fig, use_container_width=True)
        
        st.divider()
        
        # Analysis Section 5: Enter/Exit Analysis
        st.header("5. Enter and Exit Status Analysis")
        st.markdown("""
        This section analyzes records based on whether they have both enter and exit times, or only enter time.
        Records with exit time = -1 indicate the object is still in the zone or the exit was not captured.
        """)
        
        enter_exit_df, enter_exit_summary = calculate_enter_exit_analysis(df)
        
        # Overall summary metrics
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Records", f"{enter_exit_summary['total_records']:,}")
        with col2:
            st.metric(
                "With Exit", 
                f"{enter_exit_summary['with_exit']:,}",
                help="Records that have both enter and exit times"
            )
        with col3:
            st.metric(
                "Without Exit", 
                f"{enter_exit_summary['without_exit']:,}",
                help="Records with only enter time (exit = -1)"
            )
        with col4:
            st.metric(
                "Exit Rate",
                f"{enter_exit_summary['exit_percentage']:.2f}%"
            )
        
        st.write("")  # Spacing
        
        # Detailed breakdown by category
        col1, col2 = st.columns([1.2, 1.8])
        
        with col1:
            st.subheader("Breakdown by Category")
            st.dataframe(
                enter_exit_df.style.format({
                    'Total Records': '{:,}',
                    'With Exit': '{:,}',
                    'Without Exit': '{:,}',
                    'Exit %': '{:.2f}%'
                }),
                use_container_width=True,
                hide_index=True,
                height=250
            )
        
        with col2:
            # Create stacked bar chart
            fig = go.Figure(data=[
                go.Bar(
                    name='With Exit',
                    x=enter_exit_df['Records per Object'],
                    y=enter_exit_df['With Exit'],
                    marker_color='#00cc96'
                ),
                go.Bar(
                    name='Without Exit',
                    x=enter_exit_df['Records per Object'],
                    y=enter_exit_df['Without Exit'],
                    marker_color='#ef553b'
                )
            ])
            fig.update_layout(
                barmode='stack',
                title='Enter/Exit Status by Record Count Category',
                xaxis_title='Records per Object',
                yaxis_title='Number of Records',
                height=400,
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
            )
            st.plotly_chart(fig, use_container_width=True)
        
        # Create percentage comparison chart
        st.subheader("Exit Rate Comparison Across Categories")
        fig = px.bar(
            enter_exit_df,
            x='Records per Object',
            y='Exit %',
            title='Percentage of Records with Exit Time by Category',
            labels={'Exit %': 'Exit Rate (%)', 'Records per Object': 'Records per Object'},
            color='Exit %',
            color_continuous_scale='RdYlGn',
            text='Exit %'
        )
        fig.update_traces(texttemplate='%{text:.1f}%', textposition='outside')
        fig.update_layout(
            showlegend=False,
            height=500,
            margin=dict(t=80, b=50, l=50, r=50)
        )
        st.plotly_chart(fig, use_container_width=True)
        
        
    except Exception as e:
        st.error(f"Error processing file: {str(e)}")
        st.exception(e)

# Footer
st.divider()
st.markdown("""
<div style='text-align: center; color: gray; padding: 20px;'>
    <small>GMR Analysis Tool | Analyze customer zone movements and conversions</small>
</div>
""", unsafe_allow_html=True)

