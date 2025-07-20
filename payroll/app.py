import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

# Optional: LLM support
try:
    from langchain.llms import Ollama
    from langchain.chains import LLMChain
    from langchain.prompts import PromptTemplate
    llm_enabled = True
except:
    llm_enabled = False

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
    st.subheader(f"🧾 Metadata for {label}")
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

    with st.sidebar:
        st.header("Cleansing Options")
        trim = st.checkbox("Trim Whitespace", True)
        lower = st.checkbox("Lowercase", True)
        empty_nan = st.checkbox("Empty → NaN", True)
        drop_null = st.checkbox("Drop Null Rows", False)

    uploaded_0008 = st.file_uploader("Upload PA0008.xlsx", type=["xlsx"])
    uploaded_0014 = st.file_uploader("Upload PA0014.xlsx", type=["xlsx"])

    if uploaded_0008 and uploaded_0014:
        df_8 = load_data(uploaded_0008)
        df_14 = load_data(uploaded_0014)

        df_8_clean = cleanse_dataframe(df_8, trim, lower, empty_nan, drop_null)
        df_14_clean = cleanse_dataframe(df_14, trim, lower, empty_nan, drop_null)

        df_8_clean = standardize_dates(df_8_clean, ["Start date", "End Date"])
        df_14_clean = standardize_dates(df_14_clean, ["Start date", "End Date"])

        tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
            "Cleanse", "Metadata", "Validation", "Dashboard", "Stats", "Ask Your Data"
        ])

        with tab1:
            st.subheader("🧹 Cleanse & Compare")
            col1, col2 = st.columns(2)
            with col1:
                st.write("PA0008 – Original")
                st.dataframe(df_8)
            with col2:
                st.write("PA0008 – Cleansed")
                st.dataframe(show_comparison(df_8, df_8_clean))

            col3, col4 = st.columns(2)
            with col3:
                st.write("PA0014 – Original")
                st.dataframe(df_14)
            with col4:
                st.write("PA0014 – Cleansed")
                st.dataframe(show_comparison(df_14, df_14_clean))

        with tab2:
            display_metadata(df_8_clean, "PA0008")
            display_metadata(df_14_clean, "PA0014")

        with tab3:
            show_validation(df_8_clean)

        with tab4:
            show_dashboard(df_8_clean)

        with tab5:
            descriptive_statistics(df_8_clean)

        with tab6:
            st.subheader("💬 Ask Your Data")
            query = st.text_input("Ask a question:")
            if query:
                st.markdown("**Answer:**")
                st.write(get_nlp_answer(query, df_8_clean))
