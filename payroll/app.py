import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import json
import os
from typing import Dict

# ---------------- Utility Functions ----------------

def load_mappings(file_key, mode="payroll"):
    path = f"{mode}_configs/configs/{file_key}_column_mapping.json"
    if os.path.exists(path):
        with open(path, "r") as f:
            return json.load(f)
    return []

def load_picklists(mode: str) -> Dict[str, pd.DataFrame]:
    picklists = {}
    picklist_dir = os.path.join(f"{mode}_configs", "picklists")
    if os.path.exists(picklist_dir):
        for file in os.listdir(picklist_dir):
            if file.endswith(".csv"):
                try:
                    df = pd.read_csv(os.path.join(picklist_dir, file))
                    picklists[file] = df
                except:
                    continue
    return picklists

def apply_picklist_lookup(value, picklist_df, column_name):
    try:
        match = picklist_df[picklist_df[column_name] == value]
        if not match.empty:
            return match.iloc[0][1]
    except:
        pass
    return value

def apply_transformations(df, mappings, picklists=None):
    df_out = df.copy()
    for trans in mappings:
        src_col = trans["source_column"]
        dst_col = trans["destination_column"]
        trans_type = trans.get("transformation", "None")

        if trans_type == "None":
            df_out[dst_col] = df[src_col]
        elif trans_type == "UPPERCASE":
            df_out[dst_col] = df[src_col].astype(str).str.upper()
        elif trans_type == "lowercase":
            df_out[dst_col] = df[src_col].astype(str).str.lower()
        elif trans_type == "Trim Whitespace":
            df_out[dst_col] = df[src_col].astype(str).str.strip()
        elif trans_type == "Title Case":
            df_out[dst_col] = df[src_col].astype(str).str.title()
        elif trans_type == "Date Format (YYYY-MM-DD)":
            df_out[dst_col] = pd.to_datetime(df[src_col], errors="coerce").dt.strftime('%Y-%m-%d')
        elif trans_type == "Lookup Value" and picklists:
            for name, pick_df in picklists.items():
                if src_col in pick_df.columns:
                    df_out[dst_col] = df[src_col].apply(lambda x: apply_picklist_lookup(x, pick_df, src_col))
                    break
            else:
                df_out[dst_col] = df[src_col]
        else:
            df_out[dst_col] = df[src_col]
    return df_out

def cleanse_dataframe(df, trim=True, lower=True, empty_nan=True, drop_null=False):
    df_clean = df.copy()
    for col in df_clean.select_dtypes(include='object'):
        if trim:
            df_clean[col] = df_clean[col].astype(str).str.strip()
        if lower:
            df_clean[col] = df_clean[col].astype(str).str.lower()
    if empty_nan:
        df_clean.replace("", np.nan, inplace=True)
    if drop_null:
        df_clean.dropna(inplace=True)
    return df_clean
def render_payroll_tool():
    st.title("📄 Enhanced Payroll Tool with Config Manager")

    with st.sidebar:
        st.header("Cleansing Options")
        trim = st.checkbox("Trim Whitespace", True)
        lower = st.checkbox("Lowercase", True)
        empty_nan = st.checkbox("Empty → NaN", True)
        drop_null = st.checkbox("Drop Null Rows", False)

    uploaded_0008 = st.file_uploader("Upload PA0008.xlsx", type=["xlsx"], key="upload_0008")
    uploaded_0014 = st.file_uploader("Upload PA0014.xlsx", type=["xlsx"], key="upload_0014")

    if uploaded_0008 and uploaded_0014:
        df_8_raw = pd.read_excel(uploaded_0008)
        df_14_raw = pd.read_excel(uploaded_0014)

        df_8_clean = cleanse_dataframe(df_8_raw, trim, lower, empty_nan, drop_null)
        df_14_clean = cleanse_dataframe(df_14_raw, trim, lower, empty_nan, drop_null)

        mappings_0008 = load_mappings("PA0008")
        mappings_0014 = load_mappings("PA0014")
        picklists = load_picklists("payroll")

        df_8_transformed = apply_transformations(df_8_clean, mappings_0008, picklists)
        df_14_transformed = apply_transformations(df_14_clean, mappings_0014, picklists)

        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "🧹 Cleaned & Mapped", "✅ Validation", "📊 Dashboard", "📈 Stats", "⬇ Download"
        ])

        with tab1:
            st.subheader("PA0008 – Transformed")
            st.dataframe(df_8_transformed, use_container_width=True)
            st.subheader("PA0014 – Transformed")
            st.dataframe(df_14_transformed, use_container_width=True)

        with tab2:
            st.subheader("Null Summary – PA0008")
            st.dataframe(df_8_transformed.isnull().sum().reset_index(names=["Column", "Nulls"]))
            if "amount" in df_8_transformed.columns:
                st.subheader("Negative Amounts")
                st.dataframe(df_8_transformed[df_8_transformed["amount"] < 0])

        with tab3:
            st.subheader("Top Value Insights – PA0008")
            col = st.selectbox("Choose column", df_8_transformed.columns)
            if pd.api.types.is_numeric_dtype(df_8_transformed[col]):
                fig = px.histogram(df_8_transformed, x=col, title=f"Distribution of {col}")
            else:
                top_vals = df_8_transformed[col].value_counts().nlargest(10)
                fig = px.bar(x=top_vals.index, y=top_vals.values, title=f"Top Values in {col}")
            st.plotly_chart(fig, use_container_width=True)

        with tab4:
            st.subheader("Descriptive Stats – PA0008")
            st.dataframe(df_8_transformed.describe(include='all'), use_container_width=True)

        with tab5:
            col1, col2 = st.columns(2)
            with col1:
                st.download_button("⬇ PA0008 as CSV", df_8_transformed.to_csv(index=False), file_name="PA0008_output.csv")
                st.download_button("⬇ PA0014 as CSV", df_14_transformed.to_csv(index=False), file_name="PA0014_output.csv")
            with col2:
                st.download_button("⬇ PA0008 Excel", df_8_transformed.to_excel(index=False, engine='openpyxl'), file_name="PA0008_output.xlsx")
                st.download_button("⬇ PA0014 Excel", df_14_transformed.to_excel(index=False, engine='openpyxl'), file_name="PA0014_output.xlsx")
def render_payroll_tool():
    st.title("📄 Enhanced Payroll Tool with Config Manager")

    with st.sidebar:
        st.header("Cleansing Options")
        trim = st.checkbox("Trim Whitespace", True)
        lower = st.checkbox("Lowercase", True)
        empty_nan = st.checkbox("Empty → NaN", True)
        drop_null = st.checkbox("Drop Null Rows", False)

    uploaded_0008 = st.file_uploader("Upload PA0008.xlsx", type=["xlsx"], key="upload_0008")
    uploaded_0014 = st.file_uploader("Upload PA0014.xlsx", type=["xlsx"], key="upload_0014")

    if uploaded_0008 and uploaded_0014:
        df_8_raw = pd.read_excel(uploaded_0008)
        df_14_raw = pd.read_excel(uploaded_0014)

        df_8_clean = cleanse_dataframe(df_8_raw, trim, lower, empty_nan, drop_null)
        df_14_clean = cleanse_dataframe(df_14_raw, trim, lower, empty_nan, drop_null)

        mappings_0008 = load_mappings("PA0008")
        mappings_0014 = load_mappings("PA0014")
        picklists = load_picklists("payroll")

        df_8_transformed = apply_transformations(df_8_clean, mappings_0008, picklists)
        df_14_transformed = apply_transformations(df_14_clean, mappings_0014, picklists)

        tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
            "🧹 Cleaned & Mapped", "✅ Validation", "📊 Dashboard",
            "📈 Stats", "⬇ Download", "💬 Ask Your Data"
        ])

        with tab1:
            st.subheader("PA0008 – Transformed")
            st.dataframe(df_8_transformed, use_container_width=True)
            st.subheader("PA0014 – Transformed")
            st.dataframe(df_14_transformed, use_container_width=True)

        with tab2:
            st.subheader("Null Summary – PA0008")
            st.dataframe(df_8_transformed.isnull().sum().reset_index(names=["Column", "Nulls"]))
            if "amount" in df_8_transformed.columns:
                st.subheader("Negative Amounts")
                st.dataframe(df_8_transformed[df_8_transformed["amount"] < 0])

        with tab3:
            st.subheader("Top Value Insights – PA0008")
            col = st.selectbox("Choose column", df_8_transformed.columns)
            if pd.api.types.is_numeric_dtype(df_8_transformed[col]):
                fig = px.histogram(df_8_transformed, x=col, title=f"Distribution of {col}")
            else:
                top_vals = df_8_transformed[col].value_counts().nlargest(10)
                fig = px.bar(x=top_vals.index, y=top_vals.values, title=f"Top Values in {col}")
            st.plotly_chart(fig, use_container_width=True)

        with tab4:
            st.subheader("Descriptive Stats – PA0008")
            st.dataframe(df_8_transformed.describe(include='all'), use_container_width=True)

        with tab5:
            col1, col2 = st.columns(2)
            with col1:
                st.download_button("⬇ PA0008 as CSV", df_8_transformed.to_csv(index=False), file_name="PA0008_output.csv")
                st.download_button("⬇ PA0014 as CSV", df_14_transformed.to_csv(index=False), file_name="PA0014_output.csv")
            with col2:
                st.download_button("⬇ PA0008 Excel", df_8_transformed.to_excel(index=False, engine='openpyxl'), file_name="PA0008_output.xlsx")
                st.download_button("⬇ PA0014 Excel", df_14_transformed.to_excel(index=False, engine='openpyxl'), file_name="PA0014_output.xlsx")

        with tab6:
            st.subheader("💬 Ask Your Data (LLM)")
            query = st.text_input("Ask a question about PA0008:")
            if query:
                if not llm_enabled:
                    st.error("Ollama is not available.")
                else:
                    st.markdown("**Answer:**")
                    st.write(get_nlp_answer(query, df_8_transformed))
