import streamlit as st
import pandas as pd
import os
import json
from pathlib import Path
from .utils.hierarchy_utils import get_default_mappings
from typing import List, Dict, Optional, Union
import io

# Constants
CONFIG_DIR = "configs"
PICKLIST_DIR = "picklists"
SOURCE_SAMPLES_DIR = "source_samples"
MAX_SAMPLE_ROWS = 1000

def initialize_directories() -> None:
    """Ensure all required directories exist."""
    for directory in [CONFIG_DIR, PICKLIST_DIR, SOURCE_SAMPLES_DIR]:
        Path(directory).mkdir(exist_ok=True)

# Session State Integration Functions
def save_config_with_session_state(config_type: str, config_data: Union[Dict, List]) -> None:
    """Save configuration to both file and session state for immediate access."""
    
    # Save to file (existing functionality)
    save_config(config_type, config_data)
    
    # Also save to session state for immediate access by other panels
    if config_type == "column_mappings":
        # Convert to DataFrame format that hierarchy panel expects
        if isinstance(config_data, list):
            mapping_df = pd.DataFrame(config_data)
        else:
            mapping_df = config_data
            
        # Save to multiple session state keys for compatibility
        st.session_state['mapping_config'] = mapping_df
        st.session_state['current_mappings'] = mapping_df
        st.session_state['admin_mappings'] = mapping_df
        
        st.success("Configuration saved to both file and session state!")
        st.info("Hierarchy panel can now access your custom mappings!")
        
    elif config_type in ["level", "association"]:
        # Save templates to session state
        st.session_state[f'{config_type}_template_config'] = config_data
        st.success(f"{config_type.title()} template saved!")

def load_config_with_session_state(config_type: str) -> Optional[Union[Dict, List]]:
    """Load configuration from session state first, then fall back to file."""
    
    # For column mappings, check session state first
    if config_type == "column_mappings":
        # Check session state first (most recent)
        if 'mapping_config' in st.session_state:
            config_data = st.session_state['mapping_config']
            if isinstance(config_data, pd.DataFrame):
                return config_data.to_dict('records')
            return config_data
        elif 'current_mappings' in st.session_state:
            config_data = st.session_state['current_mappings'] 
            if isinstance(config_data, pd.DataFrame):
                return config_data.to_dict('records')
            return config_data
    
    # Fall back to file-based loading
    return load_config(config_type)

def sync_session_state_on_load():
    """Sync existing file configs to session state when admin panel loads."""
    
    # Load and sync column mappings
    mappings = load_config("column_mappings")
    if mappings:
        mapping_df = pd.DataFrame(mappings)
        st.session_state['mapping_config'] = mapping_df
        st.session_state['current_mappings'] = mapping_df
        st.session_state['admin_mappings'] = mappings  # Keep as list too
    
    # Load and sync templates
    for template_type in ["level", "association"]:
        template_data = load_config(template_type)
        if template_data:
            st.session_state[f'{template_type}_template_config'] = template_data

def show_session_state_debug():
    """Debug function to show what's in session state."""
    
    st.subheader("Session State Debug")
    
    # Check mapping-related keys
    mapping_keys = [k for k in st.session_state.keys() if 'mapping' in k.lower() or 'admin' in k.lower()]
    
    st.write("**Mapping-related session state keys:**")
    if mapping_keys:
        for key in mapping_keys:
            value = st.session_state[key]
            if isinstance(value, pd.DataFrame):
                st.write(f"- {key}: DataFrame with {len(value)} rows")
            elif isinstance(value, list):
                st.write(f"- {key}: List with {len(value)} items")
            else:
                st.write(f"- {key}: {type(value)}")
    else:
        st.write("No mapping-related keys found")
    
    # Show all session state keys
    with st.expander("All Session State Keys", expanded=False):
        st.write(list(st.session_state.keys()))

# Transformation functions library
TRANSFORMATION_LIBRARY = {
    "None": "value",
    "UPPERCASE": "str(value).upper()",
    "lowercase": "str(value).lower()",
    "Title Case": "str(value).title()",
    "Trim Whitespace": "str(value).strip()",
    "Concatenate": "str(value1) + str(value2)",
    "Extract First Word": "str(value).split()[0]",
    "Date Format (YYYY-MM-DD)": "convert_german_date(value)",
    "Lookup Value": "lookup_value(value, picklist_source, picklist_column, default_value)",
    "Custom Python": "Enter Python expression using 'value'"
}

# Enhanced Python transformation templates
PYTHON_TEMPLATES = {
    "Date Operations": {
        "Convert German Date": "convert_german_date(value)",
        "Extract Year": "pd.to_datetime(value, errors='coerce').year if pd.notna(value) else ''",
        "Extract Month": "pd.to_datetime(value, errors='coerce').month if pd.notna(value) else ''",
        "Date Difference (Days)": "(pd.to_datetime(value) - pd.to_datetime('2024-01-01')).days if pd.notna(value) else 0",
        "Format Date (MM/DD/YYYY)": "pd.to_datetime(value, errors='coerce').strftime('%m/%d/%Y') if pd.notna(value) else ''",
        "Is Future Date": "'Yes' if pd.to_datetime(value, errors='coerce') > pd.Timestamp.now() else 'No'",
    },
    "Text Operations": {
        "Clean Whitespace": "str(value).strip() if pd.notna(value) else ''",
        "Extract First Word": "str(value).split()[0] if pd.notna(value) and str(value).strip() else ''",
        "Extract Last Word": "str(value).split()[-1] if pd.notna(value) and str(value).strip() else ''",
        "Remove Numbers": "''.join([c for c in str(value) if not c.isdigit()]) if pd.notna(value) else ''",
        "Extract Numbers Only": "''.join([c for c in str(value) if c.isdigit()]) if pd.notna(value) else ''",
        "Title Case": "str(value).title() if pd.notna(value) else ''",
        "Upper Case": "str(value).upper() if pd.notna(value) else ''",
        "Lower Case": "str(value).lower() if pd.notna(value) else ''",
        "Replace Text": "str(value).replace('OLD_TEXT', 'NEW_TEXT') if pd.notna(value) else ''",
        "Text Length": "len(str(value)) if pd.notna(value) else 0",
    },
    "Numeric Operations": {
        "Convert to Number": "float(value) if pd.notna(value) and str(value).replace('.', '').replace('-', '').isdigit() else 0",
        "Round to 2 Decimals": "round(float(value), 2) if pd.notna(value) and str(value).replace('.', '').replace('-', '').isdigit() else 0",
        "Absolute Value": "abs(float(value)) if pd.notna(value) and str(value).replace('.', '').replace('-', '').isdigit() else 0",
        "Add Fixed Amount": "float(value) + 100 if pd.notna(value) and str(value).replace('.', '').replace('-', '').isdigit() else 0",
        "Multiply by Factor": "float(value) * 1.1 if pd.notna(value) and str(value).replace('.', '').replace('-', '').isdigit() else 0",
        "Percentage": "f'{float(value) * 100:.1f}%' if pd.notna(value) and str(value).replace('.', '').replace('-', '').isdigit() else '0%'",
    },
    "Conditional Logic": {
        "If-Then-Else": "'Active' if str(value) == '1' else 'Inactive' if pd.notna(value) else 'Unknown'",
        "Multiple Conditions": "'High' if float(value) > 100 else 'Medium' if float(value) > 50 else 'Low' if pd.notna(value) else 'Unknown'",
        "Status Mapping": "{'1': 'Active', '2': 'Inactive', '3': 'Pending'}.get(str(value), 'Unknown')",
        "Empty Value Check": "'Has Value' if pd.notna(value) and str(value).strip() else 'Empty'",
        "Null to Default": "str(value) if pd.notna(value) and str(value).strip() else 'DEFAULT_VALUE'",
    },
    "Advanced Operations": {
        "Combine Two Columns": "f'{str(value)} - {str(secondary_value)}' if pd.notna(value) and pd.notna(secondary_value) else str(value) if pd.notna(value) else str(secondary_value) if pd.notna(secondary_value) else ''",
        "Extract Email Domain": "str(value).split('@')[1] if pd.notna(value) and '@' in str(value) else ''",
        "Phone Number Format": "f'({str(value)[:3]}) {str(value)[3:6]}-{str(value)[6:]}' if pd.notna(value) and len(str(value)) == 10 else str(value)",
        "Generate ID": "f'ID_{str(value).zfill(6)}' if pd.notna(value) else ''",
        "Hash Value": "str(hash(str(value)))[:8] if pd.notna(value) else ''",
    }
}

PYTHON_HELP_GUIDE = """
### Custom Python Transformation Guide

**Available Variables:**
- `value` - The current cell value from the source column
- `secondary_value` - Second column value (for concatenation)
- `pd` - Pandas library for data operations
- `pd.notna(value)` - Check if value is not null/empty

**Common Patterns:**
```python
# Safe string operations
str(value).strip() if pd.notna(value) else ''

# Safe numeric operations  
float(value) if pd.notna(value) and str(value).replace('.', '').isdigit() else 0

# Date operations
pd.to_datetime(value, errors='coerce').strftime('%Y-%m-%d') if pd.notna(value) else ''

# Conditional logic
'Active' if str(value) == '1' else 'Inactive' if pd.notna(value) else 'Unknown'

# Dictionary mapping
{'A': 'Apple', 'B': 'Banana'}.get(str(value), 'Unknown')
```

**Best Practices:**
- Always check for null values with `pd.notna(value)`
- Use `str(value)` to safely convert to string
- Handle edge cases with try-except or conditional logic
- Test your expressions with sample data first
- Keep expressions simple and readable
"""

# Default templates with descriptions
DEFAULT_TEMPLATES = {
    "level": [
        {"target_column1": "externalCode", "target_column2": "External Code", "description": "Unique identifier for the organizational unit"},
        {"target_column1": "name.en_US", "target_column2": "Name (English US)", "description": "Name in US English"},
        {"target_column1": "name.defaultValue", "target_column2": "Name (Default)", "description": "Default name value"},
        {"target_column1": "effectiveStartDate", "target_column2": "Start Date", "description": "Effective start date"},
        {"target_column1": "effectiveEndDate", "target_column2": "End Date", "description": "Effective end date"},
        {"target_column1": "effectiveStatus", "target_column2": "Status", "description": "Current status (Active/Inactive)"},
        {"target_column1": "Operator", "target_column2": "Operator", "description": "Operator information"},
        {"target_column1": "Object abbr.", "target_column2": "Object Abbreviation", "description": "Object abbreviation"}
    ],
    "association": [
        {"target_column1": "externalCode", "target_column2": "External Code", "description": "Unique identifier for the association"},
        {"target_column1": "effectiveStartDate", "target_column2": "Start Date", "description": "Effective start date"},
        {"target_column1": "effectiveEndDate", "target_column2": "End Date", "description": "Effective end date"},
        {"target_column1": "cust_toLegalEntity.externalCode", "target_column2": "Parent Entity Code", "description": "Parent reference"},
        {"target_column1": "relationshipType", "target_column2": "Relationship Type", "description": "Type of relationship"},
        {"target_column1": "effectiveStatus", "target_column2": "Status", "description": "Current status"}
    ]
}

def safe_get_sample_value(col_data: pd.Series) -> str:
    """Safely get sample value that won't cause Arrow serialization issues."""
    if len(col_data) > 0:
        sample = col_data.iloc[0]
        if pd.isna(sample):
            return "NULL"
        return str(sample) if not isinstance(sample, (str, int, float, bool)) else str(sample)
    return ""

def get_source_columns(source_file: str) -> List[str]:
    """Dynamically get columns from source files with caching."""
    try:
        sample_path = os.path.join(SOURCE_SAMPLES_DIR, f"{source_file}_sample.csv")
        if os.path.exists(sample_path):
            df = pd.read_csv(sample_path, nrows=1)
            return df.columns.tolist()
    except Exception as e:
        st.error(f"Error loading source columns: {str(e)}")
    
    # Fallback defaults for your data structure
    if source_file == "HRP1000":
        return ["Client", "Plan version", "Object type", "Object ID", "Planning status", "Start date", "End Date", "Name", "Object abbr."]
    elif source_file == "HRP1001":
        return ["Client", "Object type", "Source ID", "Plan version", "Relationship", "Planning status", "Start date", "End Date", "Target object ID"]
    return []

def get_picklist_columns(picklist_file: str) -> List[str]:
    """Get columns from picklist files with error handling."""
    try:
        df = pd.read_csv(f"{PICKLIST_DIR}/{picklist_file}", nrows=1)
        return df.columns.tolist()
    except Exception as e:
        st.error(f"Error loading picklist columns: {str(e)}")
        return []

def save_config(config_type: str, config_data: Union[Dict, List]) -> None:
    """Save configuration with atomic write pattern."""
    temp_path = f"{CONFIG_DIR}/{config_type}_config.tmp"
    final_path = f"{CONFIG_DIR}/{config_type}_config.json"
    
    try:
        with open(temp_path, "w") as f:
            json.dump(config_data, f, indent=2)
        if os.path.exists(temp_path):
            if os.path.exists(final_path):
                os.remove(final_path)
            os.rename(temp_path, final_path)
        st.success(f"{config_type} configuration saved successfully!")
    except Exception as e:
        st.error(f"Error saving config: {str(e)}")

def load_config(config_type: str) -> Optional[Union[Dict, List]]:
    """Load configuration with robust error handling."""
    try:
        config_path = f"{CONFIG_DIR}/{config_type}_config.json"
        if not os.path.exists(config_path):
            return None
            
        with open(config_path, "r") as f:
            data = json.load(f)
            
            if config_type in ["level", "association"]:
                if isinstance(data, str):
                    try:
                        data = json.loads(data)
                    except json.JSONDecodeError:
                        return None
                if not isinstance(data, list):
                    return None
            return data
    except Exception as e:
        st.error(f"Error loading config: {str(e)}")
        return None

def show_configuration_status():
    """Show current configuration status at the top"""
    st.subheader("Current Configuration Status")
    
    # Check configuration files
    config_files = [
        ("Level Template", "configs/level_config.json"),
        ("Association Template", "configs/association_config.json"), 
        ("Column Mappings", "configs/column_mappings_config.json")
    ]
    
    cols = st.columns(3)
    for i, (name, file) in enumerate(config_files):
        with cols[i]:
            if os.path.exists(file):
                st.success(f"Available: {name}")
                try:
                    with open(file, 'r') as f:
                        data = json.load(f)
                        st.caption(f"Items: {len(data)}")
                except:
                    st.caption("Status: Available")
            else:
                st.error(f"Missing: {name}")
    
    # Show quick stats
    st.subheader("Quick Stats")
    cols = st.columns(4)
    
    with cols[0]:
        if os.path.exists("picklists"):
            picklist_count = len([f for f in os.listdir("picklists") if f.endswith('.csv')])
            st.metric("Picklists", picklist_count)
        else:
            st.metric("Picklists", 0)
    
    with cols[1]:
        if os.path.exists("source_samples"):
            sample_count = len([f for f in os.listdir("source_samples") if f.endswith('.csv')])
            st.metric("Sample Files", sample_count)
        else:
            st.metric("Sample Files", 0)
    
    with cols[2]:
        mappings = load_config("column_mappings")
        if mappings:
            st.metric("Column Mappings", len(mappings))
        else:
            st.metric("Column Mappings", 0)
    
    with cols[3]:
        level_template = load_config("level")
        if level_template:
            st.metric("Level Fields", len(level_template))
        else:
            st.metric("Level Fields", 0)

def validate_sample_columns(source_file: str, sample_df: pd.DataFrame) -> tuple:
    """Validate sample files have required columns."""
    required_columns = {
        "HRP1000": ["Object ID", "Name"],
        "HRP1001": ["Source ID", "Target object ID"]
    }
    missing_cols = set(required_columns.get(source_file, [])) - set(sample_df.columns)
    if missing_cols:
        return False, f"Missing required columns: {', '.join(missing_cols)}"
    return True, "All required columns present"

def process_uploaded_file(uploaded_file, source_file_type: str) -> None:
    """Process and validate uploaded sample files."""
    try:
        if uploaded_file.name.endswith('.xlsx'):
            df = pd.read_excel(uploaded_file, nrows=MAX_SAMPLE_ROWS)
        else:
            df = pd.read_csv(uploaded_file, nrows=MAX_SAMPLE_ROWS)
        
        is_valid, message = validate_sample_columns(source_file_type, df)
        if not is_valid:
            st.error(message)
            return

        sample_path = os.path.join(SOURCE_SAMPLES_DIR, f"{source_file_type}_sample.csv")
        df.to_csv(sample_path, index=False)
        st.success(f"Sample {source_file_type} file saved successfully!")
        
        with st.expander("File Preview", expanded=True):
            st.dataframe(df.head().astype(str))
        
        st.subheader("Column Information")
        col_info = []
        for col in df.columns:
            col_info.append({
                "Column": col,
                "Type": str(df[col].dtype),
                "Unique Values": df[col].nunique(),
                "Sample Value": safe_get_sample_value(df[col])
            })
        st.dataframe(pd.DataFrame(col_info))
        
    except Exception as e:
        st.error(f"Error processing file: {str(e)}")

def convert_text_to_template(text_input: str) -> List[Dict]:
    """Convert text input to template format."""
    lines = [line.strip() for line in text_input.split('\n') if line.strip()]
    template = []
    for line in lines:
        parts = [part.strip() for part in line.split(',') if part.strip()]
        if len(parts) >= 2:
            template.append({
                "target_column1": parts[0],
                "target_column2": parts[1],
                "description": parts[2] if len(parts) > 2 else ""
            })
    return template

def convert_template_to_text(template: List[Dict]) -> str:
    """Convert template to text input format."""
    return '\n'.join([
        f"{item['target_column1']},{item['target_column2']},{item.get('description', '')}"
        for item in template
    ])

def render_template_editor(template_type: str) -> None:
    """Render the template editor with reordering and delete functionality."""
    st.subheader(f"{template_type} Template Configuration")
    
    # Load template or use defaults
    current_template = load_config(template_type.lower()) or DEFAULT_TEMPLATES[template_type.lower()]
    
    # Store the current template in session state if not already present
    if f"{template_type}_template" not in st.session_state:
        st.session_state[f"{template_type}_template"] = current_template.copy()
    
    # Edit mode selection
    edit_mode = st.radio(
        "Edit Mode:",
        ["Table Editor", "Text Input"],
        horizontal=True,
        key=f"{template_type}_edit_mode"
    )
    
    # Reset button
    if st.button(f"Reset {template_type} Template to Default"):
        st.session_state[f"{template_type}_template"] = DEFAULT_TEMPLATES[template_type.lower()].copy()
        save_config_with_session_state(template_type.lower(), st.session_state[f"{template_type}_template"])
        st.rerun()
    
    if edit_mode == "Table Editor":
        st.markdown("""
        **Instructions:**
        - Use up/down arrows to reorder rows
        - Use delete button to remove rows
        - Add new rows below
        - Edit cells directly
        - Save when done
        """)
        
        # Display each row with controls
        for i, row in enumerate(st.session_state[f"{template_type}_template"]):
            cols = st.columns([0.3, 2.5, 2.5, 2.5, 0.5, 0.5, 0.5])
            with cols[0]:
                st.caption(f"Row {i+1}")
            with cols[1]:
                row['target_column1'] = st.text_input(
                    "System Column Name",
                    value=row['target_column1'],
                    key=f"col1_{i}",
                    label_visibility="collapsed"
                )
            with cols[2]:
                row['target_column2'] = st.text_input(
                    "Display Name",
                    value=row['target_column2'],
                    key=f"col2_{i}",
                    label_visibility="collapsed"
                )
            with cols[3]:
                row['description'] = st.text_input(
                    "Description",
                    value=row.get('description', ''),
                    key=f"desc_{i}",
                    label_visibility="collapsed"
                )
            with cols[4]:
                if st.button("↑", key=f"up_{i}", disabled=(i == 0)):
                    st.session_state[f"{template_type}_template"][i], st.session_state[f"{template_type}_template"][i-1] = \
                        st.session_state[f"{template_type}_template"][i-1], st.session_state[f"{template_type}_template"][i]
                    st.rerun()
            with cols[5]:
                if st.button("↓", key=f"down_{i}", disabled=(i == len(st.session_state[f"{template_type}_template"])-1)):
                    st.session_state[f"{template_type}_template"][i], st.session_state[f"{template_type}_template"][i+1] = \
                        st.session_state[f"{template_type}_template"][i+1], st.session_state[f"{template_type}_template"][i]
                    st.rerun()
            with cols[6]:
                if st.button("Delete", key=f"del_{i}"):
                    del st.session_state[f"{template_type}_template"][i]
                    st.success("Row deleted!")
                    st.rerun()
        
        # Add new row
        st.subheader("Add New Row")
        new_cols = st.columns(3)
        with new_cols[0]:
            new_col1 = st.text_input("System Column Name", key="new_col1")
        with new_cols[1]:
            new_col2 = st.text_input("Display Name", key="new_col2")
        with new_cols[2]:
            new_desc = st.text_input("Description", key="new_desc")
        
        if st.button("Add Row"):
            if new_col1 and new_col2:
                st.session_state[f"{template_type}_template"].append({
                    "target_column1": new_col1,
                    "target_column2": new_col2,
                    "description": new_desc
                })
                st.success("Row added!")
                st.rerun()
            else:
                st.error("Please fill System Column Name and Display Name")
    
    else:  # Text Input mode
        text_content = st.text_area(
            "Edit template as text (CSV format: System Column,Display Name,Description)",
            value=convert_template_to_text(st.session_state[f"{template_type}_template"]),
            height=400,
            key=f"{template_type}_text_input"
        )
        
        if st.button("Apply Text Changes"):
            try:
                new_template = convert_text_to_template(text_content)
                st.session_state[f"{template_type}_template"] = new_template
                st.success("Template updated from text input!")
                st.rerun()
            except Exception as e:
                st.error(f"Error parsing text input: {str(e)}")
    
    # Save template
    if st.button(f"Save {template_type} Template", type="primary"):
        validation_errors = []
        for i, row in enumerate(st.session_state[f"{template_type}_template"]):
            if not row.get('target_column1'):
                validation_errors.append(f"Row {i+1}: Missing System Column Name")
            if not row.get('target_column2'):
                validation_errors.append(f"Row {i+1}: Missing Display Name")
        
        if validation_errors:
            st.error("Validation errors:\n" + "\n".join(validation_errors))
        else:
            save_config_with_session_state(template_type.lower(), st.session_state[f"{template_type}_template"])
            
            st.subheader("Saved Template Preview")
            cols = st.columns(2)
            with cols[0]:
                st.subheader("Table View")
                st.dataframe(pd.DataFrame(st.session_state[f"{template_type}_template"]))
            with cols[1]:
                st.subheader("Text View")
                st.code(convert_template_to_text(st.session_state[f"{template_type}_template"]))

def manage_picklists() -> None:
    """Render the picklist management interface."""
    st.subheader("Picklist Management")
    
    # Upload new picklists
    new_picklists = st.file_uploader(
        "Upload CSV picklist files",
        type=["csv"],
        accept_multiple_files=True,
        help="Upload CSV files to be used as picklist references for value translations"
    )
    
    if new_picklists:
        for file in new_picklists:
            try:
                pd.read_csv(file).to_csv(f"{PICKLIST_DIR}/{file.name}", index=False)
                st.success(f"Saved: {file.name}")
            except Exception as e:
                st.error(f"Error processing {file.name}: {str(e)}")
    
    # Create new picklist manually
    st.subheader("Create New Picklist")
    pl_name = st.text_input("Picklist Name", value="new_mapping.csv")
    sample_content = """code,label,description
1,Active,Active status
2,Inactive,Inactive status
3,Pending,Pending status"""
    pl_content = st.text_area(
        "CSV Content (header row first)",
        value=sample_content,
        height=150,
        help="Enter CSV content with header row first"
    )
    
    if st.button("Save Manual Picklist") and pl_name:
        try:
            if not pl_name.endswith(".csv"):
                pl_name += ".csv"
            from io import StringIO
            pd.read_csv(StringIO(pl_content)).to_csv(f"{PICKLIST_DIR}/{pl_name}", index=False)
            st.success(f"Picklist {pl_name} created!")
        except Exception as e:
            st.error(f"Error creating picklist: {str(e)}")
    
    # Display existing picklists
    st.subheader("Available Picklists")
    if os.path.exists(PICKLIST_DIR):
        picklists = sorted([f for f in os.listdir(PICKLIST_DIR) if f.endswith('.csv')])
        if not picklists:
            st.info("No picklists available yet")
        
        for pl in picklists:
            st.subheader(f"Picklist: {pl}")
            cols = st.columns([4, 1])
            with cols[0]:
                try:
                    df = pd.read_csv(f"{PICKLIST_DIR}/{pl}")
                    st.dataframe(df, use_container_width=True)
                    st.caption(f"Rows: {len(df)}, Columns: {len(df.columns)}")
                except Exception as e:
                    st.error(f"Error loading: {str(e)}")
            with cols[1]:
                if st.button(f"Delete {pl}", key=f"del_{pl}"):
                    try:
                        os.remove(f"{PICKLIST_DIR}/{pl}")
                        st.success(f"Deleted {pl}")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error deleting: {str(e)}")

def render_column_mapping_interface() -> None:
    """Render the column mapping configuration interface."""
    st.subheader("Column Mapping Configuration")
    
    current_mappings = load_config_with_session_state("column_mappings") or get_default_mappings()
    
    # Download current mappings
    if current_mappings:
        df_mappings = pd.DataFrame(current_mappings)
        st.download_button(
            "Download Current Mappings (CSV)",
            data=df_mappings.to_csv(index=False),
            file_name="current_mappings.csv",
            mime="text/csv",
            help="Download all current mappings as a CSV file"
        )
    
    # Add new mapping
    st.markdown("### Add New Column Mapping")
    
    # Basic mapping configuration
    cols = st.columns([2, 2, 1])
    with cols[0]:
        applies_to = st.selectbox("Applies To", ["Level", "Association", "Both"])
        
        # Get target options from templates
        target_options = []
        if applies_to in ["Level", "Both"]:
            level_template = load_config("level") or DEFAULT_TEMPLATES["level"]
            target_options.extend([f"{col['target_column1']} | {col['target_column2']}" for col in level_template])
        
        if applies_to in ["Association", "Both"]:
            assoc_template = load_config("association") or DEFAULT_TEMPLATES["association"]
            target_options.extend([f"{col['target_column1']} | {col['target_column2']}" for col in assoc_template])
        
        if target_options:
            target_selection = st.selectbox("Target Column", sorted(set(target_options)))
            target_col1, target_col2 = target_selection.split(" | ") if target_selection else ("", "")
            
            st.text_input("System Column Name", value=target_col1, disabled=True)
            st.text_input("Display Name", value=target_col2, disabled=True)
        else:
            st.error("No templates configured. Please set up templates first.")
            target_col1, target_col2 = "", ""
    
    with cols[1]:
        source_file = st.selectbox("Source File", ["HRP1000", "HRP1001"])
        source_columns = get_source_columns(source_file)
        source_col = st.selectbox("Source Column", [""] + source_columns, 
                                help="Leave empty if using only default value")
    
    with cols[2]:
        default_val = st.text_input("Default Value", 
                                  help="Value to use if source is empty")
        picklist_options = [""] + sorted([f for f in os.listdir(PICKLIST_DIR) if f.endswith('.csv')]) if os.path.exists(PICKLIST_DIR) else [""]
        picklist_file = st.selectbox("Picklist File", picklist_options)
    
    # Transformation rules
    st.markdown("#### Transformation Rules")
    trans_col1, trans_col2 = st.columns(2)
    with trans_col1:
        trans_type = st.selectbox("Transformation Type", list(TRANSFORMATION_LIBRARY.keys()))
    
    with trans_col2:
        picklist_col = ""
        second_col = ""
        custom_code = ""
        
        if trans_type == "Concatenate":
            second_col = st.selectbox("Second Column", [""] + source_columns)
        elif trans_type == "Lookup Value":
            if picklist_file:
                picklist_col = st.selectbox("Picklist Column", [""] + get_picklist_columns(picklist_file))
            else:
                st.warning("Select a picklist file first")
    
    # Custom Python handling
    if trans_type == "Custom Python":
        st.markdown("#### Custom Python Transformation")
        
        # Template selection
        template_col1, template_col2 = st.columns([1, 1])
        
        with template_col1:
            st.markdown("**Quick Templates:**")
            template_category = st.selectbox(
                "Select Category",
                list(PYTHON_TEMPLATES.keys()),
                help="Choose a category to see pre-built templates"
            )
            
            if template_category:
                template_name = st.selectbox(
                    "Select Template",
                    list(PYTHON_TEMPLATES[template_category].keys()),
                    help="Choose a pre-built template to use"
                )
                
                if st.button("Use Template"):
                    template_code = PYTHON_TEMPLATES[template_category][template_name]
                    st.session_state.custom_python_code = template_code
                    st.success(f"Template '{template_name}' loaded!")
                    st.rerun()
        
        with template_col2:
            st.markdown("**Quick Help:**")
            show_help = st.checkbox("Show Python Guide")
        
        # Show help if requested
        if show_help:
            st.markdown("**Python Guide:**")
            st.code("""
# Available Variables:
# - value: current cell value
# - secondary_value: second column value  
# - pd: pandas library

# Examples:
str(value).strip() if pd.notna(value) else ''
'Active' if str(value) == '1' else 'Inactive'
{'A': 'Apple', 'B': 'Banana'}.get(str(value), 'Unknown')
            """, language='python')
        
        # Code editor
        st.markdown("**Python Expression Editor:**")
        custom_code = st.text_area(
            "Enter your Python expression",
            value=st.session_state.get('custom_python_code', 'value'),
            height=120,
            help="Use 'value' to reference the source column value.",
            key="python_code_editor"
        )
        
        # Store the code in session state
        st.session_state.custom_python_code = custom_code
        
        # Code validation
        if custom_code != 'value':
            try:
                # Basic syntax check
                compile(custom_code, '<string>', 'eval')
                st.success("Python syntax is valid")
            except SyntaxError as e:
                st.error(f"Syntax Error: {e}")
            except Exception as e:
                st.warning(f"Warning: {e}")
        
        # Show current template preview
        if template_category and template_name:
            current_template = PYTHON_TEMPLATES[template_category][template_name]
            st.markdown("**Current Template:**")
            st.code(current_template, language='python')
    
    # Reset session state for non-custom python
    if trans_type != "Custom Python":
        if 'custom_python_code' in st.session_state:
            del st.session_state.custom_python_code
    
    # Add mapping button
    st.markdown("---")
    if st.button("Add Mapping", type="primary"):
        if not all([target_col1, target_col2, applies_to, source_file]):
            st.error("Please fill all required fields")
        elif not source_col and not default_val:
            st.error("Either Source Column or Default Value must be provided")
        else:
            new_mapping = {
                "target_column1": target_col1,
                "target_column2": target_col2,
                "source_file": source_file,
                "source_column": source_col if source_col else "",
                "transformation": trans_type,
                "transformation_code": TRANSFORMATION_LIBRARY.get(trans_type, "value"),
                "default_value": default_val,
                "picklist_source": picklist_file,
                "picklist_column": picklist_col if trans_type == "Lookup Value" else "",
                "applies_to": applies_to
            }
            
            if trans_type == "Concatenate":
                new_mapping["secondary_column"] = second_col
            elif trans_type == "Custom Python":
                new_mapping["transformation_code"] = custom_code
            
            updated_mappings = current_mappings + [new_mapping]
            save_config_with_session_state("column_mappings", updated_mappings)
            st.rerun()
    
    # Display current mappings
    st.subheader("Current Column Mappings")
    if not current_mappings:
        st.info("No mappings configured yet")
    else:
        for i, mapping in enumerate(current_mappings):
            st.markdown(f"#### Mapping {i+1}: {mapping.get('target_column1', 'Unknown')}")
            
            cols = st.columns([3, 3, 2])
            with cols[0]:
                st.info(f"**Target:** {mapping.get('target_column1', '')}")
                st.info(f"**Display:** {mapping.get('target_column2', '')}")
            with cols[1]:
                st.info(f"**Source File:** {mapping.get('source_file', '')}")
                st.info(f"**Source Column:** {mapping.get('source_column', 'None')}")
            with cols[2]:
                st.info(f"**Transformation:** {mapping.get('transformation', 'None')}")
                st.info(f"**Applies To:** {mapping.get('applies_to', '')}")
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button(f"Edit Mapping {i+1}", key=f"edit_{i}"):
                    st.session_state[f'editing_mapping_{i}'] = True
                    st.rerun()
            with col2:
                if st.button(f"Delete Mapping {i+1}", key=f"delete_{i}"):
                    del current_mappings[i]
                    save_config_with_session_state("column_mappings", current_mappings)
                    st.success(f"Mapping {i+1} deleted!")
                    st.rerun()
            
            # Show edit form if this mapping is being edited
            if st.session_state.get(f'editing_mapping_{i}', False):
                st.subheader(f"Edit Mapping {i+1}")
                
                edit_col1, edit_col2 = st.columns(2)
                with edit_col1:
                    new_applies_to = st.selectbox("Applies To", ["Level", "Association", "Both"], 
                                                index=["Level", "Association", "Both"].index(mapping.get('applies_to', 'Level')),
                                                key=f"edit_applies_{i}")
                    new_source_file = st.selectbox("Source File", ["HRP1000", "HRP1001"],
                                                 index=["HRP1000", "HRP1001"].index(mapping.get('source_file', 'HRP1000')),
                                                 key=f"edit_source_file_{i}")
                    source_columns = get_source_columns(new_source_file)
                    current_source_col = mapping.get('source_column', '')
                    source_col_options = [""] + source_columns
                    source_col_index = source_col_options.index(current_source_col) if current_source_col in source_col_options else 0
                    new_source_col = st.selectbox("Source Column", source_col_options,
                                                index=source_col_index, key=f"edit_source_col_{i}")
                
                with edit_col2:
                    new_transformation = st.selectbox("Transformation", list(TRANSFORMATION_LIBRARY.keys()),
                                                    index=list(TRANSFORMATION_LIBRARY.keys()).index(mapping.get('transformation', 'None')),
                                                    key=f"edit_trans_{i}")
                    new_default_val = st.text_input("Default Value", value=mapping.get('default_value', ''),
                                                  key=f"edit_default_{i}")
                    
                    picklist_options = [""] + sorted([f for f in os.listdir(PICKLIST_DIR) if f.endswith('.csv')]) if os.path.exists(PICKLIST_DIR) else [""]
                    current_picklist = mapping.get('picklist_source', '')
                    picklist_index = picklist_options.index(current_picklist) if current_picklist in picklist_options else 0
                    new_picklist_file = st.selectbox("Picklist File", picklist_options,
                                                   index=picklist_index, key=f"edit_picklist_{i}")
                
                # Handle transformation-specific fields
                new_picklist_col = ""
                new_second_col = ""
                new_custom_code = ""
                
                if new_transformation == "Concatenate":
                    current_second_col = mapping.get('secondary_column', '')
                    second_col_options = [""] + source_columns
                    second_col_index = second_col_options.index(current_second_col) if current_second_col in second_col_options else 0
                    new_second_col = st.selectbox("Second Column", second_col_options,
                                                index=second_col_index, key=f"edit_second_{i}")
                elif new_transformation == "Lookup Value" and new_picklist_file:
                    picklist_cols = get_picklist_columns(new_picklist_file)
                    current_picklist_col = mapping.get('picklist_column', '')
                    picklist_col_options = [""] + picklist_cols
                    picklist_col_index = picklist_col_options.index(current_picklist_col) if current_picklist_col in picklist_col_options else 0
                    new_picklist_col = st.selectbox("Picklist Column", picklist_col_options,
                                                  index=picklist_col_index, key=f"edit_picklist_col_{i}")
                elif new_transformation == "Custom Python":
                    new_custom_code = st.text_area("Python Expression", 
                                                  value=mapping.get('transformation_code', 'value'),
                                                  key=f"edit_custom_{i}")
                
                # Save/Cancel buttons
                save_col, cancel_col = st.columns(2)
                with save_col:
                    if st.button(f"Save Changes {i+1}", key=f"save_{i}"):
                        # Update the mapping
                        current_mappings[i].update({
                            'applies_to': new_applies_to,
                            'source_file': new_source_file,
                            'source_column': new_source_col,
                            'transformation': new_transformation,
                            'default_value': new_default_val,
                            'picklist_source': new_picklist_file,
                            'picklist_column': new_picklist_col,
                            'transformation_code': TRANSFORMATION_LIBRARY.get(new_transformation, "value")
                        })
                        
                        if new_transformation == "Concatenate":
                            current_mappings[i]['secondary_column'] = new_second_col
                        elif new_transformation == "Custom Python":
                            current_mappings[i]['transformation_code'] = new_custom_code
                        
                        save_config_with_session_state("column_mappings", current_mappings)
                        del st.session_state[f'editing_mapping_{i}']
                        st.success(f"Mapping {i+1} updated!")
                        st.rerun()
                
                with cancel_col:
                    if st.button(f"Cancel Edit {i+1}", key=f"cancel_{i}"):
                        del st.session_state[f'editing_mapping_{i}']
                        st.rerun()
            
            st.markdown("---")

def show_admin_panel(state=None) -> None:
    """Main admin panel interface with professional styling."""
    
    # Professional CSS without emojis
    st.markdown("""
    <style>
    .admin-cockpit {
        background: linear-gradient(135deg, 
            rgba(15, 23, 42, 0.95) 0%, 
            rgba(30, 41, 59, 0.95) 25%, 
            rgba(51, 65, 85, 0.95) 50%, 
            rgba(30, 41, 59, 0.95) 75%, 
            rgba(15, 23, 42, 0.95) 100%);
        border-radius: 15px;
        padding: 20px;
        margin: 10px 0;
        border: 2px solid #475569;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
    }
    
    .cockpit-header {
        background: linear-gradient(90deg, #1e40af, #3b82f6, #1e40af);
        color: white;
        padding: 15px;
        border-radius: 10px;
        text-align: center;
        font-weight: bold;
        font-size: 24px;
        margin-bottom: 20px;
        box-shadow: 0 4px 15px rgba(59, 130, 246, 0.4);
    }
    
    .cockpit-panel {
        background: rgba(15, 23, 42, 0.8);
        border-radius: 10px;
        padding: 15px;
        margin: 10px 0;
        border: 1px solid #475569;
        backdrop-filter: blur(10px);
    }
    
    .status-indicator {
        background: rgba(0, 0, 0, 0.5);
        border-radius: 8px;
        padding: 10px;
        margin: 5px 0;
        border-left: 4px solid #10b981;
    }
    
    .metric-panel {
        background: rgba(15, 23, 42, 0.9);
        border-radius: 8px;
        padding: 10px;
        text-align: center;
        border: 1px solid #374151;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Header without emojis
    st.markdown('<div class="cockpit-header">ADMIN CONFIGURATION CENTER</div>', unsafe_allow_html=True)
    
    # Wrap everything in cockpit container
    st.markdown('<div class="admin-cockpit">', unsafe_allow_html=True)
    
    # Initialize directories
    initialize_directories()
    
    # Sync existing configs to session state
    sync_session_state_on_load()
    
    # Show configuration status at top
    show_configuration_status()
    
    st.divider()
    
    # Main tabs
    tab1, tab2, tab3, tab4 = st.tabs([
        "Source File Samples",
        "Output Templates", 
        "Picklist Management", 
        "Column Mapping"
    ])

    with tab1:
        st.markdown("### Upload Sample Source Files")
        st.info("Upload sample files to discover available columns for mapping configuration")
        
        source_file_type = st.radio("Select source file type:", 
                                  ["HRP1000", "HRP1001"],
                                  horizontal=True)
        
        uploaded_file = st.file_uploader(
            f"Upload {source_file_type} sample file (CSV or Excel)",
            type=["csv", "xlsx"],
            key=f"{source_file_type}_upload",
            help="Upload a sample file to analyze column structure"
        )
        
        if uploaded_file:
            process_uploaded_file(uploaded_file, source_file_type)
        
        # Show current sample information
        sample_path = os.path.join(SOURCE_SAMPLES_DIR, f"{source_file_type}_sample.csv")
        if os.path.exists(sample_path):
            st.subheader("Current Sample Information")
            try:
                df = pd.read_csv(sample_path)
                st.success(f"Current sample: {len(df)} rows, {len(df.columns)} columns")
                
                is_valid, message = validate_sample_columns(source_file_type, df)
                if is_valid:
                    st.success(f"{message}")
                else:
                    st.error(f"{message}")
                
                # Show columns in a simple format
                st.markdown("**Available Columns:**")
                cols = st.columns(3)
                for i, col in enumerate(df.columns):
                    with cols[i % 3]:
                        st.write(f"• {col}")
                
            except Exception as e:
                st.error(f"Error loading sample: {str(e)}")
        else:
            st.info(f"No sample file uploaded for {source_file_type} yet")

    with tab2:
        st.markdown("### Configure Output Templates")
        st.info("Define the structure and fields for your export files")
        
        template_type = st.radio("Select template type:", 
                               ["Level", "Association"],
                               horizontal=True,
                               key="template_type_radio")
        render_template_editor(template_type)

    with tab3:
        manage_picklists()

    with tab4:
        render_column_mapping_interface()
    
    # Footer with helpful information
    st.divider()
    st.markdown("### Quick Help")
    
    # Use columns instead of nested expanders
    help_col1, help_col2 = st.columns(2)
    
    with help_col1:
        st.markdown("#### Admin Workflow Guide")
        st.markdown("""
        **Recommended Setup Steps:**
        
        1. **Source Samples**: Upload sample files
        2. **Templates**: Configure export structure
        3. **Picklists**: Create lookup tables
        4. **Mappings**: Map columns & transformations
        5. **Test**: Process data in Hierarchy panel
        """)
    
    with help_col2:
        st.markdown("#### System Features")
        st.markdown("""
        **Current Capabilities:**
        - German date conversion (dd.mm.yyyy → yyyy-mm-dd)
        - Status code mapping (1→Active, 2→Inactive)
        - Text transformations (trim, title case)
        - Configurable output templates
        - Level-wise exports with hierarchy
        - Association relationship mapping
        """)
    
    # Debug section
    st.markdown("### Debug & Session State")
    show_debug = st.checkbox("Show Debug Information")
    
    if show_debug:
        show_session_state_debug()
        
        if st.button("Force Sync Session State"):
            sync_session_state_on_load()
            st.success("Session state synced!")
            st.rerun()
    
    # Show system health
    st.sidebar.markdown("### System Health")
    
    # Check system components
    health_items = [
        ("Templates", bool(load_config("level") and load_config("association"))),
        ("Mappings", bool(load_config("column_mappings"))),
        ("Picklists", os.path.exists(PICKLIST_DIR) and any(f.endswith('.csv') for f in os.listdir(PICKLIST_DIR))),
        ("Samples", os.path.exists(SOURCE_SAMPLES_DIR) and any(f.endswith('.csv') for f in os.listdir(SOURCE_SAMPLES_DIR)))
    ]
    
    for item, status in health_items:
        if status:
            st.sidebar.success(f"Available: {item}")
        else:
            st.sidebar.error(f"Missing: {item}")
    
    # Overall health
    overall_health = sum(status for _, status in health_items) / len(health_items)
    if overall_health == 1.0:
        st.sidebar.success("System Fully Configured!")
    elif overall_health >= 0.75:
        st.sidebar.warning("System Mostly Ready")
    else:
        st.sidebar.error("System Needs Configuration")
