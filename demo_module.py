# demo_module.py

import streamlit as st
import pandas as pd
import plotly.express as px

def render():
    st.subheader("🚀 Unified User Processing App")

    uploaded_files = st.file_uploader("Upload files", type=["xlsx"], accept_multiple_files=True)

    st.markdown("### 🛠️ Default Values")
    default_position = st.text_input("Default Position", "SPECIALIST")
    default_org_unit = st.text_input("Default Org Unit", "10202155")
    default_location_code = st.text_input("Default Location Code", "AL")
    default_country = st.selectbox("Country", ["Australia", "India", "USA"], index=0)
    default_state = st.selectbox("State", ["NSW", "VIC", "QLD", "ACT"], index=0)
    default_timezone = st.selectbox("Timezone", ["AEST", "IST", "PST", "UTC"], index=0)

    tab1, tab2, tab3, tab4 = st.tabs([
        "Basic Generator Panel", 
        "Validation Panel", 
        "Statistics Summary", 
        "Dashboard Builder"
    ])
    combined_df = pd.DataFrame()

    def clean_columns(df):
        df.columns = df.columns.str.strip().str.lower().str.replace('.', '', regex=False).str.replace(' ', '_')
        return df

    if uploaded_files:
        for file in uploaded_files:
            df = pd.read_excel(file)
            df = clean_columns(df)
            df['position'] = df.get('position', default_position)
            df['org_unit'] = df.get('org_unit', default_org_unit)
            df['location_code'] = df.get('location_code', default_location_code)
            df['country'] = default_country
            df['state'] = default_state
            df['timezone'] = default_timezone
            combined_df = pd.concat([combined_df, df], ignore_index=True)

        with tab1:
            st.success("✅ Files uploaded and merged successfully.")
            st.dataframe(combined_df)

        with tab2:
            st.warning("⚠️ Validation not yet implemented. This is a placeholder.")
            st.dataframe(combined_df.head(10))

        with tab3:
            st.subheader("📊 Summary Statistics")
            if not combined_df.empty:
                st.write(combined_df.describe(include='all'))
            else:
                st.info("No data to summarize.")

        with tab4:
            st.subheader("📈 Dashboard Builder")
            if not combined_df.empty:
                numeric_cols = combined_df.select_dtypes(include=['number']).columns.tolist()
                cat_cols = combined_df.select_dtypes(include=['object']).columns.tolist()
                col1, col2 = st.columns(2)
                with col1:
                    x_axis = st.selectbox("X-axis", options=numeric_cols)
                with col2:
                    y_axis = st.selectbox("Y-axis", options=numeric_cols)
                if x_axis and y_axis:
                    fig = px.scatter(combined_df, x=x_axis, y=y_axis, color=cat_cols[0] if cat_cols else None)
                    st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Upload data to build dashboard.")
    else:
        st.info("⬅️ Please upload at least one .xlsx file.")
