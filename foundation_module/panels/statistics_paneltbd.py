import streamlit as st
import plotly.express as px
import pandas as pd
from utils.statistics_utils import calculate_statistics

def show_statistics_panel(state):
    st.header("Hierarchy Structure Analytics")
    
    if state.get('hierarchy') is None or state.get('hrp1000') is None:
        st.warning("Please build the hierarchy first in the Hierarchy panel")
        if st.button("Go to Hierarchy Panel"):
            st.session_state.panel = "Hierarchy"
            st.rerun()
        return
    
    try:
        if state.get('statistics') is None:
            with st.spinner("Calculating hierarchy metrics..."):
                state['statistics'] = calculate_statistics(state['hrp1000'], state['hrp1001'], state['hierarchy'])
        
        # Main hierarchy metrics
        st.subheader("Structure Metrics")
        cols = st.columns(4)
        metrics = [
            ("Total Entities", len(state['hrp1000'])),
            ("Hierarchy Depth", state['statistics']['max_depth']),
            ("Avg Children", f"{state['statistics']['avg_children']:.1f}"),
            ("Total Relationships", state['statistics']['total_relationships'])
        ]
        
        for i, (name, value) in enumerate(metrics):
            cols[i].metric(name, value)
        
        # Level distribution analysis
        st.subheader("Level Composition")
        tab1, tab2 = st.tabs(["Visualization", "Detailed View"])
        
        with tab1:
            level_data = state['statistics']['level_counts'].copy()
            if 'level_names' in state:
                level_data['Level'] = level_data['Level'].map(state['level_names'])
            
            fig = px.treemap(
                level_data,
                path=['Level'],
                values='Count',
                title="Entities by Level",
                color='Count',
                color_continuous_scale='Blues'
            )
            st.plotly_chart(fig, use_container_width=True)
        
        with tab2:
            level_stats = state['hrp1000'].groupby('Level').agg({
                'Name': 'count',
                'Parent': pd.Series.nunique
            }).rename(columns={
                'Name': 'Entity Count',
                'Parent': 'Unique Parents'
            })
            
            if 'level_names' in state:
                level_stats.index = level_stats.index.map(state['level_names'])
            
            st.dataframe(
                level_stats.style.format({
                    'Entity Count': '{:.0f}',
                    'Unique Parents': '{:.0f}'
                }),
                use_container_width=True
            )
        
        # Dynamic drill-down analysis
        st.subheader("Drill-Down Analysis")
        
        # Level selector
        available_levels = state['statistics']['level_counts']['Level'].tolist()
        if 'level_names' in state:
            level_options = {k: state['level_names'][k] for k in available_levels}
            selected_level_name = st.selectbox(
                "Select Level to Analyze",
                options=list(level_options.values())
            )
            selected_level = [k for k, v in level_options.items() if v == selected_level_name][0]
        else:
            selected_level = st.selectbox(
                "Select Level to Analyze",
                options=available_levels
            )
        
        # Get entities at selected level
        level_entities = state['hrp1000'][state['hrp1000']['Level'] == selected_level]
        
        # Show distribution of children counts
        if not level_entities.empty:
            children_counts = level_entities['Reports'].value_counts().reset_index()
            children_counts.columns = ['Child Count', 'Entity Count']
            
            col1, col2 = st.columns(2)
            with col1:
                st.metric(
                    f"Avg Children per {selected_level_name if 'level_names' in state else 'Level '+str(selected_level)}",
                    f"{level_entities['Reports'].mean():.1f}"
                )
                fig = px.bar(
                    children_counts,
                    x='Child Count',
                    y='Entity Count',
                    title="Distribution of Child Counts"
                )
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                st.metric(
                    "Total Children",
                    int(level_entities['Reports'].sum())
                )
                st.dataframe(
                    level_entities[['Name', 'Reports']].sort_values('Reports', ascending=False),
                    use_container_width=True,
                    height=400
                )
        
        # Temporal analysis (if dates available)
        if 'StartDate' in state['hrp1000']:
            st.subheader("Growth Timeline")
            
            # Convert dates properly
            state['hrp1000']['StartYear'] = pd.to_datetime(
                state['hrp1000']['StartDate'],
                format='%d/%m/%Y',
                errors='coerce'
            ).dt.year
            
            growth_data = state['hrp1000']['StartYear'].value_counts().reset_index()
            growth_data.columns = ['Year', 'Entity Count']
            growth_data = growth_data.sort_values('Year')
            
            fig = px.area(
                growth_data,
                x='Year',
                y='Entity Count',
                title="Cumulative Entity Growth",
                markers=True
            )
            st.plotly_chart(fig, use_container_width=True)
        
    except Exception as e:
        st.error(f"Error generating statistics: {str(e)}")