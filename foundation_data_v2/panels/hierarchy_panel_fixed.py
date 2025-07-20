import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import re
import io
from openpyxl import Workbook
from openpyxl.utils.dataframe import dataframe_to_rows

def load_mapping_configuration(state):
    """Load and parse the mapping configuration from admin panel with better debugging"""
    try:
        # Debug: Show what's available in session state
        mapping_keys = [k for k in st.session_state.keys() if 'mapping' in k.lower() or 'admin' in k.lower()]
        
        # Check session state for mapping configuration (highest priority)
        if 'mapping_config' in st.session_state:
            config = st.session_state['mapping_config']
            if isinstance(config, pd.DataFrame) and not config.empty:
                st.success("Loaded custom mapping configuration from Admin panel")
                return config
            elif isinstance(config, list) and config:
                return pd.DataFrame(config)
        
        # Check alternative session state keys
        for key in ['current_mappings', 'admin_mappings']:
            if key in st.session_state:
                config = st.session_state[key]
                if isinstance(config, pd.DataFrame) and not config.empty:
                    st.success(f"Loaded mapping configuration from {key}")
                    return config
                elif isinstance(config, list) and config:
                    return pd.DataFrame(config)
        
        # Try to load from file system as fallback
        try:
            import json
            import os
            config_path = "configs/column_mappings_config.json"
            if os.path.exists(config_path):
                with open(config_path, 'r') as f:
                    config_data = json.load(f)
                    if config_data:
                        df_config = pd.DataFrame(config_data)
                        # Also sync to session state for next time
                        st.session_state['mapping_config'] = df_config
                        st.info("Loaded mapping configuration from file system")
                        return df_config
        except Exception as e:
            st.warning(f"Could not load from file system: {str(e)}")
        
        # If no custom config found, show warning and use default
        st.warning("No custom mapping configuration found. Using default mapping.")
        st.info("Configure custom mappings in the Admin panel to override defaults.")
        return create_default_mapping()
        
    except Exception as e:
        st.error(f"Error loading mapping configuration: {str(e)}")
        return create_default_mapping()

def create_default_mapping():
    """Create default mapping configuration based on standard structure"""
    level_mappings = [
        {
            'target_column1': 'externalCode',
            'target_column2': 'External Code', 
            'source_file': 'HRP1000',
            'source_column': 'Object ID',
            'transformation': 'None',
            'default_value': None,
            'applies_to': 'Level'
        },
        {
            'target_column1': 'Operator',
            'target_column2': 'Operator',
            'source_file': 'HRP1000', 
            'source_column': None,
            'transformation': 'None',
            'default_value': 'N/A',
            'applies_to': 'Level'
        },
        {
            'target_column1': 'effectiveStartDate',
            'target_column2': 'Effective Start Date',
            'source_file': 'HRP1000',
            'source_column': 'Start date',
            'transformation': 'None', 
            'default_value': None,
            'applies_to': 'Level'
        },
        {
            'target_column1': 'effectiveEndDate',
            'target_column2': 'Effective End Date',
            'source_file': 'HRP1000',
            'source_column': 'End Date',
            'transformation': 'None',
            'default_value': None,
            'applies_to': 'Level'
        },
        {
            'target_column1': 'name.en_US',
            'target_column2': 'Name (English US)',
            'source_file': 'HRP1000',
            'source_column': 'Name',
            'transformation': 'Trim Whitespace',
            'default_value': None,
            'applies_to': 'Level'
        },
        {
            'target_column1': 'name.defaultValue',
            'target_column2': 'Name (Default)',
            'source_file': 'HRP1000',
            'source_column': 'Name',
            'transformation': 'Title Case',
            'default_value': None,
            'applies_to': 'Level'
        },
        {
            'target_column1': 'effectiveStatus',
            'target_column2': 'Status',
            'source_file': 'HRP1000',
            'source_column': 'Planning status',
            'transformation': 'Lookup Value',
            'default_value': 'Active',
            'applies_to': 'Level'
        },
        {
            'target_column1': 'Object abbr.',
            'target_column2': 'Object Abbreviation',
            'source_file': 'HRP1000',
            'source_column': 'Object abbr.',
            'transformation': 'None',
            'default_value': None,
            'applies_to': 'Level'
        }
    ]
    
    association_mappings = [
        {
            'target_column1': 'effectiveStartDate',
            'target_column2': 'Effective Start Date',
            'source_file': 'HRP1001',
            'source_column': 'Start date',
            'transformation': 'None',
            'default_value': None,
            'applies_to': 'Association'
        },
        {
            'target_column1': 'relationshipType',
            'target_column2': 'Relationship Type',
            'source_file': 'HRP1001',
            'source_column': 'Relationship',
            'transformation': 'UPPERCASE',
            'default_value': 'REPORTS_TO',
            'applies_to': 'Association'
        },
        {
            'target_column1': 'cust_toLegalEntity.externalCode',
            'target_column2': 'Parent Entity Code',
            'source_file': 'HRP1001',
            'source_column': 'Source ID',
            'transformation': 'None',
            'default_value': None,
            'applies_to': 'Association'
        },
        {
            'target_column1': 'externalCode',
            'target_column2': 'External Code',
            'source_file': 'HRP1001',
            'source_column': 'Target object ID',
            'transformation': 'None',
            'default_value': None,
            'applies_to': 'Association'
        }
    ]
    
    return pd.DataFrame(level_mappings + association_mappings)

def apply_transformation(value, transformation, mapping_config=None, source_row=None, source_df=None):
    """Apply specified transformation to a value with support for advanced transformations"""
    
    # Import required libraries at the top to avoid scope issues
    import pandas as pd
    import numpy as np
    from datetime import datetime
    
    if pd.isna(value) or value is None:
        # For concatenation, we might still want to proceed even if primary value is None
        if transformation != 'Concatenate':
            return value
    
    value_str = str(value) if not pd.isna(value) else ""
    
    if transformation == 'Trim Whitespace':
        return value_str.strip()
    elif transformation == 'Title Case':
        return value_str.title()
    elif transformation == 'UPPERCASE':
        return value_str.upper()
    elif transformation == 'lowercase':
        return value_str.lower()
    elif transformation == 'Lookup Value':
        # Map planning status codes
        status_map = {
            '1': 'Active',
            '2': 'Inactive', 
            '3': 'Planned',
            '0': 'Deleted',
            1: 'Active',
            2: 'Inactive',
            3: 'Planned', 
            0: 'Deleted'
        }
        return status_map.get(value, 'Active')
    
    elif transformation == 'Concatenate':
        # Handle concatenation of two columns
        if mapping_config is not None and source_row is not None:
            secondary_column = mapping_config.get('secondary_column', '')
            if secondary_column and secondary_column in source_row.index:
                secondary_value = source_row[secondary_column]
                secondary_str = str(secondary_value) if not pd.isna(secondary_value) else ""
                
                # Concatenate with a separator
                if value_str and secondary_str:
                    return f"{value_str} - {secondary_str}"
                elif value_str:
                    return value_str
                elif secondary_str:
                    return secondary_str
                else:
                    return ""
            else:
                st.warning(f"Secondary column '{secondary_column}' not found for concatenation")
                return value_str
        else:
            return value_str
    
    elif transformation == 'Custom Python':
        # Handle custom Python code execution
        if mapping_config is not None and 'transformation_code' in mapping_config:
            custom_code = mapping_config['transformation_code']
            
            try:
                # Get secondary value if needed
                secondary_value = None
                if source_row is not None and 'secondary_column' in mapping_config:
                    secondary_column = mapping_config.get('secondary_column', '')
                    if secondary_column and secondary_column in source_row.index:
                        secondary_value = source_row[secondary_column]
                
                # Create execution environment (pd, np, datetime already imported above)
                exec_env = {
                    'value': value,
                    'secondary_value': secondary_value,
                    'pd': pd,
                    'np': np,
                    'datetime': datetime,
                    'str': str,
                    'int': int,
                    'float': float,
                    'len': len,
                    'abs': abs,
                    'round': round,
                    'hash': hash
                }
                
                # Execute the custom code
                result = eval(custom_code, {"__builtins__": {}}, exec_env)
                return result
                
            except Exception as e:
                st.error(f"Error executing custom Python code: {str(e)}")
                st.error(f"Code: {custom_code}")
                return value_str
        else:
            return value_str
    
    elif transformation == 'Extract First Word':
        if value_str and value_str.strip():
            return value_str.split()[0]
        return value_str
    
    elif transformation == 'Date Format (YYYY-MM-DD)':
        # Convert German date format to YYYY-MM-DD
        try:
            # Handle dd.mm.yyyy format
            if '.' in value_str:
                parts = value_str.split('.')
                if len(parts) == 3:
                    day, month, year = parts
                    return f"{year.zfill(4)}-{month.zfill(2)}-{day.zfill(2)}"
            return value_str
        except:
            return value_str
    
    else:
        # Default case - return original value
        return value

def create_output_dataframe(source_df, mappings, file_type):
    """Create output DataFrame with proper structure based on mappings"""
    
    # Filter mappings for this file type
    relevant_mappings = mappings[mappings['applies_to'] == file_type].copy()
    
    if relevant_mappings.empty:
        return pd.DataFrame()
    
    # Sort mappings to ensure consistent column order
    relevant_mappings = relevant_mappings.reset_index(drop=True)
    
    # Create the output structure
    output_data = []
    
    # Row 1: API field names (target_column1)
    api_fields = relevant_mappings['target_column1'].tolist()
    
    # Special handling for the first column (Operator)
    if file_type == 'Level':
        api_fields[0] = '[OPERATOR]'  # Special formatting for operator column
    elif file_type == 'Association':
        if 'Operator' in api_fields:
            idx = api_fields.index('Operator')
            api_fields[idx] = '[OPERATOR]'
    
    output_data.append(api_fields)
    
    # Row 2: Human-readable headers (target_column2)
    headers = relevant_mappings['target_column2'].tolist()
    
    # Special handling for operator header
    if file_type == 'Level':
        headers[0] = 'Supported operators: Delimit, Clear and Delete'
    elif file_type == 'Association':
        if 'Operator' in relevant_mappings['target_column2'].values:
            idx = relevant_mappings[relevant_mappings['target_column2'] == 'Operator'].index[0]
            headers[idx] = 'Supported operators: Delimit, Clear and Delete'
    
    output_data.append(headers)
    
    # Row 3-4: Empty rows for formatting
    empty_row = [None] * len(api_fields)
    output_data.append(empty_row)
    output_data.append(empty_row)
    
    # Row 5+: Actual data
    for _, source_row in source_df.iterrows():
        data_row = []
        
        for _, mapping in relevant_mappings.iterrows():
            source_column = mapping['source_column']
            transformation = mapping['transformation']
            default_value = mapping['default_value']
            
            # Get value from source
            if source_column and source_column in source_df.columns:
                value = source_row[source_column]
            elif default_value:
                value = default_value
            else:
                value = None
            
            # Apply transformation with enhanced parameters
            if transformation and transformation != 'None':
                # Convert mapping row to dict for easier access
                mapping_dict = mapping.to_dict()
                value = apply_transformation(value, transformation, mapping_dict, source_row, source_df)
            
            # Handle default values for null/empty values
            if (pd.isna(value) or value is None or value == '') and default_value:
                value = default_value
            
            # Ensure clean data types for Arrow compatibility
            if pd.isna(value) or value is None:
                value = ""
            else:
                value = str(value)  # Convert all values to string for consistency
            
            data_row.append(value)
        
        output_data.append(data_row)
    
    # Create DataFrame with the API field names as columns
    columns = [f"Column_{i+1}" for i in range(len(api_fields))]
    output_df = pd.DataFrame(output_data, columns=columns)
    
    # Ensure all columns are string type for Arrow compatibility
    for col in output_df.columns:
        output_df[col] = output_df[col].astype(str)
    
    return output_df

def process_level_files(state, level_number):
    """Process level files with proper mapping configuration"""
    
    # Load mapping configuration
    mapping_config = load_mapping_configuration(state)
    
    # Get source data
    hrp1000_df = state.get('source_hrp1000')
    if hrp1000_df is None or hrp1000_df.empty:
        return None, "HRP1000 data not found"
    
    # Filter data for this level based on hierarchy
    level_data = filter_data_for_level(hrp1000_df, level_number, state)
    
    if level_data.empty:
        return None, f"No data found for Level {level_number}"
    
    # Create output using mapping configuration
    output_df = create_output_dataframe(level_data, mapping_config, 'Level')
    
    if output_df.empty:
        return None, "Failed to create output - check mapping configuration"
    
    # Generate dynamic filename using custom level names
    level_names = state.get('level_names', {})
    if level_number in level_names and level_names[level_number]:
        level_name = level_names[level_number].replace(' ', '_')
    else:
        level_name = get_level_name(level_number, state).replace(' ', '_')
    
    filename = f"Level_{level_number}_{level_name}.xlsx"
    
    return output_df, filename

def process_association_files(state, level_number=None):
    """Process association files with proper mapping configuration"""
    
    # Load mapping configuration
    mapping_config = load_mapping_configuration(state)
    
    # Get source data
    hrp1001_df = state.get('source_hrp1001')
    if hrp1001_df is None or hrp1001_df.empty:
        return None, "HRP1001 data not found"
    
    # Filter data for specific level if provided
    if level_number:
        # Get hierarchy structure to filter relationships for this level
        hierarchy = state.get('hierarchy_structure', {})
        if hierarchy:
            level_units = [uid for uid, info in hierarchy.items() if info.get('level') == level_number]
            if level_units:
                # Filter relationships where source is from this level
                filtered_hrp1001 = hrp1001_df[hrp1001_df['Source ID'].astype(str).isin(level_units)]
            else:
                filtered_hrp1001 = pd.DataFrame()
        else:
            filtered_hrp1001 = hrp1001_df
    else:
        filtered_hrp1001 = hrp1001_df
    
    if filtered_hrp1001.empty:
        return None, f"No association data found for Level {level_number}" if level_number else "No association data found"
    
    # Create output using mapping configuration
    output_df = create_output_dataframe(filtered_hrp1001, mapping_config, 'Association')
    
    if output_df.empty:
        return None, "Failed to create output - check mapping configuration"
    
    # Generate dynamic filename
    if level_number:
        level_names = state.get('level_names', {})
        if level_number in level_names and level_names[level_number]:
            level_name = level_names[level_number].replace(' ', '_')
        else:
            level_name = get_level_name(level_number, state).replace(' ', '_')
        filename = f"Level_{level_number}_{level_name}_Associations.xlsx"
    else:
        filename = "All_Level_Associations.xlsx"
    
    return output_df, filename

def filter_data_for_level(hrp1000_df, level_number, state):
    """Filter HRP1000 data for specific hierarchy level"""
    
    # Get hierarchy structure
    hierarchy = state.get('hierarchy_structure', {})
    
    if not hierarchy:
        # If no hierarchy defined, return all data for level 1
        if level_number == 1:
            return hrp1000_df
        else:
            return pd.DataFrame()
    
    # Get units for this level
    level_units = []
    for unit_id, unit_info in hierarchy.items():
        if unit_info.get('level') == level_number:
            level_units.append(unit_id)
    
    if not level_units:
        return pd.DataFrame()
    
    # Filter data for these units
    filtered_df = hrp1000_df[hrp1000_df['Object ID'].astype(str).isin(level_units)]
    
    return filtered_df

def get_level_name(level_number, state):
    """Get dynamic level name based on hierarchy structure"""
    
    hierarchy = state.get('hierarchy_structure', {})
    level_names = state.get('level_names', {})
    
    # Try to get custom level name first
    if level_number in level_names:
        return level_names[level_number]
    
    # Generate based on hierarchy structure
    level_units = []
    for unit_id, unit_info in hierarchy.items():
        if unit_info.get('level') == level_number:
            level_units.append(unit_info.get('name', f'Unit_{unit_id}'))
    
    if level_units:
        # Use most common word in level names
        if len(level_units) == 1:
            return level_units[0].replace(' ', '_')
        else:
            # Find common pattern or use generic name
            return f"Level_{level_number}_Units"
    
    # Default naming
    level_names_default = {
        1: "Corporate",
        2: "Division", 
        3: "Department",
        4: "Team",
        5: "Unit"
    }
    
    return level_names_default.get(level_number, f"Level_{level_number}")

def validate_mapping_configuration(mapping_config):
    """Validate that mapping configuration has required fields"""
    
    required_columns = [
        'target_column1', 'target_column2', 'source_file', 
        'source_column', 'transformation', 'applies_to'
    ]
    
    if mapping_config is None or mapping_config.empty:
        return False, "Mapping configuration is empty"
    
    missing_columns = [col for col in required_columns if col not in mapping_config.columns]
    if missing_columns:
        return False, f"Missing required columns: {missing_columns}"
    
    # Check for Level and Association mappings
    level_mappings = mapping_config[mapping_config['applies_to'] == 'Level']
    association_mappings = mapping_config[mapping_config['applies_to'] == 'Association']
    
    if level_mappings.empty:
        return False, "No Level mappings found in configuration"
    
    if association_mappings.empty:
        return False, "No Association mappings found in configuration"
    
    return True, "Mapping configuration is valid"

def generate_output_files(state):
    """Generate all output files based on mapping configuration AND store for statistics analysis"""
    
    results = {
        'level_files': {},
        'association_files': {},
        'errors': []
    }
    
    try:
        # Validate mapping configuration
        mapping_config = load_mapping_configuration(state)
        is_valid, message = validate_mapping_configuration(mapping_config)
        
        if not is_valid:
            results['errors'].append(f"Mapping validation failed: {message}")
            return results
        
        # Get number of levels
        hierarchy = state.get('hierarchy_structure', {})
        max_level = max([info.get('level', 1) for info in hierarchy.values()]) if hierarchy else 1
        
        # Generate level files
        st.info(f"Generating files for {max_level} hierarchy levels...")
        for level_num in range(1, max_level + 1):
            output_df, filename = process_level_files(state, level_num)
            if output_df is not None:
                results['level_files'][level_num] = {
                    'data': output_df,
                    'filename': filename
                }
                st.success(f"Generated {filename}")
            else:
                results['errors'].append(f"Failed to generate Level {level_num}: {filename}")
        
        # Generate association files for levels 2 and above (not level 1)
        st.info("Generating association files for reporting relationships...")
        for level_num in range(2, max_level + 1):
            output_df, filename = process_association_files(state, level_num)
            if output_df is not None:
                results['association_files'][level_num] = {
                    'data': output_df,
                    'filename': filename
                }
                st.success(f"Generated {filename}")
            else:
                results['errors'].append(f"Failed to generate Association file for Level {level_num}: {filename}")
        
        # CRITICAL: Store generated files in session state for statistics panel
        state['generated_output_files'] = results
        
        # Also store generation timestamp and metadata
        state['output_generation_metadata'] = {
            'generated_at': datetime.now().isoformat(),
            'total_level_files': len(results['level_files']),
            'total_association_files': len(results['association_files']),
            'max_hierarchy_level': max_level,
            'mapping_config_used': mapping_config is not None,
            'total_errors': len(results['errors'])
        }
        
        st.success("✅ Generated files saved for statistics analysis!")
        
    except Exception as e:
        results['errors'].append(f"Error generating output files: {str(e)}")
    
    return results

def convert_df_to_excel(df):
    """Convert DataFrame to Excel format for download"""
    output = io.BytesIO()
    
    # Create workbook and worksheet
    wb = Workbook()
    ws = wb.active
    
    # Write DataFrame to worksheet
    for r in dataframe_to_rows(df, index=False, header=False):
        ws.append(r)
    
    wb.save(output)
    output.seek(0)
    return output.getvalue()

def analyze_hierarchy_structure(hrp1000_df, hrp1001_df):
    """Analyze and build hierarchy structure from the data"""
    if hrp1000_df is None or hrp1001_df is None:
        return {}
    
    # Build parent-child relationships
    relationships = {}
    for _, row in hrp1001_df.iterrows():
        if pd.notna(row.get('Source ID')) and pd.notna(row.get('Target object ID')):
            child_id = str(row['Source ID'])
            parent_id = str(row['Target object ID'])
            relationships[child_id] = parent_id
    
    # Determine levels
    hierarchy = {}
    
    # Find root nodes (nodes without parents)
    all_units = set(hrp1000_df['Object ID'].astype(str))
    child_units = set(relationships.keys())
    root_units = all_units - child_units
    
    # Assign levels starting from roots
    for unit_id in all_units:
        level = calculate_unit_level(unit_id, relationships)
        unit_name = hrp1000_df[hrp1000_df['Object ID'].astype(str) == unit_id]['Name'].iloc[0] if not hrp1000_df[hrp1000_df['Object ID'].astype(str) == unit_id].empty else f"Unit {unit_id}"
        
        hierarchy[unit_id] = {
            'name': unit_name,
            'level': level,
            'parent': relationships.get(unit_id),
            'children': [k for k, v in relationships.items() if v == unit_id]
        }
    
    return hierarchy

def calculate_unit_level(unit_id, relationships, visited=None):
    """Calculate the level of a unit in the hierarchy"""
    if visited is None:
        visited = set()
    
    if unit_id in visited:
        return 999  # Circular reference
    
    if unit_id not in relationships:
        return 1  # Root level
    
    visited.add(unit_id)
    parent_level = calculate_unit_level(relationships[unit_id], relationships, visited.copy())
    return parent_level + 1

def test_transformation_preview(state):
    """Test transformation preview to help debug mapping issues"""
    
    # Import required libraries
    import pandas as pd
    
    st.subheader("🧪 Transformation Testing")
    st.info("Test your column mappings and transformations with sample data")
    
    # Load mapping configuration
    mapping_config = load_mapping_configuration(state)
    
    if mapping_config is None or mapping_config.empty:
        st.warning("No mapping configuration found. Configure mappings in Admin panel first.")
        return
    
    # Get source data
    hrp1000_df = state.get('source_hrp1000')
    hrp1001_df = state.get('source_hrp1001')
    
    if hrp1000_df is None or hrp1001_df is None:
        st.warning("Upload source data files first.")
        return
    
    # Select mapping to test
    mapping_options = []
    for _, mapping in mapping_config.iterrows():
        label = f"{mapping['target_column1']} ({mapping['transformation']}) - {mapping['applies_to']}"
        mapping_options.append((label, mapping))
    
    if not mapping_options:
        st.warning("No mappings configured.")
        return
    
    selected_mapping_label = st.selectbox(
        "Select mapping to test:",
        [option[0] for option in mapping_options]
    )
    
    # Find the selected mapping
    selected_mapping = None
    for label, mapping in mapping_options:
        if label == selected_mapping_label:
            selected_mapping = mapping
            break
    
    if selected_mapping is None:
        return
    
    # Get appropriate source data
    if selected_mapping['source_file'] == 'HRP1000':
        source_df = hrp1000_df
    else:
        source_df = hrp1001_df
    
    # Show mapping details
    st.subheader("Mapping Details")
    col1, col2 = st.columns(2)
    
    with col1:
        st.write(f"**Target Column:** {selected_mapping['target_column1']}")
        st.write(f"**Display Name:** {selected_mapping['target_column2']}")
        st.write(f"**Source File:** {selected_mapping['source_file']}")
        st.write(f"**Source Column:** {selected_mapping['source_column']}")
    
    with col2:
        st.write(f"**Transformation:** {selected_mapping['transformation']}")
        st.write(f"**Default Value:** {selected_mapping['default_value']}")
        st.write(f"**Applies To:** {selected_mapping['applies_to']}")
        
        # Show additional fields for complex transformations
        if selected_mapping['transformation'] == 'Concatenate':
            st.write(f"**Secondary Column:** {selected_mapping.get('secondary_column', 'None')}")
        elif selected_mapping['transformation'] == 'Custom Python':
            st.write(f"**Custom Code:** `{selected_mapping.get('transformation_code', 'None')}`")
    
    # Test with sample data
    st.subheader("Test Results")
    
    if selected_mapping['source_column'] and selected_mapping['source_column'] in source_df.columns:
        # Get sample values
        sample_size = min(10, len(source_df))
        sample_data = source_df.head(sample_size)
        
        st.write("**Sample transformations:**")
        
        test_results = []
        for i, (_, row) in enumerate(sample_data.iterrows()):
            # Get original value
            original_value = row[selected_mapping['source_column']]
            
            # Apply transformation
            mapping_dict = selected_mapping.to_dict()
            transformed_value = apply_transformation(
                original_value, 
                selected_mapping['transformation'], 
                mapping_dict, 
                row, 
                source_df
            )
            
            test_results.append({
                'Row': i + 1,
                'Original Value': str(original_value) if not pd.isna(original_value) else "NULL",
                'Transformed Value': str(transformed_value) if not pd.isna(transformed_value) else "NULL",
                'Secondary Value': str(row.get(selected_mapping.get('secondary_column', ''), 'N/A')) if selected_mapping['transformation'] == 'Concatenate' else 'N/A'
            })
        
        # Show results in table
        results_df = pd.DataFrame(test_results)
        st.dataframe(results_df, use_container_width=True)
        
        # Show statistics
        st.subheader("Transformation Statistics")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            non_null_original = sum(1 for r in test_results if r['Original Value'] != 'NULL')
            st.metric("Non-null Source Values", f"{non_null_original}/{sample_size}")
        
        with col2:
            non_null_transformed = sum(1 for r in test_results if r['Transformed Value'] != 'NULL')
            st.metric("Non-null Transformed Values", f"{non_null_transformed}/{sample_size}")
        
        with col3:
            changed_values = sum(1 for r in test_results if r['Original Value'] != r['Transformed Value'])
            st.metric("Values Changed", f"{changed_values}/{sample_size}")
        
    else:
        if selected_mapping['source_column']:
            st.error(f"Source column '{selected_mapping['source_column']}' not found in {selected_mapping['source_file']}")
            st.write("**Available columns:**")
            st.write(list(source_df.columns))
        else:
            st.info("This mapping uses only default values (no source column)")
            default_val = selected_mapping['default_value']
            st.write(f"**Default value:** {default_val}")

def show_statistics_preview(state):
    """Show preview of what's available for statistics analysis"""
    
    generated_files = state.get('generated_output_files', {})
    metadata = state.get('output_generation_metadata', {})
    
    if generated_files:
        st.subheader("Statistics Integration Status")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Level Files", len(generated_files.get('level_files', {})))
            st.caption("For level analysis")
        
        with col2:
            st.metric("Association Files", len(generated_files.get('association_files', {})))
            st.caption("For relationship analysis")
        
        with col3:
            generation_time = metadata.get('generated_at', 'Unknown')
            if generation_time != 'Unknown':
                # Show time ago
                from datetime import datetime
                gen_time = datetime.fromisoformat(generation_time)
                time_diff = datetime.now() - gen_time
                if time_diff.seconds < 60:
                    time_ago = "Just now"
                elif time_diff.seconds < 3600:
                    time_ago = f"{time_diff.seconds // 60}m ago"
                else:
                    time_ago = f"{time_diff.seconds // 3600}h ago"
                st.metric("Generated", time_ago)
            else:
                st.metric("Generated", "Unknown")
            st.caption("Files ready for analysis")
        
        st.info("🔍 **Statistics Panel Ready:** Your generated files are now available for end-to-end analysis in the Statistics panel!")
        
        # Show sample of what's stored
        with st.expander("Preview Stored Data for Statistics"):
            for level_num, file_info in generated_files.get('level_files', {}).items():
                if 'data' in file_info:
                    data_shape = file_info['data'].shape
                    st.write(f"**Level {level_num}:** {data_shape[0]} rows × {data_shape[1]} columns")
            
            for level_num, file_info in generated_files.get('association_files', {}).items():
                if 'data' in file_info:
                    data_shape = file_info['data'].shape
                    st.write(f"**Association {level_num}:** {data_shape[0]} rows × {data_shape[1]} columns")

def show_hierarchy_panel(state):
    """Main hierarchy panel function with Streamlit UI"""
    
    # Custom CSS for professional styling
    st.markdown("""
    <style>
    .hierarchy-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 20px;
        border-radius: 10px;
        text-align: center;
        margin-bottom: 20px;
    }
    
    .level-card {
        background: var(--background-color);
        border: 1px solid var(--secondary-background-color);
        border-radius: 8px;
        padding: 15px;
        margin: 10px 0;
        border-left: 4px solid #007bff;
    }
    
    .success-card {
        background: rgba(22, 163, 74, 0.1);
        border: 1px solid rgba(22, 163, 74, 0.3);
        border-radius: 8px;
        padding: 15px;
        margin: 10px 0;
        border-left: 4px solid #16a34a;
    }
    
    .warning-card {
        background: rgba(245, 158, 11, 0.1);
        border: 1px solid rgba(245, 158, 11, 0.3);
        border-radius: 8px;
        padding: 15px;
        margin: 10px 0;
        border-left: 4px solid #f59e0b;
    }
    
    .error-card {
        background: rgba(239, 68, 68, 0.1);
        border: 1px solid rgba(239, 68, 68, 0.3);
        border-radius: 8px;
        padding: 15px;
        margin: 10px 0;
        border-left: 4px solid #ef4444;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Header
    st.markdown('''
    <div class="hierarchy-header">
        <h1>Organizational Hierarchy Management</h1>
        <p>Generate level-based business unit files and associations</p>
    </div>
    ''', unsafe_allow_html=True)
    
    # Data Upload Section
    st.subheader("Data Upload")
    st.info("**Upload your source data files to begin processing. HRP1000 contains organizational unit information, while HRP1001 contains the relationships between units (who reports to whom).**")
    
    # Check if source data is available
    hrp1000_df = state.get('source_hrp1000')
    hrp1001_df = state.get('source_hrp1001')
    
    # Show current data status
    col1, col2 = st.columns(2)
    
    with col1:
        if hrp1000_df is not None and not hrp1000_df.empty:
            st.success(f"HRP1000 Loaded ({len(hrp1000_df)} records)")
        else:
            st.error("HRP1000 Not Loaded")
    
    with col2:
        if hrp1001_df is not None and not hrp1001_df.empty:
            st.success(f"HRP1001 Loaded ({len(hrp1001_df)} records)")
        else:
            st.error("HRP1001 Not Loaded")
    
    # Upload interface
    if hrp1000_df is None or hrp1000_df.empty or hrp1001_df is None or hrp1001_df.empty:
        
        st.markdown("### Upload Your Files")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**HRP1000 - Organizational Units**")
            hrp1000_file = st.file_uploader(
                "Upload HRP1000 file",
                type=['xlsx', 'xls', 'csv'],
                key="hrp1000_upload",
                help="Upload your organizational units file"
            )
            
            if hrp1000_file is not None:
                try:
                    if hrp1000_file.name.endswith('.csv'):
                        hrp1000_temp = pd.read_csv(hrp1000_file)
                    else:
                        hrp1000_temp = pd.read_excel(hrp1000_file)
                    
                    st.success(f"File loaded: {len(hrp1000_temp)} rows, {len(hrp1000_temp.columns)} columns")
                    
                    # Show preview
                    with st.expander("Preview HRP1000 Data"):
                        st.dataframe(hrp1000_temp.head())
                    
                    # Save to state
                    if st.button("Process HRP1000", key="process_hrp1000"):
                        state['source_hrp1000'] = hrp1000_temp
                        st.success("HRP1000 data processed and saved!")
                        st.rerun()
                        
                except Exception as e:
                    st.error(f"Error reading HRP1000 file: {str(e)}")
        
        with col2:
            st.markdown("**HRP1001 - Relationships**")
            hrp1001_file = st.file_uploader(
                "Upload HRP1001 file",
                type=['xlsx', 'xls', 'csv'],
                key="hrp1001_upload",
                help="Upload your relationships file"
            )
            
            if hrp1001_file is not None:
                try:
                    if hrp1001_file.name.endswith('.csv'):
                        hrp1001_temp = pd.read_csv(hrp1001_file)
                    else:
                        hrp1001_temp = pd.read_excel(hrp1001_file)
                    
                    st.success(f"File loaded: {len(hrp1001_temp)} rows, {len(hrp1001_temp.columns)} columns")
                    
                    # Show preview
                    with st.expander("Preview HRP1001 Data"):
                        st.dataframe(hrp1001_temp.head())
                    
                    # Save to state
                    if st.button("Process HRP1001", key="process_hrp1001"):
                        state['source_hrp1001'] = hrp1001_temp
                        st.success("HRP1001 data processed and saved!")
                        st.rerun()
                        
                except Exception as e:
                    st.error(f"Error reading HRP1001 file: {str(e)}")
        
        # If both files are uploaded but not processed
        if hrp1000_file is not None and hrp1001_file is not None:
            if st.button("Process Both Files", type="primary"):
                try:
                    # Process HRP1000
                    if hrp1000_file.name.endswith('.csv'):
                        hrp1000_temp = pd.read_csv(hrp1000_file)
                    else:
                        hrp1000_temp = pd.read_excel(hrp1000_file)
                    
                    # Process HRP1001
                    if hrp1001_file.name.endswith('.csv'):
                        hrp1001_temp = pd.read_csv(hrp1001_file)
                    else:
                        hrp1001_temp = pd.read_excel(hrp1001_file)
                    
                    # Save both to state
                    state['source_hrp1000'] = hrp1000_temp
                    state['source_hrp1001'] = hrp1001_temp
                    
                    st.success("Both files processed successfully!")
                    st.rerun()
                    
                except Exception as e:
                    st.error(f"Error processing files: {str(e)}")
        
        st.divider()
    
    # Continue only if data is available
    if hrp1000_df is None or hrp1000_df.empty:
        st.warning("Please upload HRP1000 (Organizational Units) file to continue.")
        return
    
    if hrp1001_df is None or hrp1001_df.empty:
        st.warning("Please upload HRP1001 (Relationships) file to continue.")
        return
    
    # Load and validate mapping configuration
    mapping_config = load_mapping_configuration(state)
    is_valid, validation_message = validate_mapping_configuration(mapping_config)
    
    # Display mapping status
    col1, col2 = st.columns(2)
    
    with col1:
        if is_valid:
            st.markdown(f'''
            <div class="success-card">
                <h4>Mapping Configuration Loaded</h4>
                <p>{validation_message}</p>
                <p><strong>Level Mappings:</strong> {len(mapping_config[mapping_config['applies_to'] == 'Level'])}</p>
                <p><strong>Association Mappings:</strong> {len(mapping_config[mapping_config['applies_to'] == 'Association'])}</p>
            </div>
            ''', unsafe_allow_html=True)
        else:
            st.markdown(f'''
            <div class="warning-card">
                <h4>Using Default Mapping</h4>
                <p>{validation_message}</p>
                <p>Configure mappings in the Admin panel for custom fields.</p>
            </div>
            ''', unsafe_allow_html=True)
    
    with col2:
        if st.button("Refresh Mapping Config", help="Reload mapping configuration from Admin panel"):
            # Force refresh by clearing session state cache
            for key in ['mapping_config', 'current_mappings', 'admin_mappings']:
                if key in st.session_state:
                    del st.session_state[key]
            st.rerun()
    
    # Analyze hierarchy structure
    with st.spinner("Analyzing hierarchy structure..."):
        hierarchy = analyze_hierarchy_structure(hrp1000_df, hrp1001_df)
        state['hierarchy_structure'] = hierarchy
    
    if not hierarchy:
        st.error("Failed to analyze hierarchy structure from the data.")
        return
    
    # Display hierarchy summary
    max_level = max([info.get('level', 1) for info in hierarchy.values()])
    st.subheader("Hierarchy Analysis")
    st.info("**Your organizational structure has been analyzed and organized into hierarchy levels. Each level represents a tier in your organization, from top-level (Level 1) down to operational units.**")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Units", len(hierarchy))
        st.caption("Total organizational units found in your data")
    
    with col2:
        st.metric("Hierarchy Levels", max_level)
        st.caption("Number of organizational tiers (depth of hierarchy)")
    
    with col3:
        root_units = [uid for uid, info in hierarchy.items() if info.get('level') == 1]
        st.metric("Root Units", len(root_units))
        st.caption("Top-level units with no parent (CEO level)")
    
    with col4:
        leaf_units = [uid for uid, info in hierarchy.items() if not info.get('children')]
        st.metric("Leaf Units", len(leaf_units))
        st.caption("Bottom-level units with no subordinates")
    
    # Level names configuration
    st.subheader("Level Names Configuration")
    st.info("**Customize the names for each hierarchy level to match your organization's terminology. These names will be used in generated file names and throughout the system. Examples: Corporate, Division, Department, Team, etc.**")
    
    level_names = state.get('level_names', {})
    
    cols = st.columns(min(max_level, 5))
    for i in range(max_level):
        level_num = i + 1
        col_idx = i % 5
        
        with cols[col_idx]:
            default_name = get_level_name(level_num, state)
            level_names[level_num] = st.text_input(
                f"Level {level_num} Name:",
                value=level_names.get(level_num, default_name),
                key=f"level_name_{level_num}"
            )
    
    if st.button("Save Level Names"):
        state['level_names'] = level_names
        st.success("Level names saved!")
        st.rerun()
    
    # Show level breakdown
    st.subheader("Level Breakdown")
    
    for level_num in range(1, max_level + 1):
        level_units = [(uid, info) for uid, info in hierarchy.items() if info.get('level') == level_num]
        level_name = level_names.get(level_num, f"Level {level_num}")
        
        with st.expander(f"{level_name} ({len(level_units)} units)", expanded=False):
            if level_units:
                for uid, info in level_units[:10]:  # Show first 10
                    st.write(f"• **{info['name']}** (ID: {uid})")
                if len(level_units) > 10:
                    st.write(f"... and {len(level_units) - 10} more units")
            else:
                st.write("No units at this level")
    
    # File generation section
    st.subheader("Generate Output Files")
    st.info("**Generate Excel files organized by hierarchy level. Level files contain organizational units, while Association files define reporting relationships. These files are formatted for import into target systems.**")
    
    # Show current mapping preview
    with st.expander("Current Mapping Configuration", expanded=False):
        st.caption("**This shows how your source data fields are mapped to target system fields. Configured in the Admin panel.**")
        if not mapping_config.empty:
            st.dataframe(mapping_config, use_container_width=True)
        else:
            st.warning("No mapping configuration loaded")
    
    # FIXED: Check if files are already generated and show download buttons immediately
    existing_files = state.get('generated_output_files')
    if existing_files and (existing_files.get('level_files') or existing_files.get('association_files')):
        st.success("Files already generated! Ready for download:")
        
        # Level files
        if existing_files.get('level_files'):
            st.subheader("📁 Level Files")
            st.info("**Level files contain organizational units grouped by hierarchy level. Each level represents a different tier in your organizational structure (e.g., Corporate, Division, Department).**")
            
            for level_num, file_info in existing_files['level_files'].items():
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    st.write(f"**{file_info['filename']}**")
                    st.write(f"Contains {len(file_info['data'])-4} organizational units, {len(file_info['data'].columns)} data fields")
                    st.caption("This file contains all organizational units at this hierarchy level with their properties and metadata.")
                
                with col2:
                    st.download_button(
                        label="Download",
                        data=convert_df_to_excel(file_info['data']),
                        file_name=file_info['filename'],
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        key=f"existing_download_level_{level_num}"
                    )
        
        # Association files
        if existing_files.get('association_files'):
            st.subheader("🔗 Association Files")
            st.info("**Association files define reporting relationships between organizational units. They specify which units report to which parent units, creating the hierarchical structure.**")
            
            for level_num, file_info in existing_files['association_files'].items():
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    st.write(f"**{file_info['filename']}**")
                    st.write(f"Contains {len(file_info['data'])-4} reporting relationships, {len(file_info['data'].columns)} data fields")
                    st.caption(f"This file defines how Level {level_num} units report to their parent units in the hierarchy.")
                
                with col2:
                    st.download_button(
                        label="Download",
                        data=convert_df_to_excel(file_info['data']),
                        file_name=file_info['filename'],
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        key=f"existing_download_association_{level_num}"
                    )
        
        # Show statistics integration status
        show_statistics_preview(state)
        
        # Option to regenerate
        st.divider()
        if st.button("🔄 Regenerate All Files", help="Generate new files (will replace existing ones)"):
            # Clear existing files
            if 'generated_output_files' in state:
                del state['generated_output_files']
            if 'output_generation_metadata' in state:
                del state['output_generation_metadata']
            st.rerun()
    
    else:
        # Generate files for the first time
        if st.button("Generate All Files", type="primary"):
            with st.spinner("Generating files based on mapping configuration..."):
                results = generate_output_files(state)
            
            # Display results
            if results['errors']:
                st.error("Errors occurred during file generation:")
                for error in results['errors']:
                    st.write(f"• {error}")
            
            # Level files
            if results['level_files']:
                st.success(f"Generated {len(results['level_files'])} level files")
                st.info("**Level files contain organizational units grouped by hierarchy level. Each level represents a different tier in your organizational structure (e.g., Corporate, Division, Department).**")
                
                for level_num, file_info in results['level_files'].items():
                    col1, col2 = st.columns([3, 1])
                    
                    with col1:
                        st.write(f"**{file_info['filename']}**")
                        st.write(f"Contains {len(file_info['data'])-4} organizational units, {len(file_info['data'].columns)} data fields")
                        st.caption("This file contains all organizational units at this hierarchy level with their properties and metadata.")
                    
                    with col2:
                        st.download_button(
                            label="Download",
                            data=convert_df_to_excel(file_info['data']),
                            file_name=file_info['filename'],
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                            key=f"download_level_{level_num}"
                        )
            
            # Association files
            if results['association_files']:
                st.success(f"Generated {len(results['association_files'])} association files")
                st.info("**Association files define reporting relationships between organizational units. They specify which units report to which parent units, creating the hierarchical structure.**")
                
                for level_num, file_info in results['association_files'].items():
                    col1, col2 = st.columns([3, 1])
                    
                    with col1:
                        st.write(f"**{file_info['filename']}**")
                        st.write(f"Contains {len(file_info['data'])-4} reporting relationships, {len(file_info['data'].columns)} data fields")
                        st.caption(f"This file defines how Level {level_num} units report to their parent units in the hierarchy.")
                    
                    with col2:
                        st.download_button(
                            label="Download",
                            data=convert_df_to_excel(file_info['data']),
                            file_name=file_info['filename'],
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                            key=f"download_association_{level_num}"
                        )
            
            # Show statistics integration status
            show_statistics_preview(state)
    
    # Preview section
    st.subheader("File Preview")
    st.info("**Preview allows you to see the structure and first few rows of your generated files before downloading. This helps verify that the data transformation and mapping worked correctly.**")
    
    if st.button("Generate Preview"):
        preview_level = 1  # Preview first level
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**Level File Preview (Level 1):**")
            level_df, level_filename = process_level_files(state, preview_level)
            if level_df is not None:
                st.write(f"File: {level_filename}")
                st.caption("This shows organizational units at the top level of your hierarchy with all configured data fields.")
                st.dataframe(level_df.head(10), use_container_width=True)
            else:
                st.error("Failed to generate level preview")
        
        with col2:
            st.write("**Association File Preview (Level 2):**")
            # Preview associations for level 2 (first level that has parent relationships)
            hierarchy = state.get('hierarchy_structure', {})
            max_level = max([info.get('level', 1) for info in hierarchy.values()]) if hierarchy else 1
            
            if max_level >= 2:
                assoc_df, assoc_filename = process_association_files(state, 2)
                if assoc_df is not None:
                    st.write(f"File: {assoc_filename}")
                    st.caption("This shows how Level 2 units report to their parent units, defining the hierarchical structure.")
                    st.dataframe(assoc_df.head(10), use_container_width=True)
                else:
                    st.error("Failed to generate association preview")
            else:
                st.info("No association files needed - only one hierarchy level detected")
    
    # Transformation Testing
    st.divider()
    test_transformation_preview(state)
    
    # Debug information
    with st.expander("Debug Information", expanded=False):
        st.write("**Session State Keys:**")
        debug_keys = [k for k in state.keys() if 'mapping' in k.lower() or 'admin' in k.lower()]
        st.write(debug_keys)
        
        st.write("**Available Session State Mapping Keys:**")
        mapping_keys = [k for k in st.session_state.keys() if 'mapping' in k.lower() or 'admin' in k.lower()]
        st.write(mapping_keys)
        
        st.write("**Mapping Config Source:**")
        if 'mapping_config' in st.session_state:
            st.write("Found in 'mapping_config'")
        elif 'current_mappings' in st.session_state:
            st.write("Found in 'current_mappings'")
        elif 'admin_mappings' in st.session_state:
            st.write("Found in 'admin_mappings'")
        else:
            st.write("Using default mapping")
        
        st.write("**Hierarchy Structure Sample:**")
        if hierarchy:
            sample_hierarchy = dict(list(hierarchy.items())[:3])
            st.json(sample_hierarchy)