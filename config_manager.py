import streamlit as st
import pandas as pd
import os
import json
from typing import List, Dict, Optional
from pathlib import Path

# Directory bases
BASE_DIR = {
    "foundation": "foundation_configs",
    "payroll": "payroll_configs"
}

# ✅ Get key paths for each mode
def get_paths(mode: str) -> Optional[Dict[str, str]]:
    if mode not in BASE_DIR:
        st.error(f"❌ Invalid mode: {mode}")
        return None
    base = BASE_DIR[mode]
    return {
        "CONFIG_DIR": os.path.join(base, "configs"),
        "PICKLIST_DIR": os.path.join(base, "picklists"),
        "SAMPLES_DIR": os.path.join(base, "source_samples")
    }
def get_sample_path(file_type: str, sample_dir: str) -> str:
    return os.path.join(sample_dir, f"{file_type}_sample.csv")

# ✅ Setup directories if they don’t exist
def initialize_directories(mode: str):
    paths = get_paths(mode)
    for path in paths.values():
        Path(path).mkdir(parents=True, exist_ok=True)
# ✅ Save uploaded sample file
def process_uploaded_file(uploaded_file, source_file_type, mode):
    paths = get_paths(mode)
    if not paths:
        return
    if uploaded_file is not None:
        if uploaded_file.name.endswith(".csv"):
            df = pd.read_csv(uploaded_file)
        elif uploaded_file.name.endswith((".xls", ".xlsx")):
            df = pd.read_excel(uploaded_file)
        else:
            st.error("Unsupported file format.")
            return
        sample_path = os.path.join(paths["SAMPLES_DIR"], f"{source_file_type}_sample.csv")
        df.to_csv(sample_path, index=False)
        st.success(f"✅ {source_file_type} sample saved.")

# ✅ Validate sample file (at least 1 column)
def validate_sample_columns(file_type: str, df: pd.DataFrame) -> (bool, str):
    if df.empty or df.columns.size == 0:
        return False, "No columns found"
    return True, ""

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
# ✅ Template conversion helpers
def convert_text_to_template(text_input: str) -> List[Dict]:
    lines = [line.strip() for line in text_input.split('\n') if line.strip()]
    template = []
    for line in lines:
        parts = [part.strip() for part in line.split(',')]
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

# ✅ Picklist Management UI
def manage_picklists(mode: str):
    st.subheader("📚 Picklist Management")
    paths = get_paths(mode)
    picklist_dir = paths["PICKLIST_DIR"]
    os.makedirs(picklist_dir, exist_ok=True)

    uploaded = st.file_uploader("Upload Picklist (.csv)", type=["csv"], key=f"picklist_upload_{mode}")
    if uploaded:
        save_path = os.path.join(picklist_dir, uploaded.name)
        with open(save_path, "wb") as f:
            f.write(uploaded.getbuffer())
        st.success(f"Uploaded: {uploaded.name}")
        st.rerun()

    picklist_files = [f for f in os.listdir(picklist_dir) if f.endswith(".csv")]
    if picklist_files:
        selected = st.selectbox("Edit Picklist", picklist_files, key=f"picklist_select_{mode}")
        file_path = os.path.join(picklist_dir, selected)
        try:
            df = pd.read_csv(file_path)
            edited = st.data_editor(df, num_rows="dynamic", use_container_width=True)
            if st.button("💾 Save Picklist", key=f"save_picklist_btn_{mode}"):
                edited.to_csv(file_path, index=False)
                st.success(f"{selected} saved.")
        except Exception as e:
            st.error(f"Could not read file: {e}")
    else:
        st.info("No picklists found.")

def render_template_editor(template_type: str, mode: str) -> None:
    st.subheader(f"🧾 Destination Template – {template_type}")
    paths = get_paths(mode)
    config_path = os.path.join(paths["CONFIG_DIR"], f"{template_type}_destination_template.json")
    default_template = DEFAULT_TEMPLATES.get(template_type.lower(), [])

    # Load or fallback to default
    if os.path.exists(config_path):
        try:
            with open(config_path, "r") as f:
                template = json.load(f)
        except:
            template = default_template
    else:
        template = default_template

    if f"{template_type}_template_{mode}" not in st.session_state:
        st.session_state[f"{template_type}_template_{mode}"] = template.copy()

    edit_mode = st.radio("Edit Mode", ["Table", "Text"], horizontal=True, key=f"{template_type}_edit_mode_{mode}")

    if st.button("Reset to Default", key=f"reset_{template_type}_{mode}"):
        st.session_state[f"{template_type}_template_{mode}"] = default_template
        with open(config_path, "w") as f:
            json.dump(default_template, f, indent=2)
        st.success("Reset to default.")
        st.rerun()

    if edit_mode == "Table":
        for i, row in enumerate(st.session_state[f"{template_type}_template_{mode}"]):
            cols = st.columns([3, 3, 3, 1])
            row["target_column1"] = cols[0].text_input("System Column", row["target_column1"], key=f"col1_{i}_{mode}", label_visibility="collapsed")
            row["target_column2"] = cols[1].text_input("Display Name", row["target_column2"], key=f"col2_{i}_{mode}", label_visibility="collapsed")
            row["description"] = cols[2].text_input("Description", row.get("description", ""), key=f"desc_{i}_{mode}", label_visibility="collapsed")
            if cols[3].button("🗑️", key=f"del_{i}_{mode}"):
                del st.session_state[f"{template_type}_template_{mode}"][i]
                st.rerun()

        if st.button("💾 Save Template", key=f"save_temp_btn_{template_type}_{mode}"):
            with open(config_path, "w") as f:
                json.dump(st.session_state[f"{template_type}_template_{mode}"], f, indent=2)
            st.success("Template saved.")

    else:
        text = st.text_area("Template CSV format", convert_template_to_text(st.session_state[f"{template_type}_template_{mode}"]), height=250)
        if st.button("Apply Text", key=f"apply_txt_{template_type}_{mode}"):
            try:
                parsed = convert_text_to_template(text)
                st.session_state[f"{template_type}_template_{mode}"] = parsed
                st.success("Template updated.")
                st.rerun()
            except Exception as e:
                st.error(f"Parse error: {e}")
def render_column_mapping_interface(mode: str):
    st.subheader("🔄 Column Mapping Interface")

    paths = get_paths(mode)
    if not paths:
        st.error("❌ Invalid mode or config path.")
        return

    file_options = ["PA0008", "PA0014"] if mode == "payroll" else ["HRP1000", "HRP1001"]
    source_file = st.selectbox("📁 Choose Source File", file_options, key=f"src_map_{mode}")

    sample_path = os.path.join(paths["SAMPLES_DIR"], f"{source_file}.csv")
    config_path = os.path.join(paths["CONFIG_DIR"], f"{source_file}_column_mapping.json")

    if not os.path.exists(sample_path):
        st.warning(f"⚠️ No sample for {source_file}. Upload it first.")
        return

    try:
        df = pd.read_csv(sample_path, nrows=MAX_SAMPLE_ROWS)
        source_columns = df.columns.tolist()
    except Exception as e:
        st.error(f"Error reading sample: {e}")
        return

    # Load or init
    if f"mapping_{source_file}_{mode}" not in st.session_state:
        if os.path.exists(config_path):
            try:
                with open(config_path, "r") as f:
                    st.session_state[f"mapping_{source_file}_{mode}"] = json.load(f)
            except:
                st.session_state[f"mapping_{source_file}_{mode}"] = []
        else:
            st.session_state[f"mapping_{source_file}_{mode}"] = []

    mappings = st.session_state[f"mapping_{source_file}_{mode}"]

    for i, mapping in enumerate(mappings):
        cols = st.columns([3, 3, 3, 1])
        mapping["source_column"] = cols[0].selectbox("Source", source_columns, index=source_columns.index(mapping["source_column"]) if mapping["source_column"] in source_columns else 0, key=f"{mode}_src_{i}", label_visibility="collapsed")
        mapping["destination_column"] = cols[1].text_input("Destination", mapping["destination_column"], key=f"{mode}_dest_{i}", label_visibility="collapsed")
        mapping["transformation"] = cols[2].selectbox("Transform", list(TRANSFORMATION_LIBRARY.keys()), index=list(TRANSFORMATION_LIBRARY.keys()).index(mapping.get("transformation", "None")), key=f"{mode}_trans_{i}", label_visibility="collapsed")
        if cols[3].button("🗑️", key=f"{mode}_del_map_{i}"):
            del mappings[i]
            st.rerun()

    if st.button("➕ Add Mapping", key=f"add_map_{mode}"):
        mappings.append({
            "source_column": source_columns[0] if source_columns else "",
            "destination_column": "",
            "transformation": "None"
        })

    if st.button("💾 Save Mappings", key=f"save_map_{mode}"):
        try:
            with open(config_path, "w") as f:
                json.dump(mappings, f, indent=2)
            st.success("✅ Mappings saved!")
        except Exception as e:
            st.error(f"❌ Save error: {e}")
def show_admin_panel(mode: str = "foundation") -> None:
    """Render the Configuration Manager UI for the given mode."""
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
        selected_file_type = st.radio("Choose file type:", source_options, horizontal=True, key=f"src_type_{mode}")
    
        uploaded_file = st.file_uploader("Upload CSV or Excel", type=["csv", "xlsx"], key=f"{selected_file_type}_{mode}_upload")
        
        paths = get_paths(mode)
        if not paths:
            st.error("Invalid mode paths.")
        elif uploaded_file:
            df = pd.read_csv(uploaded_file) if uploaded_file.name.endswith(".csv") else pd.read_excel(uploaded_file)
            
            sample_path = os.path.join(paths["SAMPLES_DIR"], f"{selected_file_type}.csv")
            df.to_csv(sample_path, index=False)
            st.success(f"{selected_file_type} sample saved to {sample_path}.")
    
            # ✅ Auto-regenerate destination template if not found
            dest_template_path = os.path.join(paths["CONFIG_DIR"], f"{selected_file_type}_destination_template.csv")
            if not os.path.exists(dest_template_path):
                if selected_file_type in DEFAULT_TEMPLATES:
                    default_template_df = pd.DataFrame(DEFAULT_TEMPLATES[selected_file_type])
                    default_template_df.to_csv(dest_template_path, index=False)
                    st.success(f"✅ Destination template generated for {selected_file_type}")
                else:
                    st.warning(f"No default template found for {selected_file_type}")
    
            # ✅ Auto-regenerate column mapping if not found
            mapping_path = os.path.join(paths["CONFIG_DIR"], f"{selected_file_type}_column_mapping.json")
            if not os.path.exists(mapping_path):
                default_mapping = [
                    {
                        "source_column": col,
                        "destination_column": col,
                        "transformation": "None"
                    } for col in df.columns
                ]
                with open(mapping_path, "w") as f:
                    json.dump(default_mapping, f, indent=4)
                st.success(f"✅ Column mapping file generated for {selected_file_type}")


    with tab2:
        template_type = st.radio("Select Template Type", source_options if mode == "payroll" else ["Level", "Association"], horizontal=True, key=f"template_type_{mode}")
        render_template_editor(template_type, mode)

    with tab3:
        manage_picklists(mode)

    with tab4:
        render_column_mapping_interface(mode)
# ✅ Save functions
def save_template(template_df: pd.DataFrame, file_key: str, mode: str):
    path = os.path.join(f"{mode}_configs", "configs", f"{file_key}_destination_template.csv")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    template_df.to_csv(path, index=False)

def save_column_mapping(mapping: List[Dict], file_key: str, mode: str):
    path = os.path.join(f"{mode}_configs", "configs", f"{file_key}_column_mapping.json")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        json.dump(mapping, f, indent=2)

def save_picklist(df: pd.DataFrame, filename: str, mode: str):
    path = os.path.join(f"{mode}_configs", "picklists", filename)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    df.to_csv(path, index=False)

# ✅ Regenerate if missing
def regenerate_default_template(file_key: str, mode: str) -> None:
    """Create default template if missing."""
    path = os.path.join(f"{mode}_configs", "configs", f"{file_key}_destination_template.csv")
    if not os.path.exists(path):
        default = DEFAULT_TEMPLATES.get(file_key.lower(), [])
        df = pd.DataFrame(default)
        df.to_csv(path, index=False)

def regenerate_default_mapping(file_key: str, mode: str) -> None:
    """Create blank mapping file if missing."""
    path = os.path.join(f"{mode}_configs", "configs", f"{file_key}_column_mapping.json")
    if not os.path.exists(path):
        with open(path, "w") as f:
            json.dump([], f, indent=2)
# ✅ Transformation options used in Column Mapping
TRANSFORMATION_LIBRARY = {
    "None": lambda x: x,
    "Uppercase": lambda x: str(x).upper() if pd.notna(x) else x,
    "Lowercase": lambda x: str(x).lower() if pd.notna(x) else x,
    "Trim Spaces": lambda x: str(x).strip() if pd.notna(x) else x,
    "To Integer": lambda x: int(x) if pd.notna(x) and str(x).isdigit() else x,
    "To Float": lambda x: float(x) if pd.notna(x) else x,
    "Date Only": lambda x: str(x).split(" ")[0] if pd.notna(x) and isinstance(x, str) else x,
}
