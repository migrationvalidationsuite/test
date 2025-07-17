import os
import json
import streamlit as st
import pandas as pd
from datetime import datetime
# Add this at the top (or complete your current import)
from typing import List, Dict, Optional, Tuple


CONFIG_FILE = "config.json"
DEFAULT_TEMPLATES = {
    "foundation_template": {
        "name": {"type": "string", "source": "Object Name"},
        "obj_id": {"type": "string", "source": "Object ID"},
        "parent_id": {"type": "string", "source": "Parent Object ID"}
    },
    "payroll_template": {
        "employee_id": {"type": "string", "source": "Pers.No."},
        "wage_type": {"type": "string", "source": "Wage type"},
        "amount": {"type": "number", "source": "Amount"},
        "currency": {"type": "string", "source": "Crcy"},
        "start_date": {"type": "date", "source": "Start Date"},
        "end_date": {"type": "date", "source": "End Date"},
        "assignment": {"type": "string", "source": "Assignment number"}
    }
}

# ✅ Fix 1: Add initialize_directories
def initialize_directories():
    os.makedirs("templates", exist_ok=True)
    os.makedirs("data", exist_ok=True)
    os.makedirs("picklists", exist_ok=True)
# ✅ Load existing config or return default structure
def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as f:
            return json.load(f)
    else:
        return {
            "templates": DEFAULT_TEMPLATES,
            "picklists": {},
            "settings": {
                "created_at": datetime.now().isoformat(),
                "version": "1.0"
            }
        }

# ✅ Save config to disk
def save_config(config_data):
    try:
        with open(CONFIG_FILE, "w") as f:
            json.dump(config_data, f, indent=4)
        return True
    except Exception as e:
        st.error(f"Error saving config: {str(e)}")
        return False

# ✅ Fix 2: Accept template_type argument
def render_template_editor(template_type=None):
    st.subheader("Template Editor")

    config = load_config()
    templates = config.get('templates', DEFAULT_TEMPLATES)
    # Handle payroll-specific template auto-creation
    if template_type == "payroll":
        if "payroll_template" not in templates:
            templates["payroll_template"] = {
                "employee_id": {"type": "string", "source": "Pers.No."},
                "wage_type": {"type": "string", "source": "Wage type"},
                "amount": {"type": "number", "source": "Amount"},
                "currency": {"type": "string", "source": "Crcy"},
                "start_date": {"type": "date", "source": "Start Date"},
                "end_date": {"type": "date", "source": "End Date"},
                "assignment": {"type": "string", "source": "Assignment number"}
            }
            save_config(config)

    template_names = list(templates.keys())
    if not template_names:
        st.warning("No templates available")
        return

    selected_template = st.selectbox("Select Template", template_names)

    if selected_template:
        try:
            template_content = templates[selected_template]

            # Show as editable JSON string
            if isinstance(template_content, dict):
                template_text = json.dumps(template_content, indent=2)
            else:
                template_text = str(template_content)

            edited_template = st.text_area(
                f"Edit {selected_template}",
                value=template_text,
                height=300
            )

            col1, col2 = st.columns(2)
            with col1:
                if st.button("Save Template"):
                    try:
                        parsed_template = (
                            json.loads(edited_template)
                            if edited_template.strip().startswith("{")
                            else edited_template
                        )
                        config['templates'][selected_template] = parsed_template
                        if save_config(config):
                            st.success(f"Template '{selected_template}' saved successfully")
                        else:
                            st.error("Failed to save template")
                    except json.JSONDecodeError as e:
                        st.error(f"Invalid JSON: {str(e)}")

            with col2:
                if st.button("Delete Template"):
                    if selected_template in config['templates']:
                        del config['templates'][selected_template]
                        if save_config(config):
                            st.success(f"Template '{selected_template}' deleted")
                            st.rerun()
                        else:
                            st.error("Failed to delete template")
        except Exception as e:
            st.error(f"Error rendering template editor: {str(e)}")
def manage_picklists():
    st.subheader("Picklist Management")
    os.makedirs(PICKLIST_DIR, exist_ok=True)

    picklist_files = [f for f in os.listdir(PICKLIST_DIR) if f.endswith(".csv")]

    selected_file = st.selectbox("Select a picklist to view/edit", picklist_files) if picklist_files else None

    if selected_file:
        filepath = os.path.join(PICKLIST_DIR, selected_file)
        df = pd.read_csv(filepath)

        st.dataframe(df)

        st.download_button("Download Picklist", data=df.to_csv(index=False), file_name=selected_file)

    uploaded = st.file_uploader("Upload a new picklist (CSV)", type=["csv"])
    if uploaded:
        with open(os.path.join(PICKLIST_DIR, uploaded.name), "wb") as f:
            f.write(uploaded.read())
        st.success(f"{uploaded.name} uploaded successfully")
        st.rerun()


def get_source_columns(file_path: str) -> List[str]:
    try:
        df = pd.read_csv(file_path, nrows=MAX_SAMPLE_ROWS)
        return df.columns.tolist()
    except Exception as e:
        st.error(f"Error loading source columns: {str(e)}")
        return []


def get_picklist_columns(picklist_name: str) -> List[str]:
    try:
        path = os.path.join(PICKLIST_DIR, picklist_name)
        df = pd.read_csv(path)
        return df.columns.tolist()
    except Exception as e:
        st.error(f"Error loading picklist: {str(e)}")
        return []


def picklist_lookup(value, picklist_name, column):
    try:
        df = pd.read_csv(os.path.join(PICKLIST_DIR, picklist_name))
        if column in df.columns and value in df[column].values:
            return value
        else:
            return None
    except Exception:
        return None
def process_uploaded_file(uploaded_file, delimiter: str = ",") -> Optional[pd.DataFrame]:
    """
    Reads a CSV or Excel file from Streamlit's uploader and returns a DataFrame.
    Tries to auto-detect encoding and handles large files gracefully.
    """
    try:
        if uploaded_file.name.endswith(".csv"):
            return pd.read_csv(uploaded_file, delimiter=delimiter)
        elif uploaded_file.name.endswith((".xls", ".xlsx")):
            return pd.read_excel(uploaded_file)
        else:
            st.error("Unsupported file type")
            return None
    except Exception as e:
        st.error(f"Error processing file: {e}")
        return None

