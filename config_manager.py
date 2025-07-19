import streamlit as st
import pandas as pd
import os
import json
from typing import List, Dict, Optional, Union
from pathlib import Path

# Base directory by mode
BASE_DIR = {
    "foundation": "foundation_configs",
    "payroll": "payroll_configs"
}

# Setup constants
MAX_SAMPLE_ROWS = 1000

# Paths per mode
def get_paths(mode: str) -> Optional[Dict[str, str]]:
    if mode not in BASE_DIR:
        st.error(f"❌ Invalid mode: {mode}. Must be one of: {list(BASE_DIR.keys())}")
        return None
    base = BASE_DIR[mode]
    return {
        "CONFIG_DIR": os.path.join(base, "configs"),
        "PICKLIST_DIR": os.path.join(base, "picklists"),
        "SAMPLES_DIR": os.path.join(base, "source_samples")
    }

# Initialize folders
def initialize_directories(mode: str) -> None:
    paths = get_paths(mode)
    for path in paths.values():
        Path(path).mkdir(parents=True, exist_ok=True)

# ✅ Fixed Picklist Management
def manage_picklists(mode: str):
    st.subheader("📌 Picklist Management")

    paths = get_paths(mode)
    picklist_dir = paths["PICKLIST_DIR"]
    os.makedirs(picklist_dir, exist_ok=True)

    picklist_files = [f for f in os.listdir(picklist_dir) if f.endswith(".csv")]

    selected_file = st.selectbox("Select a picklist to view/edit", picklist_files) if picklist_files else None

    if selected_file:
        file_path = os.path.join(picklist_dir, selected_file)
        try:
            df = pd.read_csv(file_path)
            edited_df = st.data_editor(df, use_container_width=True, num_rows="dynamic")

            if st.button("💾 Save Picklist", key=f"save_picklist_{mode}_{selected_file}"):
                edited_df.to_csv(file_path, index=False)
                st.success(f"✅ Picklist '{selected_file}' saved successfully.")
        except Exception as e:
            st.error(f"Error reading '{selected_file}': {e}")
    else:
        st.info("No picklists found. Upload or create one manually.")
# 🔧 Default Destination Templates (for Foundation & Payroll)
DEFAULT_TEMPLATES = {
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
    "PA0008": [
        {"target_column1": "Currency", "target_column2": "Crcy", "description": ""},
        {"target_column1": "Start Date", "target_column2": "Start Date", "description": ""},
        {"target_column1": "Frequency", "target_column2": "Frequency", "description": "Default: Hourly"},
        {"target_column1": "Pay Component", "target_column2": "Wage type", "description": ""},
        {"target_column1": "Sequence Number", "target_column2": "Sequence Number", "description": ""},
        {"target_column1": "User ID", "target_column2": "Pers.No.", "description": ""},
        {"target_column1": "Amount", "target_column2": "Amount", "description": ""},
        {"target_column1": "End Date", "target_column2": "End Date", "description": ""},
        {"target_column1": "Notes", "target_column2": "Notes", "description": ""},
        {"target_column1": "Number of Units", "target_column2": "Number/unit", "description": ""},
        {"target_column1": "Unit of Measure", "target_column2": "Unit of Measure", "description": "Default: AUD"},
        {"target_column1": "Operation", "target_column2": "Operation", "description": ""}
    ],
    "PA0014": [
        {"target_column1": "Currency", "target_column2": "Crcy", "description": ""},
        {"target_column1": "Start Date", "target_column2": "Start Date", "description": ""},
        {"target_column1": "Frequency", "target_column2": "Frequency", "description": "Default: BWK"},
        {"target_column1": "Pay Component", "target_column2": "Wage type", "description": ""},
        {"target_column1": "Sequence Number", "target_column2": "Sequence Number", "description": ""},
        {"target_column1": "User ID", "target_column2": "Pers.No.", "description": ""},
        {"target_column1": "Amount", "target_column2": "Amount", "description": ""},
        {"target_column1": "End Date", "target_column2": "End Date", "description": ""},
        {"target_column1": "Notes", "target_column2": "Notes", "description": ""},
        {"target_column1": "Number of Units", "target_column2": "Number/unit", "description": ""},
        {"target_column1": "Unit of Measure", "target_column2": "Unit of Measure", "description": "Default: AUD"},
        {"target_column1": "Operation", "target_column2": "Operation", "description": ""}
    ]
}

def convert_text_to_template(text_input: str) -> List[Dict]:
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
    return '\n'.join([
        f"{item['target_column1']},{item['target_column2']},{item.get('description', '')}"
        for item in template
    ])

def render_template_editor(template_type: str, mode: str) -> None:
    st.subheader(f"{template_type} Template Configuration")

    paths = get_paths(mode)
    config_path = paths["CONFIG_DIR"]
    config_file = os.path.join(config_path, f"{template_type.lower()}_config.json")

    # Load or initialize
    default_template = DEFAULT_TEMPLATES.get(template_type.lower(), [])
    if os.path.exists(config_file):
        try:
            with open(config_file, "r") as f:
                current_template = json.load(f)
        except:
            current_template = default_template
    else:
        current_template = default_template

    if f"{template_type}_template_{mode}" not in st.session_state:
        st.session_state[f"{template_type}_template_{mode}"] = current_template.copy()

    edit_mode = st.radio("Edit Mode:", ["Table Editor", "Text Input"], horizontal=True, key=f"{template_type}_edit_mode_{mode}")

    if st.button("Reset to Default Templates", key=f"reset_default_{template_type}_{mode}"):
        st.session_state[f"{template_type}_template_{mode}"] = default_template.copy()
        with open(config_file, "w") as f:
            json.dump(st.session_state[f"{template_type}_template_{mode}"], f, indent=2)
        st.success(f"✅ {template_type} template reset to default.")
        st.rerun()

    if edit_mode == "Table Editor":
        for i, row in enumerate(st.session_state[f"{template_type}_template_{mode}"]):
            cols = st.columns([3, 3, 3, 1])
            row['target_column1'] = cols[0].text_input("System Column", row['target_column1'], key=f"{template_type}_col1_{i}_{mode}", label_visibility="collapsed")
            row['target_column2'] = cols[1].text_input("Display Name", row['target_column2'], key=f"{template_type}_col2_{i}_{mode}", label_visibility="collapsed")
            row['description'] = cols[2].text_input("Description", row.get('description', ''), key=f"{template_type}_desc_{i}_{mode}", label_visibility="collapsed")
            if cols[3].button("🗑️", key=f"{template_type}_del_{i}_{mode}"):
                del st.session_state[f"{template_type}_template_{mode}"][i]
                st.rerun()

        if st.button("Save Template", key=f"save_template_{template_type}_{mode}"):
            with open(config_file, "w") as f:
                json.dump(st.session_state[f"{template_type}_template_{mode}"], f, indent=2)
            st.success("Template saved successfully.")

    else:
        text_input = st.text_area(
            "Template (CSV format: col1,col2,desc)",
            value=convert_template_to_text(st.session_state[f"{template_type}_template_{mode}"]),
            height=250
        )
        if st.button("Apply Text Changes", key=f"apply_txt_{template_type}_{mode}"):
            try:
                parsed = convert_text_to_template(text_input)
                st.session_state[f"{template_type}_template_{mode}"] = parsed
                st.success("Template updated.")
                st.rerun()
            except Exception as e:
                st.error(f"Error: {e}")
# 🔁 Transformation options
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

def render_column_mapping_interface(mode: str):
    st.subheader(f"Column Mapping – {'Payroll' if mode == 'payroll' else 'Foundation'} Mode")
    st.info("Define how your source columns map to destination columns using transformations.")

    paths = get_paths(mode)
    if not paths:
        st.error("❌ Failed to resolve paths.")
        return

    file_options = ["PA0008", "PA0014"] if mode == "payroll" else ["HRP1000", "HRP1001"]
    source_file = st.selectbox("Select source file type", file_options, key=f"column_map_src_{mode}")
    sample_path = os.path.join(paths["SAMPLES_DIR"], f"{source_file}_sample.csv")
    config_path = os.path.join(paths["CONFIG_DIR"], f"{source_file}_column_mapping.json")

    # Load sample file
    if not os.path.exists(sample_path):
        st.warning(f"⚠️ No sample uploaded for {source_file}. Please upload one first.")
        return

    try:
        sample_df = pd.read_csv(sample_path)
        columns = sample_df.columns.tolist()
    except Exception as e:
        st.error(f"Error reading sample: {e}")
        return

    # Load existing mappings
    if f"mappings_{source_file}_{mode}" not in st.session_state:
        if os.path.exists(config_path):
            try:
                with open(config_path, "r") as f:
                    st.session_state[f"mappings_{source_file}_{mode}"] = json.load(f)
            except:
                st.session_state[f"mappings_{source_file}_{mode}"] = []
        else:
            st.session_state[f"mappings_{source_file}_{mode}"] = []

    st.markdown("### 🔁 Define Mappings")
    mappings = st.session_state[f"mappings_{source_file}_{mode}"]

    for i, mapping in enumerate(mappings):
        cols = st.columns([3, 3, 3, 1])
        mapping["source_column"] = cols[0].selectbox(
            "Source", columns,
            index=columns.index(mapping["source_column"]) if mapping["source_column"] in columns else 0,
            key=f"{mode}_src_{i}", label_visibility="collapsed"
        )
        mapping["destination_column"] = cols[1].text_input(
            "Destination", value=mapping["destination_column"],
            key=f"{mode}_dest_{i}", label_visibility="collapsed"
        )
        mapping["transformation"] = cols[2].selectbox(
            "Transformation", list(TRANSFORMATION_LIBRARY.keys()),
            index=list(TRANSFORMATION_LIBRARY.keys()).index(mapping["transformation"]) if mapping["transformation"] in TRANSFORMATION_LIBRARY else 0,
            key=f"{mode}_trans_{i}", label_visibility="collapsed"
        )
        if cols[3].button("🗑️", key=f"{mode}_del_map_{i}"):
            del mappings[i]
            st.rerun()

    if st.button("➕ Add New Mapping", key=f"add_map_btn_{mode}"):
        mappings.append({
            "source_column": columns[0] if columns else "",
            "destination_column": "",
            "transformation": "None"
        })

    if st.button("💾 Save Mappings", key=f"save_map_btn_{mode}"):
        try:
            os.makedirs(paths["CONFIG_DIR"], exist_ok=True)
            with open(config_path, "w") as f:
                json.dump(mappings, f, indent=2)
            st.success("✅ Mappings saved successfully!")
        except Exception as e:
            st.error(f"❌ Error saving: {e}")
def manage_picklists(mode: str):
    st.subheader("📚 Picklist Management")
    paths = get_paths(mode)
    if not paths:
        st.error("❌ Could not resolve picklist path.")
        return

    os.makedirs(paths["PICKLIST_DIR"], exist_ok=True)
    picklist_files = [f for f in os.listdir(paths["PICKLIST_DIR"]) if f.endswith(".csv") or f.endswith(".xlsx")]

    uploaded = st.file_uploader("Upload new picklist (.csv or .xlsx)", type=["csv", "xlsx"], key=f"picklist_upload_{mode}")
    if uploaded:
        save_path = os.path.join(paths["PICKLIST_DIR"], uploaded.name)
        with open(save_path, "wb") as f:
            f.write(uploaded.getbuffer())
        st.success(f"Uploaded to {save_path}")
        st.rerun()

    if not picklist_files:
        st.info("No picklists available. Upload one to get started.")
        return

    selected = st.selectbox("📄 Select a picklist to view/edit", picklist_files, key=f"select_picklist_{mode}")
    full_path = os.path.join(paths["PICKLIST_DIR"], selected)

    try:
        df = pd.read_excel(full_path) if selected.endswith(".xlsx") else pd.read_csv(full_path)
    except Exception as e:
        st.error(f"❌ Failed to load: {e}")
        return

    st.write(f"🔍 Preview: `{selected}`")
    st.dataframe(df, use_container_width=True)

    if st.button("💾 Save Changes", key=f"save_picklist_{mode}"):
        try:
            if selected.endswith(".xlsx"):
                df.to_excel(full_path, index=False)
            else:
                df.to_csv(full_path, index=False)
            st.success("✅ Picklist saved.")
        except Exception as e:
            st.error(f"❌ Save error: {e}")
def show_admin_panel(mode: str = "foundation") -> None:
    """Render the admin interface based on selected mode."""
    st.title(f"🛠️ Configuration Manager – {mode.capitalize()} Mode")
    initialize_directories(mode)

    tab1, tab2, tab3, tab4 = st.tabs([
        "📂 Source File Samples",
        "📄 Destination Templates",
        "🗃️ Picklist Management",
        "🔄 Column Mapping"
    ])

    with tab1:
        st.subheader("📁 Upload Sample Files")
        source_options = ["PA0008", "PA0014"] if mode == "payroll" else ["HRP1000", "HRP1001"]
        source_type = st.radio("Choose file type:", source_options, horizontal=True, key=f"src_type_{mode}")
        
        uploaded_file = st.file_uploader("Upload CSV or Excel", type=["csv", "xlsx"], key=f"{source_type}_{mode}_upload")
        if uploaded_file:
            process_uploaded_file(uploaded_file, source_type, mode)

        sample_path = get_sample_path(source_type, mode)
        if os.path.exists(sample_path):
            try:
                df = pd.read_csv(sample_path, nrows=1)
                st.success(f"✅ {source_type} Sample Loaded")
                is_valid, msg = validate_sample_columns(source_type, df)
                st.success("✔ Columns valid") if is_valid else st.error(f"Missing columns: {msg}")
            except Exception as e:
                st.error(f"⚠️ Failed to read sample: {e}")

    with tab2:
        if mode == "payroll":
            template_options = ["PA0008", "PA0014"]
        else:
            template_options = ["Level", "Association"]

        template_type = st.radio("Select Template Type", template_options, horizontal=True, key=f"template_type_{mode}")
        render_template_editor(template_type, mode)

    with tab3:
        manage_picklists(mode)

    with tab4:
        render_column_mapping_interface(mode)
