import streamlit as st
import pandas as pd
import os
import json
from pathlib import Path
# from utils.hierarchy_utils import get_default_mappings
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

# Transformation functions library
TRANSFORMATION_LIBRARY = {
    "None": "value",
    "UPPERCASE": "str(value).upper()",
    "lowercase": "str(value).lower()",
    "Title Case": "str(value).title()",
    "Trim Whitespace": "str(value).strip()",
    "Concatenate": "str(value1) + str(value2)",
    "Extract First Word": "str(value).split()[0]",
    "Date Format (YYYY-MM-DD)": "pd.to_datetime(value).strftime('%Y-%m-%d')",
    "Lookup Value": "picklist_lookup(value, picklist_name, picklist_column)",
    "Custom Python": "Enter Python expression using 'value'"
}

PYTHON_TRANSFORMATION_GUIDE = """
### Python Transformation Guide
- Use `value` to reference the source column value
- For date transformations: `pd.to_datetime(value).strftime('%Y-%m-%d')`
- For numeric operations: `float(value) * 1.1`
- For conditional logic: `'Active' if value == 'A' else 'Inactive'`
- Always handle potential None/NA values
- Keep expressions simple and test them thoroughly
"""

# Default templates with descriptions
DEFAULT_TEMPLATES = {
    # Foundation Data
    "level": [
        {"target_column1": "effectiveStartDate", "target_column2": "Start Date", "description": "Effective start date of the level"},
        {"target_column1": "externalCode", "target_column2": "Code", "description": "Unique identifier for the level"},
        {"target_column1": "name.en_US", "target_column2": "US English", "description": "Name in US English"},
        {"target_column1": "name.defaultValue", "target_column2": "Default Value", "description": "Default name value"},
        {"target_column1": "effectiveStatus", "target_column2": "Status", "description": "Current status (Active/Inactive)"},
        {"target_column1": "headOfUnit", "target_column2": "Head of Unit", "description": "Person in charge of this unit"}
    ],
    "association": [
        {"target_column1": "externalCode", "target_column2": "Code", "description": "Unique identifier for the association"},
        {"target_column1": "effectiveStartDate", "target_column2": "Start Date", "description": "Effective start date"},
        {"target_column1": "cust_toLegalEntity.externalCode", "target_column2": "Business Unit.Company", "description": "Legal entity reference"}
    ],
    # Payroll Data
    "pa0008": [
        {"target_column1": "employee_id", "target_column2": "Employee ID", "description": "Unique employee identifier"},
        {"target_column1": "start_date", "target_column2": "Start Date", "description": "Start of payroll period"},
        {"target_column1": "end_date", "target_column2": "End Date", "description": "End of payroll period"},
        {"target_column1": "amount", "target_column2": "Amount", "description": "Payment amount"}
    ],
    "pa0014": [
        {"target_column1": "employee_id", "target_column2": "Employee ID", "description": "Unique employee identifier"},
        {"target_column1": "wage_type", "target_column2": "Wage Type", "description": "Type of wage"},
        {"target_column1": "amount", "target_column2": "Amount", "description": "Wage amount"},
        {"target_column1": "currency", "target_column2": "Currency", "description": "Payment currency"}
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
            df = pd.read_csv(sample_path, nrows=1)  # Only read headers
            return df.columns.tolist()
    except Exception as e:
        st.error(f"Error loading source columns: {str(e)}")
    
    # Fallback defaults
    if source_file == "HRP1000":
        return ["Object ID", "Name", "Description", "Start date", "Manager ID"]
    elif source_file == "HRP1001":
        return ["Source ID", "Target object ID", "Parent ID", "Start date"]
    return []

def get_picklist_columns(picklist_file: str) -> List[str]:
    """Get columns from picklist files with error handling."""
    try:
        df = pd.read_csv(f"{PICKLIST_DIR}/{picklist_file}", nrows=1)  # Only read headers
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
        # Atomic rename
        if os.path.exists(temp_path):
            if os.path.exists(final_path):
                os.remove(final_path)
            os.rename(temp_path, final_path)
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

def validate_sample_columns(source_file: str, sample_df: pd.DataFrame) -> tuple:
    """Validate sample files have required columns."""
    required_columns = {
        "HRP1000": ["Object ID", "Name", "Start date"],
        "HRP1001": ["Source ID", "Target object ID", "Start date"]
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
    if st.button("Reset to Default Templates"):
        st.session_state[f"{template_type}_template"] = DEFAULT_TEMPLATES[template_type.lower()].copy()
        save_config(template_type.lower(), st.session_state[f"{template_type}_template"])
        st.success(f"{template_type} template reset to default values!")
        st.rerun()
    
    if edit_mode == "Table Editor":
        st.markdown("""
        **Instructions:**
        1. Use the up/down buttons to reorder rows
        2. Use the trash can (🗑️) button to delete rows
        3. Add new rows at the bottom
        4. Edit cells directly
        5. Click "Save Template" when done
        """)
        
        # Display each row with reorder and delete controls
        for i, row in enumerate(st.session_state[f"{template_type}_template"]):
            cols = st.columns([0.5, 3, 3, 3, 1, 1, 1])  # Added extra column for delete button
            with cols[0]:
                st.write(f"{i+1}.")
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
                # Up button - disabled for first row
                if st.button("↑", key=f"up_{i}", disabled=(i == 0)):
                    st.session_state[f"{template_type}_template"][i], st.session_state[f"{template_type}_template"][i-1] = \
                        st.session_state[f"{template_type}_template"][i-1], st.session_state[f"{template_type}_template"][i]
                    st.rerun()
            with cols[5]:
                # Down button - disabled for last row
                if st.button("↓", key=f"down_{i}", disabled=(i == len(st.session_state[f"{template_type}_template"])-1)):
                    st.session_state[f"{template_type}_template"][i], st.session_state[f"{template_type}_template"][i+1] = \
                        st.session_state[f"{template_type}_template"][i+1], st.session_state[f"{template_type}_template"][i]
                    st.rerun()
            with cols[6]:
                # Delete button with trash can icon
                if st.button("🗑️", key=f"del_{i}"):
                    del st.session_state[f"{template_type}_template"][i]
                    st.success("Row deleted!")
                    st.rerun()
        
        # Add new row
        with st.expander("➕ Add New Row", expanded=False):
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
    
    else:  # Text Input mode
        text_content = st.text_area(
            "Edit template as text (CSV format: System Column,Display Name,Description)",
            value=convert_template_to_text(st.session_state[f"{template_type}_template"]),
            height=300,
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
    
    if st.button("Save Template"):
        validation_errors = []
        for i, row in enumerate(st.session_state[f"{template_type}_template"]):
            if not row.get('target_column1'):
                validation_errors.append(f"Row {i+1}: Missing System Column Name")
            if not row.get('target_column2'):
                validation_errors.append(f"Row {i+1}: Missing Display Name")
        
        if validation_errors:
            st.error("Validation errors:\n" + "\n".join(validation_errors))
        else:
            save_config(template_type.lower(), st.session_state[f"{template_type}_template"])
            st.success(f"{template_type} template saved successfully!")
            
            with st.expander("Saved Template Preview", expanded=True):
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
    
    new_picklists = st.file_uploader(
        "Upload CSV picklist files",
        type=["csv"],
        accept_multiple_files=True,
        help="Upload CSV files to be used as picklist references"
    )
    
    if new_picklists:
        for file in new_picklists:
            try:
                pd.read_csv(file).to_csv(f"{PICKLIST_DIR}/{file.name}", index=False)
                st.success(f"Saved: {file.name}")
            except Exception as e:
                st.error(f"Error processing {file.name}: {str(e)}")
    
    with st.expander("➕ Create New Picklist", expanded=False):
        pl_name = st.text_input("Picklist Name (must end with .csv)", value="status_mapping.csv")
        sample_content = """status_code,status_label,is_active\nACT,Active,1\nINA,Inactive,0\nPND,Pending,1\nDEL,Deleted,0"""
        pl_content = st.text_area(
            "Comma-separated values (header row first)",
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
    
    st.subheader("Available Picklists")
    if os.path.exists(PICKLIST_DIR):
        picklists = sorted([f for f in os.listdir(PICKLIST_DIR) if f.endswith('.csv')])
        if not picklists:
            st.info("No picklists available yet")
        
        for pl in picklists:
            with st.expander(pl, expanded=False):
                cols = st.columns([4, 1])
                with cols[0]:
                    try:
                        df = pd.read_csv(f"{PICKLIST_DIR}/{pl}")
                        st.dataframe(df)
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

def render_column_mapping_interface():
    st.subheader("🧩 Column Mapping Configuration")

    # CSV Export
    col1, _ = st.columns([1, 4])
    with col1:
        if st.button("Download Current Mappings (CSV)"):
            mappings_df = pd.read_csv("config/column_mapping.csv")
            st.download_button("Download Mappings", data=mappings_df.to_csv(index=False), file_name="column_mapping.csv")

    st.markdown("### ➕ Add New Mapping")

def render_column_mapping_interface(mode="foundation"):
    if mode == "payroll":
        applies_to_options = ["PA0008", "PA0014"]
        source_file_options = ["PA0008", "PA0014"]
    else:
        applies_to_options = ["Level", "Association"]
        source_file_options = ["HRP1000", "HRP1001"]


    applies_to = st.selectbox("Applies To*", applies_to_options)
    source_file = st.selectbox("Source File*", source_file_options)
    # Load available columns from uploaded sample files
    available_source_columns = get_source_columns(source_file)
    if not available_source_columns:
        st.warning(f"⚠️ No uploaded sample file found for {source_file}. Please upload one under 'Source File Samples'.")
        return

    template = load_config(source_file.lower()) or DEFAULT_TEMPLATES.get(source_file.lower(), {})

    if not template:
        st.error(f"No template found for source file: {source_file}")
        return

    all_target_keys = list(template.keys())

    target_display_options = [f"{key} | {template[key].get('display_name', '')}" for key in all_target_keys]

    # Select mappings
    target_column_display = st.selectbox("Target Column*", target_display_options)
    target_column = target_column_display.split(" | ")[0]
    source_column = st.selectbox("Source Column", available_source_columns)
    default_value = st.text_input("Default Value")
    picklist_options = get_picklist_columns()
    picklist_file = st.selectbox("Picklist File", [""] + picklist_options)

    # Show system and display names
    st.text_input("System Column Name", value=target_column, disabled=True)
    st.text_input("Display Name", value=template[target_column].get("display_name", ""), disabled=True)
    # Save logic
    if st.button("➕ Save Mapping"):
        if target_column not in template:
            template[target_column] = {}

        # Initialize nested dict if not present
        if applies_to not in template[target_column]:
            template[target_column][applies_to] = {}

        # Save values
        template[target_column]["display_name"] = template[target_column].get("display_name", "")
        template[target_column][applies_to]["source_file"] = source_file
        template[target_column][applies_to]["source_column"] = source_column
        template[target_column][applies_to]["default_value"] = default_value
        template[target_column][applies_to]["picklist_file"] = picklist_file

        save_config(source_file.lower(), template)
        st.success("✅ Mapping saved successfully.")
    # Download logic
    st.markdown("---")
    st.subheader("📥 Download Current Mappings (CSV)")

    def flatten_template(template_dict):
        rows = []
        for target, props in template_dict.items():
            display = props.get("display_name", "")
            for scope, cfg in props.items():
                if scope == "display_name":
                    continue
                row = {
                    "Target Column": target,
                    "Display Name": display,
                    "Applies To": scope,
                    "Source File": cfg.get("source_file", ""),
                    "Source Column": cfg.get("source_column", ""),
                    "Default Value": cfg.get("default_value", ""),
                    "Picklist File": cfg.get("picklist_file", "")
                }
                rows.append(row)
        return pd.DataFrame(rows)

    flat_df = flatten_template(template)
    st.download_button("📄 Download as CSV", data=flat_df.to_csv(index=False), file_name="column_mappings.csv", mime="text/csv")
    st.markdown("---")
    st.subheader("📋 Current Mapping Overview")

    if flat_df.empty:
        st.info("No mappings available yet.")
    else:
        st.dataframe(flat_df, use_container_width=True)

