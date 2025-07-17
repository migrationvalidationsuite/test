import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from datetime import datetime
from foundation_module.utils.statistics_utils import calculate_statistics

def show_statistics_panel(state):
    st.header("🏢 Advanced Organizational Analytics Dashboard")
    
    # Check if hierarchy data is available
    if state.get('hierarchy') is None or state.get('hrp1000') is None:
        st.warning("⚠️ Please build the hierarchy first in the Hierarchy panel")
        if st.button("Go to Hierarchy Panel"):
            st.session_state.panel = "Hierarchy"
            st.rerun()
        return
    
    try:
        # Calculate statistics if not already done
        if state.get('statistics') is None:
            with st.spinner("🔍 Calculating advanced statistics..."):
                state['statistics'] = calculate_statistics(
                    state['hrp1000'], 
                    state['hrp1001'], 
                    state['hierarchy']
                )
        
        # ================== KEY METRICS SECTION ==================
        st.subheader("📊 Key Organizational Metrics")
        cols = st.columns(4)
        metrics = [
            ("🏛️ Total Units", state['statistics']['total_units']),
            ("📏 Max Depth", state['statistics']['max_depth']),
            ("🧒 Avg Children", f"{state['statistics']['avg_children']:.1f}"),
            ("🤝 Total Relationships", state['statistics']['total_relationships'])
        ]
        
        for i, (name, value) in enumerate(metrics):
            cols[i].metric(name, value)
        
        # Advanced metrics with better formatting
        st.subheader("🔍 Advanced Metrics")
        adv_cols = st.columns(4)
        adv_metrics = [
            ("👔 Manager Ratio", f"{state['hrp1000']['IsManager'].mean():.1%}" if 'IsManager' in state['hrp1000'] else "N/A"),
            ("📊 Avg Span Control", f"{state['hrp1000']['Reports'].mean():.1f}" if 'Reports' in state['hrp1000'] else "N/A"),
            ("🆔 Unique Positions", state['hrp1000']['Position'].nunique() if 'Position' in state['hrp1000'] else "N/A"),
            ("🕳️ Empty Positions", state['hrp1000']['Position'].isna().sum() if 'Position' in state['hrp1000'] else "N/A")
        ]
        
        for i, (name, value) in enumerate(adv_metrics):
            adv_cols[i].metric(name, value)
        
        # ================== LEVEL DISTRIBUTION SECTION ==================
        st.subheader("📈 Level Distribution Analysis")
        tab1, tab2, tab3 = st.tabs(["📊 Visualization", "🔢 Counts", "📊 Advanced Stats"])
        
        with tab1:
            fig = px.bar(
                state['statistics']['level_counts'],
                x='Level',
                y='Count',
                title="Organizational Units by Level",
                color='Level',
                text='Count',
                template='plotly_white'
            )
            fig.update_layout(
                showlegend=False,
                hovermode="x unified",
                xaxis_title="Organizational Level",
                yaxis_title="Number of Units"
            )
            st.plotly_chart(fig, use_container_width=True)
        
        with tab2:
            st.dataframe(
                state['statistics']['level_counts'].style.format(precision=0),
                use_container_width=True,
                height=400
            )
            
        with tab3:
            if 'Level' in state['hrp1000']:
                level_stats = state['hrp1000'].groupby('Level').agg({
                    'Reports': ['mean', 'median', 'std', 'max'],
                    'Position': ['nunique', lambda x: x.isna().sum()],
                    'IsManager': 'mean'
                }).rename(columns={
                    'IsManager': 'Manager Ratio',
                    '<lambda>': 'Empty Positions'
                })
                
                st.dataframe(
                    level_stats.style.format({
                        ('Reports', 'mean'): '{:.1f}',
                        ('Reports', 'median'): '{:.1f}',
                        ('Reports', 'std'): '{:.1f}',
                        ('Reports', 'max'): '{:.0f}',
                        ('Position', 'nunique'): '{:.0f}',
                        ('Position', '<lambda>_0'): '{:.0f}',
                        'Manager Ratio': '{:.1%}'
                    }),
                    use_container_width=True,
                    height=400
                )
        
        # ================== TEMPORAL ANALYSIS SECTION ==================
        st.subheader("⏳ Organizational Growth Over Time")

        if 'Start date' in state['hrp1000']:
            # Process dates with error handling
            df = state['hrp1000'].copy()
            df['Start_Date'] = pd.to_datetime(
                df['Start date'], 
                format='%d.%m.%Y', 
                errors='coerce'
            )
            
            # Filter valid dates
            valid_dates = df.dropna(subset=['Start_Date'])
            
            if len(valid_dates) > 0:
                # Extract year and calculate metrics
                valid_dates['Year'] = valid_dates['Start_Date'].dt.year
                yearly_counts = valid_dates.groupby('Year').size().reset_index(name='New Units')
                yearly_counts = yearly_counts.sort_values('Year')
                
                # Calculate cumulative and percentage changes
                yearly_counts['Cumulative Units'] = yearly_counts['New Units'].cumsum()
                yearly_counts['YoY Growth'] = yearly_counts['Cumulative Units'].pct_change() * 100
                
                # Format the growth indicators with emojis
                yearly_counts['Trend'] = yearly_counts['YoY Growth'].apply(
                    lambda x: "🚀↑↑" if x > 30 else (
                        "⬆️↑" if x > 0 else (
                            "➡️→" if pd.isna(x) or x == 0 else "⬇️↓"
                        )
                    )
                )
                
                # Create two columns layout
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    # Enhanced area chart with better styling
                    fig = go.Figure()
                    fig.add_trace(go.Scatter(
                        x=yearly_counts['Year'],
                        y=yearly_counts['Cumulative Units'],
                        mode='lines+markers',
                        line=dict(shape='spline', smoothing=0.8, width=3, color='#4B9EF3'),
                        marker=dict(size=8, color='#1A73E8', line=dict(width=1, color='DarkSlateGrey')),
                        fill='tozeroy',
                        fillcolor='rgba(75, 158, 243, 0.2)',
                        name='Total Units',
                        hovertemplate=
                            '<b>Year</b>: %{x}<br>' +
                            '<b>Total Units</b>: %{y:,}<br>' +
                            '<b>New Units</b>: %{text:,}',
                        text=yearly_counts['New Units']
                    ))
                    
                    fig.update_layout(
                        title="Cumulative Organizational Growth",
                        xaxis_title="Year",
                        yaxis_title="Total Units",
                        hovermode="x unified",
                        showlegend=False,
                        margin=dict(l=20, r=20, t=40, b=20),
                        plot_bgcolor='rgba(0,0,0,0)',
                        paper_bgcolor='rgba(0,0,0,0)'
                    )
                    
                    st.plotly_chart(fig, use_container_width=True)
                
                with col2:
                    st.markdown("**📅 Yearly Growth Metrics**")
                    
                    # Display formatted table with better styling
                    display_df = yearly_counts[['Year', 'New Units', 'Cumulative Units', 'YoY Growth', 'Trend']].copy()
                    st.dataframe(
                        display_df.style.format({
                            'New Units': '{:,}',
                            'Cumulative Units': '{:,}',
                            'YoY Growth': '{:.1f}%'
                        }).applymap(
                            lambda x: 'color: #2ecc71' if '🚀' in str(x) else (
                                'color: #27ae60' if '⬆️' in str(x) else (
                                    'color: #e74c3c' if '⬇️' in str(x) else 'color: #95a5a6'
                                )
                            ), subset=['Trend']
                        ),
                        use_container_width=True,
                        height=400,
                        hide_index=True
                    )
                
                # Single expander with additional stats
                with st.expander("📈 Advanced Growth Statistics", expanded=False):
                    st.markdown("**📊 Detailed Yearly Analysis**")
                    
                    # Calculate additional metrics
                    yearly_stats = yearly_counts.copy()
                    yearly_stats['5Y Growth Rate'] = yearly_stats['Cumulative Units'].pct_change(periods=5) * 100
                    yearly_stats['Avg. Annual Growth'] = yearly_stats['YoY Growth'].rolling(3, min_periods=1).mean()
                    yearly_stats['Growth Acceleration'] = yearly_stats['YoY Growth'].diff()
                    
                    st.dataframe(
                        yearly_stats.style.format({
                            'New Units': '{:,}',
                            'Cumulative Units': '{:,}',
                            'YoY Growth': '{:.1f}%',
                            '5Y Growth Rate': '{:.1f}%',
                            'Avg. Annual Growth': '{:.1f}%',
                            'Growth Acceleration': '{:.1f}%'
                        }),
                        use_container_width=True
                    )
                    
                    st.markdown("""
                    **📝 Metrics Explanation:**
                    - **New Units**: Units created that year
                    - **Cumulative Units**: Total units up to that year
                    - **YoY Growth**: Year-over-year growth percentage
                    - **5Y Growth Rate**: 5-year compound growth rate
                    - **Avg. Annual Growth**: 3-year moving average of growth
                    - **Growth Acceleration**: Change in growth rate year-to-year
                    """)
            else:
                st.error("""
                **❌ Data Issue Detected:**
                - All dates appear as 'NaT' (Not a Time)
                - This typically happens when date parsing failed during data loading
                """)
                
                # Show troubleshooting guidance
                with st.expander("🛠️ How to fix this issue", expanded=True):
                    st.markdown("""
                    1. **🔍 Check your source files**:
                       - Open your HRP1000 file in Excel/text editor
                       - Verify the 'Start date' column contains valid dates
                       - Expected format: `DD.MM.YYYY` (e.g., 16.02.2009)

                    2. **🔄 Re-import your data**:
                       - Go back to the Hierarchy panel
                       - Re-upload your files
                       - Ensure date columns are properly parsed during import

                    3. **📅 Alternative formats**:
                       - Try different date formats if the standard one fails
                       - Common alternatives: `YYYY-MM-DD`, `MM/DD/YYYY`
                    """)
                
                # Alternative visualization using object counts
                st.info("ℹ️ Showing simple unit count since dates are unavailable")
                fig = go.Figure()
                fig.add_trace(go.Indicator(
                    mode="number",
                    value=len(state['hrp1000']),
                    title={"text": "Total Organizational Units"},
                    number={'font': {'size': 40}},
                    domain={'x': [0, 1], 'y': [0, 1]}
                ))
                fig.update_layout(paper_bgcolor="lightgray")
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("⚠️ Dataset missing 'Start date' column")
            
        # ================== COMPOSITION ANALYSIS SECTION ==================
        st.subheader("🧩 Level Composition Analysis")
        comp_col1, comp_col2 = st.columns([2, 1])
        
        with comp_col1:
            if 'Level' in state['hrp1000'] and 'Department' in state['hrp1000']:
                level_dept = state['hrp1000'].groupby(['Level', 'Department']).size().reset_index(name='Count')
                fig = px.sunburst(
                    level_dept,
                    path=['Level', 'Department'],
                    values='Count',
                    title="Department Distribution Across Levels",
                    color='Level',
                    color_discrete_sequence=px.colors.sequential.Blues_r
                )
                fig.update_traces(textinfo="label+percent entry")
                st.plotly_chart(fig, use_container_width=True)
            elif 'Level' in state['hrp1000'] and 'Position' in state['hrp1000']:
                level_pos = state['hrp1000'].groupby(['Level', 'Position']).size().reset_index(name='Count')
                fig = px.treemap(
                    level_pos,
                    path=['Level', 'Position'],
                    values='Count',
                    title="Position Distribution Across Levels",
                    color='Level',
                    color_discrete_sequence=px.colors.sequential.Blues_r
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.warning("Insufficient data for composition analysis")
        
        with comp_col2:
            if 'Level' in state['hrp1000'] and 'Department' in state['hrp1000']:
                crosstab = pd.crosstab(
                    state['hrp1000']['Level'], 
                    state['hrp1000']['Department'],
                    margins=True
                )
                st.dataframe(
                    crosstab.style.format(precision=0),
                    use_container_width=True,
                    height=500
                )
            elif 'Level' in state['hrp1000'] and 'Position' in state['hrp1000']:
                crosstab = pd.crosstab(
                    state['hrp1000']['Level'], 
                    state['hrp1000']['Position'],
                    margins=True
                )
                st.dataframe(
                    crosstab.style.format(precision=0),
                    use_container_width=True,
                    height=500
                )
        
        # ================== COMPENSATION ANALYSIS SECTION ==================
        if 'Salary' in state['hrp1000'].columns:
            st.subheader("💰 Compensation Structure Analysis")
            comp_col1, comp_col2 = st.columns([2, 1])
            
            with comp_col1:
                fig = px.box(
                    state['hrp1000'],
                    x='Level',
                    y='Salary',
                    title="Salary Distribution by Level",
                    color='Level',
                    points="all",
                    hover_data=['Position', 'Department'],
                    template='plotly_white'
                )
                fig.update_layout(
                    yaxis_title="Salary",
                    xaxis_title="Organizational Level",
                    showlegend=False
                )
                st.plotly_chart(fig, use_container_width=True)
            
            with comp_col2:
                salary_stats = state['hrp1000'].groupby('Level')['Salary'].agg(
                    ['min', 'median', 'max', 'std', 'count']
                )
                salary_stats['Compression'] = salary_stats['max'] / salary_stats['min']
                salary_stats['Range'] = salary_stats['max'] - salary_stats['min']
                
                st.dataframe(
                    salary_stats.style.format({
                        'min': '${:,.0f}',
                        'median': '${:,.0f}',
                        'max': '${:,.0f}',
                        'std': '${:,.0f}',
                        'count': '{:,.0f}',
                        'Compression': '{:.1f}x',
                        'Range': '${:,.0f}'
                    }),
                    use_container_width=True,
                    height=500
                )
        
        # ================== DETAILED STATISTICS SECTION ==================
        st.subheader("📋 Complete Statistical Summary")
        if 'detailed_stats' in state['statistics']:
            st.dataframe(
                state['statistics']['detailed_stats'].style.format(precision=2),
                use_container_width=True,
                height=600
            )
        else:
            st.warning("No detailed statistics available")
        
    except Exception as e:
        st.error(f"❌ Error generating statistics: {str(e)}")
        st.exception(e)
