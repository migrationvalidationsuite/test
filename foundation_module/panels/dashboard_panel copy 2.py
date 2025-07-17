import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
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
            ("Total Employees", len(state['hrp1000'])),
            ("Management Ratio", f"{state['hrp1000']['IsManager'].mean():.1%}" if 'IsManager' in state['hrp1000'] else "N/A"),
            ("Avg Span Control", f"{state['hrp1000']['Reports'].mean():.1f}" if 'Reports' in state['hrp1000'] else "N/A"),
            ("Hierarchy Depth", state['statistics']['max_depth'])
        ]
        
        for i, (name, value) in enumerate(metrics):
            cols[i].metric(name, value)
        
        # ==================== Sankey Diagram with Improved Logic ====================
        st.subheader("Organizational Flow (Sankey Diagram)")
        
        # Try multiple possible ID columns
        id_cols_to_try = ['ManagerID', 'Manager Id', 'Manager_ID', 'manager_id', 
                         'ObjectID', 'Object Id', 'Object_ID', 'object_id',
                         'Parent', 'ParentID', 'Parent Id', 'parent_id']
        
        manager_col = next((col for col in id_cols_to_try if col in state['hrp1000']), None)
        employee_col = next((col for col in ['ObjectID', 'Object Id', 'Object_ID', 'object_id', 'ID', 'Id'] 
                           if col in state['hrp1000']), None)
        
        if manager_col and employee_col:
            # Prepare data for Sankey
            sankey_data = state['hrp1000'][[employee_col, manager_col]].dropna()
            
            # Get names for display
            name_col = next((col for col in ['Name', 'EmployeeName', 'FullName'] 
                           if col in state['hrp1000']), None)
            
            if name_col:
                sankey_data = sankey_data.merge(
                    state['hrp1000'][[employee_col, name_col]],
                    left_on=employee_col,
                    right_on=employee_col,
                    how='left'
                )
                sankey_data = sankey_data.merge(
                    state['hrp1000'][[employee_col, name_col]],
                    left_on=manager_col,
                    right_on=employee_col,
                    how='left',
                    suffixes=('_employee', '_manager')
                )
                
                # Create node list
                nodes = pd.concat([
                    sankey_data[f"{name_col}_manager"],
                    sankey_data[f"{name_col}_employee"]
                ]).dropna().unique()
                
                # Create links
                node_indices = {name: idx for idx, name in enumerate(nodes)}
                links = {
                    'source': [node_indices[name] for name in sankey_data[f"{name_col}_manager"] 
                             if name in node_indices],
                    'target': [node_indices[name] for name in sankey_data[f"{name_col}_employee"] 
                             if name in node_indices],
                    'value': [1] * len(sankey_data)
                }
                
                # Create figure
                fig = go.Figure(go.Sankey(
                    node=dict(
                        pad=15,
                        thickness=20,
                        line=dict(color="black", width=0.5),
                        label=nodes,
                        color="blue"
                    ),
                    link=dict(
                        source=links['source'],
                        target=links['target'],
                        value=links['value']
                    )
                ))
                
                fig.update_layout(
                    title_text="Manager-Employee Relationships",
                    font_size=10,
                    height=600
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.warning("Name column not found - using IDs for Sankey diagram")
                # Fallback to using IDs if names not available
                nodes = pd.concat([
                    sankey_data[manager_col],
                    sankey_data[employee_col]
                ]).unique()
                
                node_indices = {name: idx for idx, name in enumerate(nodes)}
                links = {
                    'source': [node_indices[name] for name in sankey_data[manager_col]],
                    'target': [node_indices[name] for name in sankey_data[employee_col]],
                    'value': [1] * len(sankey_data)
                }
                
                fig = go.Figure(go.Sankey(
                    node=dict(
                        pad=15,
                        thickness=20,
                        line=dict(color="black", width=0.5),
                        label=nodes,
                        color="blue"
                    ),
                    link=dict(
                        source=links['source'],
                        target=links['target'],
                        value=links['value']
                    )
                ))
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("Manager/Employee relationship columns not found - cannot generate Sankey diagram")
        
        # ==================== Hierarchical Visualization (from copy version) ====================
        st.subheader("Hierarchical Views")
        
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
        
        # ==================== Enhanced Type Composition Analysis ====================
        # If type breakdown is too simple, show tenure analysis instead
        if 'type_breakdown' in state['statistics'] and len(state['statistics']['type_breakdown']) > 1:
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
        elif 'StartDate' in state['hrp1000'].columns:
            st.subheader("Tenure Analysis")
            tenure_col1, tenure_col2 = st.columns([2, 1])
            
            with tenure_col1:
                state['hrp1000']['Tenure'] = (pd.to_datetime('today') - pd.to_datetime(state['hrp1000']['StartDate'])).dt.days / 365
                fig = px.box(
                    state['hrp1000'],
                    x='Level',
                    y='Tenure',
                    title="Tenure Distribution by Level",
                    color='Level'
                )
                st.plotly_chart(fig, use_container_width=True)
            
            with tenure_col2:
                tenure_stats = state['hrp1000'].groupby('Level')['Tenure'].agg(['mean', 'median', 'std', 'count'])
                st.dataframe(
                    tenure_stats.style.format({
                        'mean': '{:.1f} years',
                        'median': '{:.1f} years',
                        'std': '{:.1f} years',
                        'count': '{:.0f}'
                    }),
                    use_container_width=True
                )
        
        # Department distribution
        st.subheader("Department Distribution")
        if 'Department' in state['hrp1000'].columns:
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
        
        # Detailed view
        st.subheader("Detailed View")
        view_option = st.radio(
            "View Data As",
            ["Hierarchy Table", "Employee List"],
            horizontal=True
        )
        
        if view_option == "Hierarchy Table":
            st.dataframe(
                filtered_data[['Level', 'Name', 'Parent Name']],
                use_container_width=True,
                height=400
            )
        else:
            st.dataframe(
                state['hrp1000'],
                use_container_width=True,
                height=400
            )
        
    except Exception as e:
        st.error(f"Error generating dashboard: {str(e)}")
        st.write("Debug Information:")
        if 'filtered_data' in locals():
            st.write("Filtered Data:")
            st.dataframe(filtered_data)
        st.write("HRP1000 Data:")
        st.dataframe(state['hrp1000'].head())