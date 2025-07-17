import streamlit as st
import pandas as pd
import json
import os
import io
from datetime import datetime

# Add these missing functions to your config_manager.py file:

def process_uploaded_file(uploaded_file, file_type="excel"):
    """
    Process an uploaded file and return a DataFrame
    """
    try:
        if file_type == "excel" or uploaded_file.name.endswith(('.xlsx', '.xls')):
            df = pd.read_excel(uploaded_file)
        elif file_type == "csv" or uploaded_file.name.endswith('.csv'):
            df = pd.read_csv(uploaded_file)
        else:
            st.error(f"Unsupported file type: {uploaded_file.name}")
            return None
        
        return df
    except Exception as e:
        st.error(f"Error processing file: {str(e)}")
        return None

def convert_template_to_text(template_dict):
    """
    Convert template dictionary to text format
    """
    if isinstance(template_dict, dict):
        return json.dumps(template_dict, indent=2)
    return str(template_dict)

def get_source_columns(df):
    """
    Get list of source columns from DataFrame
    """
    if df is not None:
        return df.columns.tolist()
    return []

def get_picklist_columns(config):
    """
    Get columns that have picklists defined
    """
    picklists = config.get('picklists', {})
    return list(picklists.keys())

def render_column_mapping_interface(uploaded_file, mode="default"):
    """
    Render the column mapping interface
    """
    st.subheader("Column Mapping")
    
    if uploaded_file is None:
        st.warning("Please upload a file first")
        return None
    
    # Process the uploaded file
    df = process_uploaded_file(uploaded_file)
    if df is None:
        return None
    
    st.write("File preview:")
    st.dataframe(df.head())
    
    # Get source columns
    source_columns = get_source_columns(df)
    
    # Create mapping interface
    mapping = {}
    
    # Common target columns (customize based on your needs)
    target_columns = [
        "employee_id", "employee_name", "department", "position", 
        "base_salary", "overtime_hours", "overtime_rate", "deductions",
        "gross_pay", "net_pay", "tax_withheld"
    ]
    
    if mode == "payroll":
        st.write("Map your file columns to payroll fields:")
        for target_col in target_columns:
            mapping[target_col] = st.selectbox(
                f"Map '{target_col}' to:",
                options=[""] + source_columns,
                key=f"mapping_{target_col}"
            )
    else:
        st.write("Column mapping:")
        for i, source_col in enumerate(source_columns):
            mapping[source_col] = st.text_input(
                f"Map '{source_col}' to:",
                value=source_col,
                key=f"mapping_{i}"
            )
    
    return mapping

def show_admin_panel():
    """
    Show the admin panel for configuration management
    """
    st.header("Admin Panel")
    
    # Initialize directories
    initialize_directories()
    
    # Load current configuration
    config = load_config()
    
    # Create tabs for different admin functions
    tab1, tab2, tab3, tab4 = st.tabs(["Templates", "Picklists", "Configuration", "System Info"])
    
    with tab1:
        st.subheader("Template Management")
        render_template_editor()
    
    with tab2:
        st.subheader("Picklist Management")
        manage_picklists()
    
    with tab3:
        st.subheader("Configuration")
        
        # Display current config
        st.write("Current Configuration:")
        st.json(config)
        
        # Option to reset to defaults
        if st.button("Reset to Default Configuration"):
            default_config = {
                "templates": DEFAULT_TEMPLATES,
                "picklists": {},
                "settings": {
                    "created_at": datetime.now().isoformat(),
                    "version": "1.0"
                }
            }
            save_config(default_config)
            st.success("Configuration reset to defaults")
            st.rerun()
    
    with tab4:
        st.subheader("System Information")
        st.write("System Status:")
        st.write(f"- Configuration file exists: {os.path.exists('config.json')}")
        st.write(f"- Templates directory exists: {os.path.exists('templates')}")
        st.write(f"- Data directory exists: {os.path.exists('data')}")
        
        # Show directory contents
        if os.path.exists('templates'):
            st.write("Template files:")
            for file in os.listdir('templates'):
                st.write(f"  - {file}")

def initialize_directories():
    """
    Create necessary directories if they don't exist
    """
    directories = ['templates', 'data', 'config']
    for directory in directories:
        if not os.path.exists(directory):
            os.makedirs(directory)
            st.info(f"Created directory: {directory}")

def render_template_editor():
    """
    Render the template editor interface
    """
    st.subheader("Template Editor")
    
    config = load_config()
    templates = config.get('templates', DEFAULT_TEMPLATES)
    
    # Template selection
    template_names = list(templates.keys())
    selected_template = st.selectbox("Select Template", template_names)
    
    if selected_template:
        # Edit template
        template_content = templates[selected_template]
        
        # Convert to text for editing
        template_text = convert_template_to_text(template_content)
        
        edited_template = st.text_area(
            f"Edit {selected_template}",
            value=template_text,
            height=300
        )
        
        if st.button("Save Template"):
            try:
                # Try to parse as JSON if it looks like JSON
                if edited_template.strip().startswith('{'):
                    parsed_template = json.loads(edited_template)
                else:
                    parsed_template = edited_template
                
                # Update config
                config['templates'][selected_template] = parsed_template
                save_config(config)
                st.success(f"Template '{selected_template}' saved successfully")
            except json.JSONDecodeError as e:
                st.error(f"Invalid JSON format: {str(e)}")

def manage_picklists():
    """
    Manage picklists for dropdowns and validation
    """
    st.subheader("Picklist Management")
    
    config = load_config()
    picklists = config.get('picklists', {})
    
    # Create new picklist
    st.write("Create New Picklist:")
    new_picklist_name = st.text_input("Picklist Name")
    new_picklist_values = st.text_area("Values (one per line)")
    
    if st.button("Create Picklist") and new_picklist_name:
        values = [v.strip() for v in new_picklist_values.split('\n') if v.strip()]
        picklists[new_picklist_name] = values
        config['picklists'] = picklists
        save_config(config)
        st.success(f"Picklist '{new_picklist_name}' created")
        st.rerun()
    
    # Edit existing picklists
    if picklists:
        st.write("Edit Existing Picklists:")
        for name, values in picklists.items():
            with st.expander(f"Edit {name}"):
                edited_values = st.text_area(
                    f"Values for {name}",
                    value='\n'.join(values),
                    key=f"picklist_{name}"
                )
                
                col1, col2 = st.columns(2)
                with col1:
                    if st.button(f"Save {name}", key=f"save_{name}"):
                        new_values = [v.strip() for v in edited_values.split('\n') if v.strip()]
                        picklists[name] = new_values
                        config['picklists'] = picklists
                        save_config(config)
                        st.success(f"Picklist '{name}' updated")
                        st.rerun()
                
                with col2:
                    if st.button(f"Delete {name}", key=f"delete_{name}"):
                        del picklists[name]
                        config['picklists'] = picklists
                        save_config(config)
                        st.success(f"Picklist '{name}' deleted")
                        st.rerun()

# Make sure you also have these essential functions in your config_manager.py:

def load_config():
    """Load configuration from file"""
    config_file = "config.json"
    if os.path.exists(config_file):
        try:
            with open(config_file, 'r') as f:
                return json.load(f)
        except:
            pass
    
    # Return default config if file doesn't exist or is corrupted
    return {
        "templates": DEFAULT_TEMPLATES,
        "picklists": {},
        "settings": {
            "created_at": datetime.now().isoformat(),
            "version": "1.0"
        }
    }

def save_config(config):
    """Save configuration to file"""
    config_file = "config.json"
    try:
        with open(config_file, 'w') as f:
            json.dump(config, f, indent=2)
        return True
    except Exception as e:
        st.error(f"Error saving configuration: {str(e)}")
        return False

# Default templates (customize based on your needs)
DEFAULT_TEMPLATES = {
    "payroll_template": {
        "employee_id": "string",
        "employee_name": "string",
        "department": "string",
        "base_salary": "number",
        "overtime_hours": "number",
        "gross_pay": "number",
        "net_pay": "number"
    },
    "employee_template": {
        "employee_id": "string",
        "name": "string",
        "email": "string",
        "department": "string",
        "hire_date": "date"
    }
}
__all__ = [
    "initialize_directories",
    "render_template_editor",
    "manage_picklists",
    "render_column_mapping_interface",
    "get_source_columns",
    "get_picklist_columns",
    "load_config",
    "DEFAULT_TEMPLATES",
    "save_config",
    "show_admin_panel",
    "process_uploaded_file"
]
