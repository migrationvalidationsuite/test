import streamlit as st
import pandas as pd
import os
import traceback
import plotly.express as px

from employeedata.app.utils.transformations import apply_transformations
from employeedata.app.utils.validation import build_validation_panel, build_statistics_panel

def render_employee_v2():
    st.title("🔄 Data Migration & Transformation Tool")

    mode = st.sidebar.radio("🌐 Who are you?", ["Developer Admin", "Developer"])

    if mode == "Developer Admin":
        # 🔐 Password protection
        if "admin_authenticated" not in st.session_state:
            st.session_state.admin_authenticated = False

        if not st.session_state.admin_authenticated:
            password = st.sidebar.text_input("🔐 Enter Admin Password", type="password")
            if password == "test":  # 🔁 Change this to your real password
                st.session_state.admin_authenticated = True
                st.success("✅ Access granted.")
            else:
                st.warning("⚠️ Incorrect password or empty field.")
                return

        # 🛠️ Admin panel
        st.sidebar.subheader("🛠️ Developer Admin Setup")

        mapping_file = st.sidebar.file_uploader("Upload Mapping Sheet (.xlsx)", type=["xlsx"])
        picklist_files = st.sidebar.file_uploader("Upload Picklist Files (.csv)", type=["csv"], accept_multiple_files=True)
        output_template = st.sidebar.file_uploader("Upload Final Output Template (.csv)", type=["csv"])

        if st.sidebar.button("Save Admin Config"):
            if mapping_file and output_template:
                st.session_state["mapping_file"] = mapping_file
                st.session_state["output_template"] = output_template
                st.session_state["picklist_files"] = picklist_files
                st.success("✅ Admin config saved. Developer can now run transformation.")
            else:
                st.warning("⚠️ Please upload both Mapping Sheet and Output Template before saving.")
        return

    if "mapping_file" not in st.session_state or "output_template" not in st.session_state:
        st.error("⚠️ Admin setup not completed. Please contact Developer Admin.")
        return

    st.sidebar.subheader("👨‍💻 Developer Execution")
    uploaded_files = st.sidebar.file_uploader("Upload Source Files", type=["xlsx"], accept_multiple_files=True)
    date_format = st.sidebar.selectbox("📅 Date Format", ["%d/%m/%Y", "%d-%m-%Y", "%d%m%Y"])

    if uploaded_files:
        try:
            mapping_df = pd.read_excel(st.session_state["mapping_file"])
            output_template_df = pd.read_csv(st.session_state["output_template"], header=[0, 1])
            source_data = {os.path.splitext(f.name)[0]: pd.read_excel(f) for f in uploaded_files}

            picklists = {}
            if "picklist_files" in st.session_state:
                for f in st.session_state["picklist_files"]:
                    name = os.path.splitext(f.name)[0]
                    picklists[name] = pd.read_csv(f)

            with st.spinner("🧠 Applying transformations..."):
                data_rows, header_rows, logs = apply_transformations(mapping_df, source_data, date_format, picklists)
                final_df = pd.concat([header_rows, data_rows], ignore_index=True)

                validation_df = build_validation_panel(logs)
                stats_df = build_statistics_panel(final_df.iloc[2:], validation_df)

            st.subheader("📤 Transformed Output")
            st.dataframe(final_df.head(20), use_container_width=True)
            st.download_button("⬇️ Download Final Output", final_df.to_csv(index=False, header=False), "transformed_output.csv")

            st.subheader("🧪 Validation Panel")
            st.dataframe(validation_df, use_container_width=True)
            st.download_button("⬇️ Download Validation Report", validation_df.to_csv(index=False), "validation_report.csv")

            st.subheader("📊 Migration Statistics")
            col1, col2 = st.columns([2, 2])
            with col1:
                pie = px.pie(stats_df, names='Metric', values='Value', color='Metric',
                            color_discrete_map={"Success Columns": "green", "Missing Columns": "orange", "Error Columns": "red"})
                pie.update_layout(height=300, width=300, margin=dict(t=20, b=20, l=0, r=0))
                st.plotly_chart(pie, use_container_width=False)
            with col2:
                selected = st.selectbox("🔍 Drilldown Issues", ["Missing Columns", "Error Columns"])
                st.dataframe(validation_df[validation_df["Status"] == selected.split()[0]])

        except Exception as e:
            st.error("❌ Error during transformation")
            st.exception(traceback.format_exc())
    else:
        st.info("📎 Please upload source files to begin transformation.")
