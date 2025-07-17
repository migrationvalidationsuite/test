import streamlit as st
import plotly.express as px
import pandas as pd

def show_dashboard_panel(state):
    st.header("Interactive Dashboard")
    
    if state.get('hierarchy') is None or state['hierarchy'].get('hierarchy_table') is None:
        st.warning("Please build the hierarchy first in the Hierarchy panel")
        if st.button("Go to Hierarchy Panel"):
            st.session_state.panel = "Hierarchy"
            st.rerun()
        return
    
    try:
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
            "Chart Type",
            ["Sunburst", "Treemap", "Icicle", "Network Graph"],
            index=0
        )
        
        # Generate appropriate chart
        if chart_type == "Sunburst":
            fig = px.sunburst(
                filtered_data,
                path=['Level', 'Parent Name', 'Name'],
                title="Organizational Hierarchy"
            )
        elif chart_type == "Treemap":
            fig = px.treemap(
                filtered_data,
                path=['Level', 'Parent Name', 'Name'],
                title="Organizational Structure"
            )
        elif chart_type == "Icicle":
            fig = px.icicle(
                filtered_data,
                path=['Level', 'Parent Name', 'Name'],
                title="Hierarchy Breakdown"
            )
        else:  # Network Graph
            fig = px.scatter(
                filtered_data,
                x='Level',
                y='Name',
                color='Level',
                title="Network View"
            )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Detailed view
        st.subheader("Detailed View")
        st.dataframe(
            filtered_data[['Level', 'Name', 'Parent Name']],
            use_container_width=True,
            height=400
        )
        
    except Exception as e:
        st.error(f"Error generating dashboard: {str(e)}")
        st.write("Data being used:")
        st.dataframe(filtered_data if 'filtered_data' in locals() else state['hierarchy']['hierarchy_table'])