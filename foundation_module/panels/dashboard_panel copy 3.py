import streamlit as st
import plotly.express as px
import pandas as pd
from utils.statistics_utils import calculate_statistics

def show_dashboard_panel(state):
    st.header("Interactive Organizational Dashboard")
    
    if state.get('hierarchy') is None or state.get('hrp1000') is None:
        st.warning("Please build the hierarchy first in the Hierarchy panel")
        if st.button("Go to Hierarchy Panel"):
            st.session_state.panel = "Hierarchy"
            st.rerun()
        return
    
    try:
        # Calculate statistics if not already done
        if state.get('statistics') is None:
            with st.spinner("Calculating dashboard metrics..."):
                state['statistics'] = calculate_statistics(state['hrp1000'], state['hrp1001'], state['hierarchy'])
        
        # Main metrics
        st.subheader("Executive Summary")
        cols = st.columns(4)
        metrics = [
            ("Total Units", len(state['hrp1000'])),
            ("Hierarchy Depth", state['statistics']['max_depth']),
            ("Avg Children", f"{state['statistics']['avg_children']:.1f}"),
            ("Total Relationships", state['statistics']['total_relationships'])
        ]
        
        for i, (name, value) in enumerate(metrics):
            cols[i].metric(name, value)

        # ==================== Hierarchical Visualization ====================
        st.subheader("Hierarchy Explorer")
        
        # Prepare filtered data - clean and deduplicate
        filtered_data = state['hierarchy']['hierarchy_table'].copy()
        
        # Apply level names if available
        if 'level_names' in state:
            filtered_data['Level'] = filtered_data['Level'].map(state['level_names'])
        else:
            filtered_data['Level'] = 'Level ' + filtered_data['Level'].astype(str)
        
        # Fill NA values and ensure proper types
        filtered_data['Parent Name'] = filtered_data['Parent Name'].fillna('Top Level')
        filtered_data['Name'] = filtered_data['Name'].fillna('Unnamed')
        
        # Deduplicate while keeping hierarchy structure
        filtered_data = filtered_data.drop_duplicates(subset=['Object ID', 'Level', 'Parent'], keep='first')
        
        # Level filter
        available_levels = sorted(filtered_data['Level'].unique())
        selected_levels = st.multiselect(
            "Filter by Levels",
            options=available_levels,
            default=available_levels[:5] if len(available_levels) > 5 else available_levels
        )
        
        if selected_levels:
            filtered_data = filtered_data[filtered_data['Level'].isin(selected_levels)]
        
        # Chart selection
        chart_type = st.selectbox(
            "Hierarchy Chart Type",
            ["Sunburst", "Treemap", "Icicle"],
            index=0
        )
        
        # Generate appropriate chart
        if chart_type == "Sunburst":
            fig = px.sunburst(
                filtered_data,
                path=['Level', 'Parent Name', 'Name'],
                title="Organizational Hierarchy",
                height=700
            )
        elif chart_type == "Treemap":
            fig = px.treemap(
                filtered_data,
                path=['Level', 'Parent Name', 'Name'],
                title="Organizational Structure",
                height=700
            )
        else:  # Icicle
            fig = px.icicle(
                filtered_data,
                path=['Level', 'Parent Name', 'Name'],
                title="Hierarchy Breakdown",
                height=700
            )
        
        st.plotly_chart(fig, use_container_width=True)

        # ==================== Department Distribution ====================
        if 'Department' in state['hrp1000'].columns:
            st.subheader("Department Distribution")
            dept_col1, dept_col2 = st.columns([2, 1])
            
            with dept_col1:
                dept_counts = state['hrp1000']['Department'].value_counts().reset_index()
                fig = px.bar(
                    dept_counts,
                    x='Department',
                    y='count',
                    title="Employees by Department",
                    color='Department'
                )
                st.plotly_chart(fig, use_container_width=True)
            
            with dept_col2:
                st.dataframe(
                    dept_counts,
                    use_container_width=True,
                    hide_index=True
                )
        
        # ==================== Detailed View ====================
        st.subheader("Detailed View")
        st.dataframe(
            filtered_data[['Level', 'Name', 'Parent Name']],
            use_container_width=True,
            height=400
        )
        
    except Exception as e:
        st.error(f"Error generating dashboard: {str(e)}")
        st.write("Debug Information:")
        if 'filtered_data' in locals():
            st.write("Filtered Data:")
            st.dataframe(filtered_data)