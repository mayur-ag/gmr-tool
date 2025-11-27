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
    get_summary_statistics
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
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Records", f"{stats['total_records']:,}")
        with col2:
            st.metric("Unique People", f"{stats['unique_people']:,}")
        with col3:
            st.metric("Unique Zones", f"{stats['unique_zones']:,}")
        with col4:
            if stats['date_range']:
                date_str = f"{stats['date_range'][0].strftime('%Y-%m-%d')} to {stats['date_range'][1].strftime('%Y-%m-%d')}"
                st.metric("Date Range", date_str)
            else:
                st.metric("Date Range", "N/A")
        
        # Data preview section (expandable)
        with st.expander("Data Preview (First 10 rows)"):
            st.dataframe(df.head(10), use_container_width=True)
        
        st.divider()
        
        # Analysis Section 1: Conversion from Zone 1 to other zones
        st.header("1. Conversion from Entrance (Zone 1) to Other Zones")
        st.markdown("""
        This table shows the number of people who visited **both Zone 1 (entrance) and each specific zone**.
        Only counts customers who started their journey from the entrance.
        """)
        
        conversion_df = calculate_conversion_rates(df)
        
        if len(conversion_df) > 0:
            col1, col2 = st.columns([1, 2])
            
            with col1:
                st.dataframe(
                    conversion_df.style.format({'Conversion Count': '{:,}'}),
                    use_container_width=True,
                    height=400
                )
            
            with col2:
                # Create bar chart for conversions
                fig = px.bar(
                    conversion_df,
                    x='Zone ID',
                    y='Conversion Count',
                    title='Conversion Counts by Zone',
                    labels={'Conversion Count': 'Number of People', 'Zone ID': 'Zone ID'},
                    color='Conversion Count',
                    color_continuous_scale='Blues'
                )
                fig.update_layout(
                    xaxis_type='category',
                    showlegend=False,
                    height=400
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
            col1, col2 = st.columns([1, 2])
            
            with col1:
                st.dataframe(
                    frequency_df.style.format({'Count': '{:,}'}),
                    use_container_width=True,
                    height=400
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
                    height=400
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
                "Total Unique People",
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
        
        # Analysis Section 4: Duplicate of Section 3 (as requested by user)
        st.header("4. Percentage of Records with Zone ID 1 Missing")
        st.markdown("""
        This is the same as Section 3 above - showing the percentage of customers whose journey 
        did not start from Zone 1 (entrance).
        """)
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric(
                "Missing Zone 1",
                f"{percentage:.2f}%"
            )
        with col2:
            st.metric(
                "People Without Zone 1",
                f"{missing_count:,}"
            )
        with col3:
            st.metric(
                "People With Zone 1",
                f"{total_people - missing_count:,}"
            )
        
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

