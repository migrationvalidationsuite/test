import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from utils.statistics_utils import calculate_statistics

def show_statistics_panel(state):
    st.header("Advanced Organizational Analytics")
    
    if state.get('hierarchy') is None or state.get('hrp1000') is None:
        st.warning("Please build the hierarchy first in the Hierarchy panel")
        if st.button("Go to Hierarchy Panel"):
            st.session_state.panel = "Hierarchy"
            st.rerun()
        return
    
    try:
        # Calculate statistics if not already done
        if state.get('statistics') is None:
            with st.spinner("Calculating advanced statistics..."):
                state['statistics'] = calculate_statistics(state['hrp1000'], state['hrp1001'], state['hierarchy'])
        
        # Main metrics
        st.subheader("Key Organizational Metrics")
        cols = st.columns(4)
        metrics = [
            ("Total Units", state['statistics']['total_units']),
            ("Max Depth", state['statistics']['max_depth']),
            ("Avg Children", f"{state['statistics']['avg_children']:.1f}"),
            ("Total Relationships", state['statistics']['total_relationships'])
        ]
        
        for i, (name, value) in enumerate(metrics):
            cols[i].metric(name, value)
        
        # Advanced metrics
        st.subheader("Advanced Metrics")
        adv_cols = st.columns(4)
        adv_metrics = [
            ("Manager Ratio", f"{state['hrp1000']['IsManager'].mean():.1%}" if 'IsManager' in state['hrp1000'] else "N/A"),
            ("Avg Span Control", f"{state['hrp1000']['Reports'].mean():.1f}" if 'Reports' in state['hrp1000'] else "N/A"),
            ("Unique Positions", state['hrp1000']['Position'].nunique() if 'Position' in state['hrp1000'] else "N/A"),
            ("Empty Positions", state['hrp1000']['Position'].isna().sum() if 'Position' in state['hrp1000'] else "N/A")
        ]
        
        for i, (name, value) in enumerate(adv_metrics):
            adv_cols[i].metric(name, value)
        
        # Level distribution with advanced stats
        st.subheader("Level Distribution Analysis")
        tab1, tab2, tab3 = st.tabs(["Visualization", "Counts", "Advanced Stats"])
        
        with tab1:
            fig = px.bar(
                state['statistics']['level_counts'],
                x='Level',
                y='Count',
                title="Organizational Units by Level",
                color='Level',
                text='Count'
            )
            fig.update_layout(showlegend=False)
            st.plotly_chart(fig, use_container_width=True)
        
        with tab2:
            st.dataframe(
                state['statistics']['level_counts'],
                use_container_width=True
            )
            
        with tab3:
            if 'Level' in state['hrp1000']:
                level_stats = state['hrp1000'].groupby('Level').agg({
                    'Reports': ['mean', 'median', 'std'],
                    'Position': 'nunique',
                    'IsManager': 'mean'
                }).rename(columns={
                    'IsManager': 'Manager Ratio'
                })
                st.dataframe(
                    level_stats.style.format({
                        ('Reports', 'mean'): '{:.1f}',
                        ('Reports', 'median'): '{:.1f}',
                        ('Reports', 'std'): '{:.1f}',
                        'Position': '{:.0f}',
                        'Manager Ratio': '{:.1%}'
                    }),
                    use_container_width=True
                )
        
        # Enhanced Temporal Analysis
        if 'date_ranges' in state['statistics']:
            st.subheader("Temporal Analysis")
            st.write("Organizational Growth Over Time")
            
            temp_col1, temp_col2 = st.columns([2, 1])
            
            with temp_col1:
                fig = px.area(
                    state['statistics']['date_ranges'],
                    x='Start Year',
                    y='Count',
                    title="Cumulative Organizational Growth",
                    markers=True,
                    line_shape='spline'
                )
                st.plotly_chart(fig, use_container_width=True)
            
            with temp_col2:
                yearly_stats = state['statistics']['date_ranges'].copy()
                yearly_stats['YoY Growth'] = yearly_stats['Count'].pct_change() * 100
                st.dataframe(
                    yearly_stats.style.format({
                        'Count': '{:.0f}',
                        'YoY Growth': '{:.1f}%'
                    }),
                    use_container_width=True
                )
        
        # Enhanced Type Breakdown
        if 'type_breakdown' in state['statistics']:
            st.subheader("Type Composition Analysis")
            type_col1, type_col2 = st.columns([2, 1])
            
            with type_col1:
                fig = px.sunburst(
                    state['statistics']['type_breakdown'],
                    path=['Type'],
                    values='Count',
                    title="Organizational Unit Type Distribution"
                )
                st.plotly_chart(fig, use_container_width=True)
            
            with type_col2:
                st.dataframe(
                    state['statistics']['type_breakdown'],
                    use_container_width=True
                )
        
        # Department Analysis (if available)
        if 'Department' in state['hrp1000'].columns:
            st.subheader("Departmental Structure")
            dept_col1, dept_col2 = st.columns([2, 1])
            
            with dept_col1:
                dept_stats = state['hrp1000']['Department'].value_counts().reset_index()
                fig = px.treemap(
                    dept_stats,
                    path=['Department'],
                    values='count',
                    title="Department Size Distribution"
                )
                st.plotly_chart(fig, use_container_width=True)
            
            with dept_col2:
                st.dataframe(
                    dept_stats,
                    use_container_width=True,
                    hide_index=True
                )
        
        # Compensation Analysis (if available)
        if 'Salary' in state['hrp1000'].columns:
            st.subheader("Compensation Structure")
            comp_col1, comp_col2 = st.columns([2, 1])
            
            with comp_col1:
                fig = px.box(
                    state['hrp1000'],
                    x='Level',
                    y='Salary',
                    title="Salary Distribution by Level"
                )
                st.plotly_chart(fig, use_container_width=True)
            
            with comp_col2:
                salary_stats = state['hrp1000'].groupby('Level')['Salary'].agg(['min', 'median', 'max', 'std'])
                salary_stats['Compression'] = salary_stats['max'] / salary_stats['min']
                st.dataframe(
                    salary_stats.style.format({
                        'min': '${:,.0f}',
                        'median': '${:,.0f}',
                        'max': '${:,.0f}',
                        'std': '${:,.0f}',
                        'Compression': '{:.1f}x'
                    }),
                    use_container_width=True
                )
        
        # Detailed statistics table
        st.subheader("Complete Statistical Summary")
        st.dataframe(
            state['statistics'].get('detailed_stats', pd.DataFrame()),
            use_container_width=True,
            height=400
        )
        
    except Exception as e:
        st.error(f"Error generating statistics: {str(e)}")