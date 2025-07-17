import pandas as pd

def calculate_statistics(hrp1000, hrp1001, hierarchy):
    """Calculate statistics about the organizational hierarchy"""
    stats = {}
    
    # Basic counts
    stats['total_units'] = len(hrp1000)
    stats['total_relationships'] = len(hrp1001)
    stats['max_depth'] = hierarchy['max_level']
    
    # Level distribution
    level_counts = hierarchy['hierarchy_table']['Level'].value_counts().reset_index()
    level_counts.columns = ['Level', 'Count']
    level_counts = level_counts.sort_values('Level')
    stats['level_counts'] = level_counts
    
    # Unit type breakdown (if available)
    if 'Object type' in hrp1000:
        type_breakdown = hrp1000['Object type'].value_counts().reset_index()
        type_breakdown.columns = ['Type', 'Count']
        stats['type_breakdown'] = type_breakdown
    else:
        stats['type_breakdown'] = pd.DataFrame({'Type': ['All'], 'Count': [len(hrp1000)]})
    
    # Date ranges
    if 'Start date' in hrp1000:
        hrp1000['Start Year'] = pd.to_datetime(hrp1000['Start date']).dt.year
        date_ranges = hrp1000['Start Year'].value_counts().reset_index()
        date_ranges.columns = ['Start Year', 'Count']
        stats['date_ranges'] = date_ranges
    else:
        stats['date_ranges'] = pd.DataFrame({'Start Year': ['Unknown'], 'Count': [len(hrp1000)]})
    
    # Hierarchy depth distribution
    depth_distribution = hierarchy['hierarchy_table'].groupby('Level').size().reset_index(name='Count')
    depth_distribution['Depth'] = depth_distribution['Level'].astype(str)
    stats['depth_distribution'] = depth_distribution
    
    # Average children per parent
    parent_counts = hierarchy['hierarchy_table']['Parent'].value_counts()
    stats['avg_children'] = parent_counts.mean() if not parent_counts.empty else 0
    
    # Detailed stats table
    detailed_stats = pd.DataFrame({
        'Metric': [
            'Total Organizational Units',
            'Total Relationships',
            'Maximum Hierarchy Depth',
            'Average Children per Parent',
            'Units at Top Level',
            'Units at Bottom Level'
        ],
        'Value': [
            stats['total_units'],
            stats['total_relationships'],
            stats['max_depth'],
            stats['avg_children'],
            level_counts[level_counts['Level'] == 1]['Count'].values[0] if not level_counts.empty else 0,
            level_counts[level_counts['Level'] == stats['max_depth']]['Count'].values[0] if not level_counts.empty else 0
        ]
    })
    
    stats['detailed_stats'] = detailed_stats
    
    return stats