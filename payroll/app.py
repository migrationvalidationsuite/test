import streamlit as st
import pandas as pd
import os
import json
from io import BytesIO
import plotly.express as px
from config_manager import get_paths, show_admin_panel

# Initialize session state
def init_session():
    for key, default in {
        "payroll_raw": {},
        "payroll_cleaned": {},
        "payroll_transformed": {},
    }.items():
        if key not in st.session_state:
            st.session_state[key] = default
def load_mapping(file_key, mode="payroll"):
    config_path = os.path.join(get_paths(mode)["CONFIG_DIR"], f"{file_key}_column_mapping.json")
    if os.path.exists(config_path):
        with open(config_path, "r") as f:
            return json.load(f)
    return []

def load_template(file_key, mode="payroll"):
    template_path = os.path.join(get_paths(mode)["CONFIG_DIR"], f"{file_key}_destination_template.csv")
    if os.path.exists(template_path):
        return pd.read_csv(template_path)
    return pd.DataFrame()

def cleanse_dataframe(df, trim=True, lower=True, empty_nan=True, drop_null=False):
    df = df.copy()
    if trim:
        df = df.applymap(lambda x: str(x).strip() if isinstance(x, str) else x)
    if lower:
        df = df.applymap(lambda x: str(x).lower() if isinstance(x, str) else x)
    if empty_nan:
        df.replace("", pd.NA, inplace=True)
    if drop_null:
        df.dropna(how="all", inplace=True)
    return df

def apply_transformation(value, transformation):
    try:
        if transformation == "None":
            return value
        elif transformation == "UPPERCASE":
            return str(value).upper()
        elif transformation == "lowercase":
            return str(value).lower()
        elif transformation == "Title Case":
            return str(value).title()
        elif transformation == "Trim Whitespace":
            return str(value).strip()
        elif transformation == "Date Format (YYYY-MM-DD)":
            return pd.to_datetime(value).strftime("%Y-%m-%d")
        else:
            return value
    except:
        return value

def apply_transformations(df, mappings):
    transformed_rows = []
    for _, row in df.iterrows():
        new_row = {}
        for map_item in mappings:
            src = map_item.get("source_column")
            dst = map_item.get("destination_column")
            transformation = map_item.get("transformation", "None")
            value = row.get(src, "")
            new_row[dst] = apply_transformation(value, transformation)
        transformed_rows.append(new_row)
    return pd.DataFrame(transformed_rows)
def render_payroll_tool():
    st.title("💰 Enhanced Payroll Mapping Tool")
    mode = "payroll"
    paths = get_paths(mode)

    file_options = ["PA0008", "PA0014"]
    selected_file = st.radio("Select Payroll File Type", file_options, horizontal=True)

    uploaded_file = st.file_uploader(f"Upload {selected_file} file", type=["csv", "xlsx"], key=f"{selected_file}_upload")
    if uploaded_file:
        df = pd.read_csv(uploaded_file) if uploaded_file.name.endswith(".csv") else pd.read_excel(uploaded_file)
        st.session_state["payroll_data"][selected_file] = df
        st.success(f"✅ {selected_file} uploaded successfully")
        
        # 🔄 Save sample to source_samples
        sample_path = os.path.join(paths["SAMPLES_DIR"], f"{selected_file}.csv")
        df.to_csv(sample_path, index=False)

        # 🔄 Regenerate destination template if not found
        template_path = os.path.join(paths["CONFIG_DIR"], f"{selected_file}_destination_template.csv")
        if not os.path.exists(template_path):
            if selected_file in DEFAULT_TEMPLATES:
                default_template = pd.DataFrame(DEFAULT_TEMPLATES[selected_file])
                default_template.to_csv(template_path, index=False)
                st.success(f"✅ Destination template generated for {selected_file}")
            else:
                st.warning(f"No default template found for {selected_file}")

        # 🔄 Regenerate column mapping if not found
        mapping_path = os.path.join(paths["CONFIG_DIR"], f"{selected_file}_column_mapping.json")
        if not os.path.exists(mapping_path):
            default_mapping = [
                {
                    "source_column": col,
                    "destination_column": col,
                    "transformation": "None"
                } for col in df.columns
            ]
            with open(mapping_path, "w") as f:
                json.dump(default_mapping, f, indent=2)
            st.success(f"✅ Column mapping created for {selected_file}")

    with st.sidebar:
        st.header("Cleansing Options")
        trim = st.checkbox("Trim Whitespace", True)
        lower = st.checkbox("Lowercase", True)
        empty_nan = st.checkbox("Empty → NaN", True)
        drop_null = st.checkbox("Drop Null Rows", False)

    mappings = load_mapping(selected_file, mode)
    template = load_template(selected_file, mode)

    if not mappings or template.empty:
        st.warning("⚠️ Missing mapping or template. Please configure in Admin Panel.")
        return

    if selected_file in st.session_state["payroll_data"]:
        raw_df = st.session_state["payroll_data"][selected_file]
        cleansed_df = cleanse_dataframe(raw_df, trim, lower, empty_nan, drop_null)
        transformed_df = apply_transformations(cleansed_df, mappings)
        st.session_state["transformed_data"][selected_file] = transformed_df

        tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
            "🧹 Cleaned & Mapped", "✅ Validation", "📊 Dashboard",
            "📈 Stats", "⬇ Download", "🛠️ Admin"
        ])

        with tab1:
            st.subheader("🔍 Transformed Data Preview")
            st.dataframe(transformed_df.head())

        with tab2:
            st.subheader("✅ Null Summary")
            null_summary = transformed_df.isnull().sum().reset_index()
            null_summary.columns = ["Column", "Null Count"]
            st.dataframe(null_summary)

        with tab3:
            st.subheader("📊 Top Value Insights")
            col = st.selectbox("Choose column", transformed_df.columns)
            if pd.api.types.is_numeric_dtype(transformed_df[col]):
                fig = px.histogram(transformed_df, x=col, title=f"Distribution of {col}")
            else:
                top_vals = transformed_df[col].value_counts().nlargest(10)
                fig = px.bar(x=top_vals.index, y=top_vals.values, title=f"Top Values in {col}")
            st.plotly_chart(fig, use_container_width=True)

        with tab4:
            st.subheader("📈 Descriptive Statistics")
            st.dataframe(transformed_df.describe(include='all'), use_container_width=True)

        with tab5:
            st.subheader("⬇ Export Cleaned Files")
            col1, col2 = st.columns(2)
            with col1:
                st.download_button(
                    "📥 Download CSV",
                    data=transformed_df.to_csv(index=False),
                    file_name=f"{selected_file}_output.csv",
                    mime="text/csv"
                )
            with col2:
                st.download_button(
                    "📥 Download Excel",
                    data=to_excel(transformed_df),
                    file_name=f"{selected_file}_output.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )

        with tab6:
            st.subheader("🛠️ Admin Panel")
            show_admin_panel(mode)
def cleanse_dataframe(df, trim=True, lower=True, empty_nan=True, drop_null=False):
    df = df.copy()
    if trim:
        df = df.applymap(lambda x: str(x).strip() if isinstance(x, str) else x)
    if lower:
        df = df.applymap(lambda x: str(x).lower() if isinstance(x, str) else x)
    if empty_nan:
        df.replace("", pd.NA, inplace=True)
    if drop_null:
        df.dropna(how="all", inplace=True)
    return df

def apply_transformation(value, transformation):
    try:
        if transformation == "None":
            return value
        elif transformation == "UPPERCASE":
            return str(value).upper()
        elif transformation == "lowercase":
            return str(value).lower()
        elif transformation == "Title Case":
            return str(value).title()
        elif transformation == "Trim Whitespace":
            return str(value).strip()
        elif transformation == "Extract First Word":
            return str(value).split()[0]
        elif transformation == "Date Format (YYYY-MM-DD)":
            return pd.to_datetime(value).strftime("%Y-%m-%d")
        else:
            return value
    except:
        return value

def apply_transformations(df, mappings, picklists):
    output = []
    for _, row in df.iterrows():
        new_row = {}
        for mapping in mappings:
            src = mapping.get("source_column")
            dest = mapping.get("destination_column")
            transformation = mapping.get("transformation", "None")
            value = row.get(src, "")
            new_row[dest] = apply_transformation(value, transformation)
        output.append(new_row)
    return pd.DataFrame(output)

def to_excel(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Sheet1')
    return output.getvalue()

def init_session():
    defaults = {
        "current_step": "upload",
        "payroll_data": {},
        "column_mappings": {},
        "transformed_data": {}
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val
