
import pandas as pd
import networkx as nx
import json
import os
from pathlib import Path
from datetime import datetime
import sys

# Set recursion limit higher
sys.setrecursionlimit(10000)

def load_config(config_type):
    """Load configuration from JSON files with fallback to defaults"""
    try:
        config_path = f"configs/{config_type}_config.json"
        if os.path.exists(config_path):
            with open(config_path, "r") as f:
                return json.load(f)
    except Exception as e:
        print(f"Error loading config {config_type}: {e}")
    return None

def get_default_mappings():
    """Default mappings for your specific data structure"""
    return [
        {
            "target_column1": "externalCode",
            "target_column2": "External Code",
            "source_column": "Object ID",
            "source_file": "HRP1000",
            "transformation": "None",
            "transformation_code": "value",
            "default_value": "",
            "picklist_source": "",
            "picklist_column": "",
            "applies_to": "Level"
        }
    ]

def convert_german_date(value):
    """Convert German date format (dd.mm.yyyy) to ISO format (yyyy-mm-dd)"""
    try:
        if pd.isna(value) or value == '' or value == '00.00.0000':
            return ''
        
        date_str = str(value).strip()
        
        if '.' in date_str:
            try:
                date_obj = datetime.strptime(date_str, '%d.%m.%Y')
                return date_obj.strftime('%Y-%m-%d')
            except:
                pass
        
        if '-' in date_str and len(date_str) == 10:
            return date_str
        
        return str(value)
    except:
        return str(value) if value else ''

def lookup_value(value, picklist_name, picklist_column="", default=""):
    """Helper for picklist lookups with your status mapping"""
    try:
        if not picklist_name or not os.path.exists(f"picklists/{picklist_name}"):
            return default
            
        picklist = pd.read_csv(f"picklists/{picklist_name}")
        
        if picklist_name == "status_mapping.csv":
            status_map = {
                '1': 'ACT',
                '2': 'INA',
                '3': 'PND',
                '0': 'DEL'
            }
            lookup_value = status_map.get(str(value), str(value))
        else:
            lookup_value = str(value)
        
        matched = picklist[picklist['status_code'] == lookup_value]
        
        if not matched.empty:
            if picklist_column and picklist_column in picklist.columns:
                return matched[picklist_column].iloc[0]
            else:
                return matched['status_label'].iloc[0]
        
        return default
    except Exception as e:
        print(f"Picklist lookup error: {e}")
        return default

def apply_transformation(value, transformation_code, secondary_value=None):
    """Apply transformation code to value"""
    try:
        if pd.isna(value):
            value = ""
        
        if "convert_german_date" in transformation_code:
            return convert_german_date(value)
        
        if "lookup_value" in transformation_code:
            return str(value)
        
        if secondary_value is not None and not pd.isna(secondary_value):
            value1, value2 = value, secondary_value
            return eval(transformation_code)
        else:
            return eval(transformation_code)
    except Exception as e:
        print(f"Transformation error: {e}")
        return value

def apply_mappings(df, mappings, export_type, hrp1000_df=None, hrp1001_df=None):
    """Apply configured mappings to transform data"""
    if df.empty:
        return df
    
    applicable_mappings = [
        m for m in mappings 
        if m.get('applies_to') in [export_type, 'Both']
    ]
    
    if not applicable_mappings:
        return df
    
    result_df = df.copy()
    
    for mapping in applicable_mappings:
        target_col = mapping.get('target_column1', '')
        source_col = mapping.get('source_column', '')
        source_file = mapping.get('source_file', '')
        transformation = mapping.get('transformation', 'None')
        transformation_code = mapping.get('transformation_code', 'value')
        default_value = mapping.get('default_value', '')
        picklist_source = mapping.get('picklist_source', '')
        picklist_column = mapping.get('picklist_column', '')
        
        if not target_col:
            continue
            
        if source_file == "HRP1000" and hrp1000_df is not None:
            source_df = hrp1000_df
        elif source_file == "HRP1001" and hrp1001_df is not None:
            source_df = hrp1001_df
        else:
            source_df = df
        
        if source_col and source_col in source_df.columns:
            source_values = source_df[source_col]
        else:
            source_values = pd.Series([default_value] * len(df))
        
        if transformation == "Lookup Value" and picklist_source:
            result_df[target_col] = source_values.apply(
                lambda x: lookup_value(x, picklist_source, picklist_column, default_value)
            )
        elif transformation == "Date Format (YYYY-MM-DD)":
            result_df[target_col] = source_values.apply(convert_german_date)
        elif transformation != "None":
            result_df[target_col] = source_values.apply(
                lambda x: apply_transformation(x, transformation_code)
            )
        else:
            result_df[target_col] = source_values.fillna(default_value)
    
    return result_df

def build_hierarchy(hrp1000, hrp1001):
    """Build organizational hierarchy with improved recursion handling"""
    try:
        print(f"Processing {len(hrp1000)} units and {len(hrp1001)} relationships...")
        
        required_hrp1000 = ['Object ID', 'Name']
        required_hrp1001 = ['Source ID', 'Target object ID']
        
        missing_cols = []
        for col in required_hrp1000:
            if col not in hrp1000.columns:
                missing_cols.append(f"HRP1000: {col}")
        
        for col in required_hrp1001:
            if col not in hrp1001.columns:
                missing_cols.append(f"HRP1001: {col}")
        
        if missing_cols:
            raise ValueError(f"Missing required columns: {', '.join(missing_cols)}")
        
        # Clean data
        hrp1000_clean = hrp1000.copy()
        hrp1001_clean = hrp1001.copy()
        
        # Convert to strings
        hrp1000_clean['Object ID'] = hrp1000_clean['Object ID'].astype(str)
        hrp1001_clean['Source ID'] = hrp1001_clean['Source ID'].astype(str)
        hrp1001_clean['Target object ID'] = hrp1001_clean['Target object ID'].astype(str)
        
        # Filter active relationships
        if 'Planning status' in hrp1001_clean.columns:
            hrp1001_clean = hrp1001_clean[hrp1001_clean['Planning status'] == 1]
        
        print(f"Active relationships: {len(hrp1001_clean)}")
        
        # Build parent-child mapping (non-recursive approach)
        parent_child_map = {}
        child_parent_map = {}
        
        for _, row in hrp1001_clean.iterrows():
            source_id = row['Source ID']
            target_id = row['Target object ID']
            
            # Only process if both IDs exist in HRP1000
            if source_id in hrp1000_clean['Object ID'].values and target_id in hrp1000_clean['Object ID'].values:
                # target_id is parent of source_id
                if target_id not in parent_child_map:
                    parent_child_map[target_id] = []
                parent_child_map[target_id].append(source_id)
                child_parent_map[source_id] = target_id
        
        # Find root nodes (no parent)
        all_nodes = set(hrp1000_clean['Object ID'].values)
        root_nodes = [node for node in all_nodes if node not in child_parent_map]
        
        print(f"Root nodes found: {len(root_nodes)}")
        
        # Build hierarchy using iterative approach (no recursion)
        hierarchy_table = []
        level_data = {}
        associations_table = []
        level_associations = {}
        
        # Create node data lookup
        node_data = {}
        for _, row in hrp1000_clean.iterrows():
            node_data[row['Object ID']] = row.to_dict()
        
        # Process levels iteratively
        current_level = 1
        current_nodes = root_nodes.copy()
        processed_nodes = set()
        
        while current_nodes and current_level <= 20:  # Limit to 20 levels max
            next_level_nodes = []
            
            for node_id in current_nodes:
                if node_id in processed_nodes:
                    continue
                
                processed_nodes.add(node_id)
                node_info = node_data.get(node_id, {})
                
                # Get parent info
                parent_id = child_parent_map.get(node_id)
                parent_name = ""
                if parent_id and parent_id in node_data:
                    parent_name = node_data[parent_id].get('Name', '')
                
                # Create hierarchy entry
                hierarchy_entry = {
                    'Object ID': node_id,
                    'Name': node_info.get('Name', ''),
                    'Level': current_level,
                    'Parent': parent_id,
                    'Parent Name': parent_name,
                    'Path': f"Level {current_level}",
                    **node_info
                }
                
                hierarchy_table.append(hierarchy_entry)
                
                # Add to level data
                if current_level not in level_data:
                    level_data[current_level] = []
                level_data[current_level].append(hierarchy_entry)
                
                # Create association entry if has parent
                if parent_id and current_level > 1:
                    association_entry = {
                        'Source ID': node_id,
                        'Target object ID': parent_id,
                        'Level': current_level,
                        'Child Name': node_info.get('Name', ''),
                        'Parent Name': parent_name,
                        'Relationship Type': 'Reports To',
                        'Planning status': 1,
                        'Start date': node_info.get('Start date', ''),
                        'End Date': node_info.get('End Date', '')
                    }
                    
                    associations_table.append(association_entry)
                    
                    if current_level not in level_associations:
                        level_associations[current_level] = []
                    level_associations[current_level].append(association_entry)
                
                # Add children to next level
                if node_id in parent_child_map:
                    for child_id in parent_child_map[node_id]:
                        if child_id not in processed_nodes:
                            next_level_nodes.append(child_id)
            
            current_nodes = next_level_nodes
            current_level += 1
        
        # Convert to DataFrames
        hierarchy_df = pd.DataFrame(hierarchy_table)
        associations_df = pd.DataFrame(associations_table)
        
        level_data_dfs = {}
        for level, data in level_data.items():
            level_data_dfs[level] = pd.DataFrame(data)
        
        level_associations_dfs = {}
        for level, data in level_associations.items():
            level_associations_dfs[level] = pd.DataFrame(data)
        
        max_level = max(level_data.keys()) if level_data else 1
        
        print(f"Hierarchy built successfully: {len(hierarchy_table)} units, {max_level} levels")
        
        return {
            'hierarchy_table': hierarchy_df,
            'associations_table': associations_df,
            'level_data': level_data_dfs,
            'level_associations': level_associations_dfs,
            'max_level': max_level,
            'root_nodes': root_nodes
        }
        
    except Exception as e:
        raise Exception(f"Error building hierarchy: {str(e)}")

def format_for_export(df, export_type, level_names=None, level_num=None, hrp1000_df=None, hrp1001_df=None):
    """Format data for export using configured templates and mappings"""
    try:
        if df.empty:
            return df
        
        mappings = load_config("column_mappings") or get_default_mappings()
        formatted_df = apply_mappings(df, mappings, export_type, hrp1000_df, hrp1001_df)
        
        template_config = load_config(export_type.lower())
        if template_config:
            template_columns = [item.get('target_column1', '') for item in template_config if item.get('target_column1')]
            existing_template_cols = [col for col in template_columns if col in formatted_df.columns]
            other_cols = [col for col in formatted_df.columns if col not in template_columns]
            final_columns = existing_template_cols + other_cols
            formatted_df = formatted_df[final_columns]
        
        if level_names and 'Level' in formatted_df.columns:
            formatted_df['Level'] = formatted_df['Level'].map(level_names).fillna(formatted_df['Level'])
        
        return formatted_df
        
    except Exception as e:
        print(f"Export formatting error: {e}")
        return df

def optimize_table_display(df):
    """Prepare DataFrame for clean display in Streamlit"""
    if df.empty:
        return df
    
    display_df = df.copy()
    
    for col in display_df.columns:
        if display_df[col].dtype == 'object':
            display_df[col] = display_df[col].astype(str).apply(
                lambda x: x[:50] + "..." if len(str(x)) > 50 else x
            )
    
    for col in display_df.columns:
        if display_df[col].dtype in ['int64', 'float64']:
            display_df[col] = display_df[col].round(2)
    
    for col in display_df.columns:
        if 'date' in col.lower() or 'Date' in col:
            try:
                display_df[col] = display_df[col].apply(convert_german_date)
            except:
                pass
    
    return display_df
