import pandas as pd
import networkx as nx
from io import BytesIO

def build_hierarchy(hrp1000, hrp1001):
    """Build organizational hierarchy from HRP1000 and HRP1001 data"""
    # Create a mapping of Object ID to Name
    id_to_name = dict(zip(hrp1000['Object ID'], hrp1000['Name']))
    
    # Create a directed graph
    G = nx.DiGraph()
    
    # Add nodes
    for obj_id in hrp1000['Object ID']:
        G.add_node(obj_id)
    
    # Add edges from HRP1001
    for _, row in hrp1001.iterrows():
        if row['Source ID'] in G.nodes and row['Target object ID'] in G.nodes:
            G.add_edge(row['Source ID'], row['Target object ID'])
    
    # Find roots (nodes with no incoming edges)
    roots = [node for node in G.nodes if G.in_degree(node) == 0]
    
    # Build hierarchy levels
    hierarchy = []
    max_level = 0
    
    for root in roots:
        levels = nx.single_source_shortest_path_length(G, root)
        for node, level in levels.items():
            hierarchy.append({
                'Object ID': node,
                'Name': id_to_name.get(node, 'Unknown'),
                'Level': level + 1,  # Make level 1-based
                'Parent': next(iter(G.predecessors(node)), None) if G.in_degree(node) > 0 else None
            })
            if level + 1 > max_level:
                max_level = level + 1
    
    # Create hierarchy table
    hierarchy_table = pd.DataFrame(hierarchy)
    
    # Add parent names
    hierarchy_table['Parent Name'] = hierarchy_table['Parent'].map(id_to_name)
    
    # Create level associations
    level_associations = []
    
    for level in range(1, max_level + 1):
        level_df = hierarchy_table[hierarchy_table['Level'] == level]
        parent_level = level - 1 if level > 1 else None
        
        for _, row in level_df.iterrows():
            level_associations.append({
                'Level': level,
                'Object ID': row['Object ID'],
                'Name': row['Name'],
                'Parent ID': row['Parent'],
                'Parent Name': row['Parent Name']
            })
    
    level_associations = pd.DataFrame(level_associations)
    
    return {
        'hierarchy_table': hierarchy_table,
        'level_associations': level_associations,
        'max_level': max_level
    }

def optimize_table_display(df):
    """Optimize DataFrame for Streamlit display"""
    # Make a copy to avoid modifying original
    display_df = df.copy()
    
    # Convert datetime columns to strings
    datetime_cols = display_df.select_dtypes(include=['datetime']).columns
    for col in datetime_cols:
        display_df[col] = display_df[col].dt.strftime('%Y-%m-%d')
    
    # Truncate long text
    text_cols = display_df.select_dtypes(include=['object']).columns
    for col in text_cols:
        display_df[col] = display_df[col].astype(str).str[:50] + ('...' if display_df[col].str.len().max() > 50 else '')
    
    return display_df

def get_filtered_hierarchy(hierarchy_table, level_filter, parent_filter, status_filter, hrp1000):
    """Apply filters to hierarchy data"""
    filtered = hierarchy_table.copy()
    
    if level_filter:
        filtered = filtered[filtered['Level'].isin(level_filter)]
    
    if parent_filter:
        filtered = filtered[filtered['Parent'].isin(parent_filter)]
    
    if status_filter is not None and 'Planning status' in hrp1000:
        status_mapping = dict(zip(hrp1000['Object ID'], hrp1000['Planning status']))
        filtered['Planning status'] = filtered['Object ID'].map(status_mapping)
        filtered = filtered[filtered['Planning status'].isin(status_filter)]
    
    return filtered