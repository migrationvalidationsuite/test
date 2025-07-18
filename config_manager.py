import streamlit as st
import pandas as pd
import os
import json
from pathlib import Path
from typing import List, Dict, Optional, Union

# Constants for different tool modes
BASE_DIR = {
    "foundation": "foundation_configs",
    "payroll": "payroll_configs"
}

MAX_SAMPLE_ROWS = 1000

# Utility to get all necessary directories for a given mode
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

def initialize_directories(mode: str) -> None:
    """Ensure mode-specific directories exist."""
    paths = get_paths(mode)
    for path in paths.values():
        Path(path).mkdir(parents=True, exist_ok=True)
# Transformation logic
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
"""

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
    ]
}

def safe_get_sample_value(col_data: pd.Series) -> str:
    if len(col_data) > 0:
        sample = col_data.iloc[0]
        if pd.isna(sample):
            return "NULL"
        return str(sample) if not isinstance(sample, (str, int, float, bool)) else str(sample)
    return ""

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
def get_dir(base: str, mode: str) -> str:
    """Returns the mode-specific directory path."""
    return os.path.join(base, mode)

def get_config_path(config_type: str, mode: str) -> str:
    """Returns full path to the config file."""
    return os.path.join(get_dir(CONFIG_DIR, mode), f"{config_type}_config.json")

def get_sample_path(file_type: str, mode: str) -> str:
    """Returns full path to the source sample file."""
    return os.path.join(get_dir(SOURCE_SAMPLES_DIR, mode), f"{file_type}_sample.csv")

def get_picklist_path(file_name: str, mode: str) -> str:
    """Returns full path to picklist file."""
    return os.path.join(get_dir(PICKLIST_DIR, mode), file_name)

def load_config(config_type: str, mode: str) -> Optional[Union[Dict, List]]:
    """Load a config file."""
    try:
        path = get_config_path(config_type, mode)
        if not os.path.exists(path):
            return None
        with open(path, "r") as f:
            data = json.load(f)
            if config_type in ["level", "association"]:
                if isinstance(data, str):
                    data = json.loads(data)
                if not isinstance(data, list):
                    return None
            return data
    except Exception as e:
        st.error(f"[{mode}] Error loading config: {str(e)}")
        return None

def save_config(config_type: str, config_data: Union[Dict, List], mode: str) -> None:
    """Save config safely."""
    try:
        os.makedirs(get_dir(CONFIG_DIR, mode), exist_ok=True)
        final_path = get_config_path(config_type, mode)
        temp_path = final_path + ".tmp"
        with open(temp_path, "w") as f:
            json.dump(config_data, f, indent=2)
        if os.path.exists(final_path):
            os.remove(final_path)
        os.rename(temp_path, final_path)
    except Exception as e:
        st.error(f"[{mode}] Error saving config: {str(e)}")
def validate_sample_columns(source_file: str, sample_df: pd.DataFrame) -> tuple:
    """Validate required columns exist in sample."""
    required = {
        "HRP1000": ["Object ID", "Name", "Start date"],
        "HRP1001": ["Source ID", "Target object ID", "Start date"]
    }
    missing = set(required.get(source_file, [])) - set(sample_df.columns)
    return (False, f"Missing required: {', '.join(missing)}") if missing else (True, "Valid columns")

def process_uploaded_file(uploaded_file, source_file_type: str, mode: str) -> None:
    """Read, validate, and store uploaded file sample."""
    try:
        df = pd.read_excel(uploaded_file) if uploaded_file.name.endswith('.xlsx') else pd.read_csv(uploaded_file)
        df = df.head(MAX_SAMPLE_ROWS)

        valid, msg = validate_sample_columns(source_file_type, df)
        if not valid:
            st.error(msg)
            return

        path = get_sample_path(source_file_type, mode)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        df.to_csv(path, index=False)
        st.success(f"{source_file_type} sample saved to {mode} mode")

        with st.expander("Preview Sample File", expanded=True):
            st.dataframe(df.astype(str))

        st.subheader("Column Info")
        col_data = [
            {
                "Column": col,
                "Type": str(df[col].dtype),
                "Unique Values": df[col].nunique(),
                "Sample": safe_get_sample_value(df[col])
            } for col in df.columns
        ]
        st.dataframe(pd.DataFrame(col_data))

    except Exception as e:
        st.error(f"[{mode}] Error processing file: {str(e)}")
def get_picklist_dir(mode: str) -> str:
    return os.path.join(PICKLIST_DIR, mode)

def get_sample_path(source_file_type: str, mode: str) -> str:
    """Return full path to the saved sample file."""
    paths = get_paths(mode)
    return os.path.join(paths["SAMPLES_DIR"], f"{source_file_type}_sample.csv")


def get_config_path(config_type: str, mode: str) -> str:
    return os.path.join(CONFIG_DIR, mode, f"{config_type}_config.json")

def save_config(config_type: str, config_data: Union[Dict, List], mode: str) -> None:
    """Save config data to file."""
    path = get_config_path(config_type, mode)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    try:
        with open(path, "w") as f:
            json.dump(config_data, f, indent=2)
        st.success(f"Saved {config_type} config ({mode})")
    except Exception as e:
        st.error(f"Error saving {config_type} config: {e}")

def load_config(config_type: str, mode: str) -> Optional[Union[Dict, List]]:
    """Load config file if exists."""
    path = get_config_path(config_type, mode)
    try:
        if not os.path.exists(path):
            return None
        with open(path, "r") as f:
            return json.load(f)
    except Exception as e:
        st.error(f"Error loading {config_type} config for {mode}: {e}")
        return None

def render_template_editor(template_type: str, mode: str) -> None:
    """Render the template editor with dynamic config directory based on mode."""
    st.subheader(f"{template_type} Template Configuration")

    paths = get_paths(mode)
    config_path = paths["CONFIG_DIR"]
    default_template = DEFAULT_TEMPLATES[template_type.lower()]

    config_file = os.path.join(config_path, f"{template_type.lower()}_config.json")
    if os.path.exists(config_file):
        with open(config_file, "r") as f:
            try:
                current_template = json.load(f)
            except json.JSONDecodeError:
                current_template = default_template
    else:
        current_template = default_template

    if f"{template_type}_template" not in st.session_state:
        st.session_state[f"{template_type}_template"] = current_template.copy()

    edit_mode = st.radio(
        "Edit Mode:",
        ["Table Editor", "Text Input"],
        horizontal=True,
        key=f"{template_type}_edit_mode"
    )

    if st.button("Reset to Default Templates"):
        st.session_state[f"{template_type}_template"] = default_template.copy()
        with open(config_file, "w") as f:
            json.dump(st.session_state[f"{template_type}_template"], f, indent=2)
        st.success(f"{template_type} template reset to default!")
        st.rerun()

    if edit_mode == "Table Editor":
        for i, row in enumerate(st.session_state[f"{template_type}_template"]):
            cols = st.columns([3, 3, 3, 1])
            row['target_column1'] = cols[0].text_input(
                "System Column Name", value=row['target_column1'], key=f"{template_type}_col1_{i}", label_visibility="collapsed"
            )
            row['target_column2'] = cols[1].text_input(
                "Display Name", value=row['target_column2'], key=f"{template_type}_col2_{i}", label_visibility="collapsed"
            )
            row['description'] = cols[2].text_input(
                "Description", value=row.get('description', ''), key=f"{template_type}_desc_{i}", label_visibility="collapsed"
            )
            if cols[3].button("🗑️", key=f"{template_type}_del_{i}"):
                del st.session_state[f"{template_type}_template"][i]
                st.rerun()

        if st.button("Save Template"):
            with open(config_file, "w") as f:
                json.dump(st.session_state[f"{template_type}_template"], f, indent=2)
            st.success("Template saved successfully!")

    else:  # Text Input
        text_input = st.text_area(
            "Template (CSV format: col1,col2,desc)",
            value=convert_template_to_text(st.session_state[f"{template_type}_template"]),
            height=250
        )
        if st.button("Apply Text Changes"):
            try:
                parsed = convert_text_to_template(text_input)
                st.session_state[f"{template_type}_template"] = parsed
                st.success("Template updated!")
                st.rerun()
            except Exception as e:
                st.error(f"Failed to parse input: {e}")

def show_admin_panel(mode: str = "foundation") -> None:
    """Render the admin interface based on selected mode."""
    st.title(f"Configuration Manager – {mode.capitalize()} Mode")

    initialize_directories(mode)

    tab1, tab2, tab3, tab4 = st.tabs([
        "📂 Source File Samples",
        "📄 Destination Templates",
        "🗃️ Picklist Management",
        "🔄 Column Mapping"
    ])

    with tab1:
        st.subheader("Upload Source File Samples")
        st.info("Upload sample files first to configure column mappings")

        source_file_type = st.radio("Select source file type:", ["HRP1000", "HRP1001"], horizontal=True)

        uploaded_file = st.file_uploader(
            f"Upload {source_file_type} sample file (CSV or Excel)",
            type=["csv", "xlsx"],
            key=f"{source_file_type}_{mode}_upload"
        )

        if uploaded_file:
            process_uploaded_file(uploaded_file, source_file_type, mode)

        sample_path = get_sample_path(source_file_type, mode)
        if os.path.exists(sample_path):
            st.subheader("Current Sample Info")
            try:
                df = pd.read_csv(sample_path, nrows=1)
                st.info(f"Current sample has {len(df.columns)} columns")
                is_valid, msg = validate_sample_columns(source_file_type, df)
                st.success(msg) if is_valid else st.error(msg)
                st.write("Available Columns:", ", ".join(df.columns.tolist()))
            except Exception as e:
                st.error(f"Error reading sample: {e}")
        else:
            st.info(f"No sample uploaded for {source_file_type} yet")

    with tab2:
        template_type = st.radio("Select template type:", ["Level", "Association"], horizontal=True)
        render_template_editor(template_type, mode)

    with tab3:
        manage_picklists(mode)

    with tab4:
        render_column_mapping_interface(mode)
if __name__ == "__main__":
    import streamlit.web.bootstrap

    def run():
        import streamlit as st
        mode = st.sidebar.selectbox("Select Configuration Mode", ["foundation", "payroll"], key="mode_select")
        show_admin_panel(mode)

    streamlit.web.bootstrap.run(run, "", [])
