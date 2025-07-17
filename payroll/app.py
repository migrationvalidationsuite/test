import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

try:
    from langchain.llms import Ollama
    from langchain.chains import LLMChain
    from langchain.prompts import PromptTemplate
    llm_enabled = True
except:
    llm_enabled = False

from config_manager import (
    show_admin_panel,
    initialize_directories,
    render_template_editor,
    manage_picklists,
    render_column_mapping_interface,
    get_source_columns,
    get_picklist_columns,
    load_config,
    DEFAULT_TEMPLATES,
    save_config,
    process_uploaded_file
)


from foundation_module.foundation_app import render as render_foundation
from employee_app import render_employee_tool
from employeedata.app.data_migration_tool import render_employee_v2
@st.cache_data
def load_data(file):
    return pd.read_excel(file)

def cleanse_dataframe(df, trim_whitespace=True, lowercase=True, empty_to_nan=True, drop_null_rows=False):
    df_clean = df.copy()
    for col in df_clean.columns:
        if df_clean[col].dtype == 'object':
            if trim_whitespace:
                df_clean[col] = df_clean[col].astype(str).str.strip()
            if lowercase:
                df_clean[col] = df_clean[col].astype(str).str.lower()
    if empty_to_nan:
        df_clean.replace("", np.nan, inplace=True)
    if drop_null_rows:
        df_clean.dropna(inplace=True)
    return df_clean

def standardize_dates(df, date_columns):
    def try_parse(val):
        for fmt in ("%d.%m.%Y", "%d/%m/%Y", "%Y-%m-%d"):
            try:
                return pd.to_datetime(val, format=fmt)
            except:
                continue
        return pd.NaT

    df_copy = df.copy()
    for col in date_columns:
        if col in df_copy.columns:
            df_copy[col] = df_copy[col].apply(try_parse)
    return df_copy
def show_comparison(original, cleansed):
    diff_df = original.copy()
    for col in original.columns:
        if col in cleansed.columns:
            diff_df[col] = np.where(original[col] != cleansed[col], "🟡 " + cleansed[col].astype(str), cleansed[col])
    return diff_df

def display_metadata(df, label):
    st.subheader(f"📜 Metadata for {label}")
    st.write("**Data Types:**")
    st.write(df.dtypes)
    st.write("**Null Count:**")
    st.write(df.isnull().sum())
    st.write("**Unique Values:**")
    st.write(df.nunique())

def show_dashboard(df):
    st.subheader("📊 Dashboard")
    selected_col = st.selectbox("Select column:", df.columns)

    nulls = df.isnull().sum()
    nulls = nulls[nulls > 0]

    if nulls.empty:
        st.info("✅ No missing values detected.")
    else:
        fig = px.bar(x=nulls.index, y=nulls.values, title="Nulls per Column", labels={'x': 'Column', 'y': 'Nulls'})
        st.plotly_chart(fig, use_container_width=True)

    st.markdown("**Value Distribution**")
    if pd.api.types.is_numeric_dtype(df[selected_col]):
        fig2 = px.histogram(df, x=selected_col, title=f"{selected_col} Distribution")
    else:
        top_vals = df[selected_col].value_counts().nlargest(10)
        fig2 = px.bar(x=top_vals.index, y=top_vals.values, title=f"Top Values in {selected_col}")
    st.plotly_chart(fig2)

def descriptive_statistics(df):
    st.subheader("📈 Descriptive Stats")
    st.dataframe(df.describe(include='all'))
def show_validation(df):
    st.subheader("✅ Validation Panel")
    null_summary = df.isnull().sum().reset_index()
    null_summary.columns = ["Column", "Null Count"]
    st.dataframe(null_summary, use_container_width=True)

    if 'amount' in df.columns:
        st.write("Negative Amounts:")
        st.dataframe(df[df['amount'] < 0])

def get_nlp_answer(query, df):
    if not llm_enabled:
        return "❌ Ollama not available."
    llm = Ollama(model="mistral")
    context = f"Columns: {', '.join(df.columns)}\nPreview:\n{df.head().to_string()}"
    prompt = PromptTemplate(
        input_variables=["question", "context"],
        template="""You are a helpful data assistant. Given the context below:

{context}

Answer this:

{question}
"""
    )
    chain = LLMChain(llm=llm, prompt=prompt)
    return chain.run({"question": query, "context": context})
def render_payroll_tool():
    st.title("🔍 Enhanced Payroll Mapping & Cleansing Tool")

    view = st.radio(
        "Select View Mode", 
        ["Mapping & Cleansing", "Configuration Manager"], 
        horizontal=True,
        key="payroll_view_mode"
    )

    if view == "Mapping & Cleansing":
        # [Keep all your existing cleansing logic]
        pass
        
    elif view == "Configuration Manager":
        st.markdown("## 🛠️ Payroll Data – Configuration Manager")
        initialize_directories()

        # Use columns for better layout
        col1, col2 = st.columns([1, 3])
        
        with col1:
            st.subheader("Configuration Sections")
            config_section = st.radio(
                "Select Section:",
                ["Source Files", "Templates", "Picklists", "Mappings"],
                key="payroll_config_section"
            )
        
        with col2:
            if config_section == "Source Files":
                st.subheader("📂 Upload Source Files")
                source_type = st.radio(
                    "File Type:",
                    ["PA0008", "PA0014"],
                    horizontal=True,
                    key="payroll_source_type"
                )
                uploaded_file = st.file_uploader(
                    f"Upload {source_type} sample",
                    type=["csv", "xlsx"],
                    key=f"payroll_{source_type}_upload"
                )
                if uploaded_file:
                    process_uploaded_file(uploaded_file, source_type)
                
            elif config_section == "Templates":
                st.subheader("📄 Template Configuration")
                template_type = st.radio(
                    "Template Type:",
                    ["PA0008", "PA0014"],
                    horizontal=True,
                    key="payroll_template_type"
                )
                render_template_editor(template_type)
                
            elif config_section == "Picklists":
                st.subheader("🗃️ Picklist Management")
                manage_picklists()
                
            elif config_section == "Mappings":
                st.subheader("🔄 Column Mapping")
                render_column_mapping_interface(mode="payroll")
