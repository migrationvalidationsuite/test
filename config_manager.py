import streamlit as st
import pandas as pd
import os
import json
from pathlib import Path
from typing import List, Dict, Optional, Union

CONFIG_DIR = "configs"
PICKLIST_DIR = "picklists"
SOURCE_SAMPLES_DIR = "source_samples"
MAX_SAMPLE_ROWS = 1000

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

DEFAULT_TEMPLATES = {
    # Foundation
    "level": [
        {"target_column1": "externalCode", "target_column2": "Code"},
        {"target_column1": "name.en_US", "target_column2": "Name"},
        {"target_column1": "startDate", "target_column2": "Start Date"}
    ],
    "association": [
        {"target_column1": "sourceCode", "target_column2": "Source"},
        {"target_column1": "targetCode", "target_column2": "Target"}
    ],
    # Payroll
    "pa0008": [
        {"target_column1": "employee_id", "target_column2": "Employee ID"},
        {"target_column1": "start_date", "target_column2": "Start Date"},
        {"target_column1": "end_date", "target_column2": "End Date"},
        {"target_column1": "amount", "target_column2": "Amount"}
    ],
    "pa0014": [
        {"target_column1": "employee_id", "target_column2": "Employee ID"},
        {"target_column1": "wage_type", "target_column2": "Wage Type"},
        {"target_column1": "amount", "target_column2": "Amount"},
        {"target_column1": "currency", "target_column2": "Currency"}
    ]
]
def initialize_directories() -> None:
    for directory in [CONFIG_DIR, PICKLIST_DIR, SOURCE_SAMPLES_DIR]:
        Path(directory).mkdir(exist_ok=True)

def save_config(config_type: str, config_data: Union[Dict, List]) -> None:
    temp_path = f"{CONFIG_DIR}/{config_type}_config.tmp"
    final_path = f"{CONFIG_DIR}/{config_type}_config.json"
    try:
        with open(temp_path, "w") as f:
            json.dump(config_data, f, indent=2)
        if os.path.exists(final_path):
            os.remove(final_path)
        os.rename(temp_path, final_path)
    except Exception as e:
        st.error(f"Error saving config: {str(e)}")

def load_config(config_type: str) -> Optional[Union[Dict, List]]:
    config_path = f"{CONFIG_DIR}/{config_type}_config.json"
    try:
        if not os.path.exists(config_path):
            return None
        with open(config_path, "r") as f:
            return json.load(f)
    except Exception as e:
        st.error(f"Error loading config: {str(e)}")
        return None

def get_source_columns(source_file: str) -> List[str]:
    try:
        path = os.path.join(SOURCE_SAMPLES_DIR, f"{source_file}_sample.csv")
        if os.path.exists(path):
            return pd.read_csv(path, nrows=1).columns.tolist()
    except Exception as e:
        st.error(f"Error reading columns: {e}")
    return []

def get_picklist_columns(picklist_file: str) -> List[str]:
    try:
        return pd.read_csv(f"{PICKLIST_DIR}/{picklist_file}", nrows=1).columns.tolist()
    except Exception as e:
        st.error(f"Error reading picklist: {e}")
        return []
def render_column_mapping_interface():
    st.subheader("🧩 Column Mapping Configuration")

    # Determine dynamic options
    template_keys = list(DEFAULT_TEMPLATES.keys())
    if "pa0008" in template_keys or "pa0014" in template_keys:
        applies_to_options = ["PA0008", "PA0014"]
        source_file_options = ["PA0008", "PA0014"]
    else:
        applies_to_options = ["Level", "Association"]
        source_file_options = ["HRP1000", "HRP1001"]

    applies_to = st.selectbox("Applies To*", applies_to_options)
    source_file = st.selectbox("Source File*", source_file_options)
    source_columns = get_source_columns(source_file)

    if not source_columns:
        st.warning(f"No uploaded sample file found for {source_file}. Please upload one under 'Source File Samples'.")
        return

    template_type = applies_to.lower()
    template = load_config(template_type) or DEFAULT_TEMPLATES.get(template_type, [])
    target_options = [f"{row['target_column1']} | {row['target_column2']}" for row in template]
    selected = st.selectbox("Target Column*", target_options)
    target_col1, target_col2 = selected.split(" | ")

    source_col = st.selectbox("Source Column", [""] + source_columns)
    default_val = st.text_input("Default Value")
    picklist_options = [""] + sorted([f for f in os.listdir(PICKLIST_DIR) if f.endswith('.csv')]) if os.path.exists(PICKLIST_DIR) else [""]
    picklist_file = st.selectbox("Picklist File", picklist_options)
    trans_type = st.selectbox("Transformation Type", list(TRANSFORMATION_LIBRARY.keys()))

    second_col = ""
    picklist_col = ""
    custom_code = ""

    if trans_type == "Concatenate":
        second_col = st.selectbox("Second Column", [""] + source_columns)
    elif trans_type == "Lookup Value" and picklist_file:
        picklist_col = st.selectbox("Picklist Column", get_picklist_columns(picklist_file))
    elif trans_type == "Custom Python":
        custom_code = st.text_area("Python Expression", value="value")

    if st.button("➕ Save Mapping"):
        mapping = {
            "target_column1": target_col1,
            "target_column2": target_col2,
            "applies_to": applies_to,
            "source_file": source_file,
            "source_column": source_col,
            "default_value": default_val,
            "picklist_file": picklist_file,
            "picklist_column": picklist_col if trans_type == "Lookup Value" else "",
            "transformation": trans_type,
            "secondary_column": second_col if trans_type == "Concatenate" else "",
            "transformation_code": custom_code if trans_type == "Custom Python" else TRANSFORMATION_LIBRARY.get(trans_type, "")
        }

        all_mappings = load_config("column_mappings") or []
        all_mappings.append(mapping)
        save_config("column_mappings", all_mappings)
        st.success("✅ Mapping saved successfully.")
        st.rerun()

    st.markdown("---")
    st.subheader("📋 Existing Mappings")
    current = load_config("column_mappings") or []
    if not current:
        st.info("No mappings configured yet.")
    else:
        df = pd.DataFrame(current)
        st.dataframe(df, use_container_width=True)
        st.download_button("📄 Download Mappings as CSV", data=df.to_csv(index=False), file_name="column_mappings.csv", mime="text/csv")
def render_template_editor(template_type: str):
    """Render the destination template editor (Level, Association, PA0008, etc.)"""
    st.subheader(f"{template_type} Template Configuration")

    current_template = load_config(template_type.lower()) or DEFAULT_TEMPLATES[template_type.lower()]

    if f"{template_type}_template" not in st.session_state:
        st.session_state[f"{template_type}_template"] = current_template.copy()

    edit_mode = st.radio("Edit Mode", ["Table Editor", "Text Input"], horizontal=True)

    if st.button("Reset to Default"):
        st.session_state[f"{template_type}_template"] = DEFAULT_TEMPLATES[template_type.lower()].copy()
        save_config(template_type.lower(), st.session_state[f"{template_type}_template"])
        st.success("Reset to default template!")
        st.rerun()

    if edit_mode == "Table Editor":
        for i, row in enumerate(st.session_state[f"{template_type}_template"]):
            cols = st.columns([4, 4, 2])
            with cols[0]:
                row['target_column1'] = st.text_input("System Name", value=row['target_column1'], key=f"{template_type}_tc1_{i}")
            with cols[1]:
                row['target_column2'] = st.text_input("Display Name", value=row['target_column2'], key=f"{template_type}_tc2_{i}")
            with cols[2]:
                row['description'] = st.text_input("Description", value=row.get('description', ''), key=f"{template_type}_desc_{i}")

        if st.button("Save Template"):
            save_config(template_type.lower(), st.session_state[f"{template_type}_template"])
            st.success("Template saved!")
    else:
        raw_text = convert_template_to_text(st.session_state[f"{template_type}_template"])
        updated_text = st.text_area("Template as CSV Text (System,Display,Description)", value=raw_text, height=300)
        if st.button("Apply Text Changes"):
            try:
                parsed = convert_text_to_template(updated_text)
                st.session_state[f"{template_type}_template"] = parsed
                st.success("Text updated.")
                st.rerun()
            except Exception as e:
                st.error(f"Invalid format: {str(e)}")

def manage_picklists():
    st.subheader("Picklist Management")

    new_files = st.file_uploader("Upload Picklist CSVs", type=["csv"], accept_multiple_files=True)
    if new_files:
        for file in new_files:
            try:
                df = pd.read_csv(file)
                df.to_csv(f"{PICKLIST_DIR}/{file.name}", index=False)
                st.success(f"Uploaded: {file.name}")
            except Exception as e:
                st.error(f"Error with {file.name}: {e}")

    with st.expander("➕ Create Manual Picklist"):
        pl_name = st.text_input("Picklist Name", value="example.csv")
        pl_data = st.text_area("Enter CSV Data", value="code,label\nA,Active\nI,Inactive")
        if st.button("Save Picklist") and pl_name.endswith(".csv"):
            try:
                pd.read_csv(io.StringIO(pl_data)).to_csv(f"{PICKLIST_DIR}/{pl_name}", index=False)
                st.success("Manual picklist saved.")
            except Exception as e:
                st.error(f"Error: {e}")

    st.subheader("📂 Existing Picklists")
    if os.path.exists(PICKLIST_DIR):
        files = [f for f in os.listdir(PICKLIST_DIR) if f.endswith(".csv")]
        for file in files:
            with st.expander(file):
                try:
                    df = pd.read_csv(f"{PICKLIST_DIR}/{file}")
                    st.dataframe(df)
                except:
                    st.warning(f"⚠ Could not read {file}")
                if st.button(f"🗑️ Delete {file}", key=file):
                    os.remove(f"{PICKLIST_DIR}/{file}")
                    st.success(f"{file} deleted")
                    st.rerun()
def show_admin_panel():
    """Main admin panel interface with tabs (foundation + payroll)"""
    st.title("🛠️ Configuration Manager")
    initialize_directories()

    tab1, tab2, tab3, tab4 = st.tabs([
        "📂 Source File Samples",
        "📄 Destination Templates",
        "🗃️ Picklist Management",
        "🔄 Column Mapping"
    ])

    with tab1:
        st.subheader("Upload Source File Samples")
        st.info("Upload CSV/Excel samples for HRP1000, HRP1001, PA0008, or PA0014")

        source_type = st.radio("Select Source File Type", ["HRP1000", "HRP1001", "PA0008", "PA0014"], horizontal=True)
        uploaded_file = st.file_uploader(f"Upload {source_type} Sample", type=["csv", "xlsx"], key=f"{source_type}_upload")

        if uploaded_file:
            process_uploaded_file(uploaded_file, source_type)

        sample_path = os.path.join(SOURCE_SAMPLES_DIR, f"{source_type}_sample.csv")
        if os.path.exists(sample_path):
            try:
                df = pd.read_csv(sample_path, nrows=1)
                st.success(f"✅ {source_type} sample has {len(df.columns)} columns")
                st.write("Columns:", df.columns.tolist())
            except Exception as e:
                st.error(f"Could not read sample: {e}")
        else:
            st.info("No sample uploaded yet.")

    with tab2:
        template_mode = st.radio("Select Template Type", ["Level", "Association", "PA0008", "PA0014"], horizontal=True)
        render_template_editor(template_mode)

    with tab3:
        manage_picklists()

    with tab4:
        # Auto-detect mode
        available_keys = list(DEFAULT_TEMPLATES.keys())
        if "pa0008" in available_keys or "pa0014" in available_keys:
            render_column_mapping_interface(mode="payroll")
        else:
            render_column_mapping_interface(mode="foundation")
