import streamlit as st
import pandas as pd
from io import BytesIO
from foundation_module.utils.file_utils import load_data
from foundation_module.utils.hierarchy_utils import build_hierarchy, optimize_table_display

def generate_level_export(level_data, level_name):
    headers = [
        '[OPERATOR]', 'effectiveStartDate', 'externalCode', 
        'name.en_US', 'name.defaultValue', 'name.en_DEBUG', 'name.en_GB',
        'description.en_US', 'description.defaultValue', 
        'description.en_DEBUG', 'description.en_GB',
        'effectiveStatus', 'headOfUnit'
    ]
    descriptions = [
        'Supported operators: Delimit, Clear and Delete',
        'Start Date',
        'Code',
        'US English',
        'Default Value', 
        'English (DEBUG)',
        'English (United Kingdom)',
        'US English',
        'Default Value',
        'English (DEBUG)',
        'English (United Kingdom)',
        'Status(Valid Values : A/I)',
        'Head of Unit'
    ]
    df = pd.DataFrame(columns=headers)
    df.loc[0] = descriptions
    df.loc[1] = [''] * len(headers)

    for idx, row in level_data.iterrows():
        df.loc[idx + 2] = [
            '', '1900-01-01 00:00:00', str(row['Object ID']),
            row['Name'], row['Name'], row['Name'], '',
            row['Name'], row['Name'], row['Name'], '', 'A', ''
        ]
    return df

def generate_association_file(current_df, parent_df, hrp1001, current_name, parent_name):
    associations = []
    parent_map = hrp1001.set_index('Target object ID')['Source ID'].astype(str).to_dict()
    valid_parent_ids = set(parent_df['Object ID'].astype(str))
    
    for _, row in current_df.iterrows():
        child_id = str(row['Object ID'])
        parent_id = parent_map.get(child_id)
        if parent_id and parent_id in valid_parent_ids:
            associations.append({
                f'{current_name}Code': child_id,
                f'{parent_name}Code': parent_id
            })
    return pd.DataFrame(associations)

def show_hierarchy_panel(state):
    st.header("Hierarchy Builder")

    with st.expander("📤 Upload Files", expanded=True):
        col1, col2 = st.columns(2)
        with col1:
            hrp1000_file = st.file_uploader("Upload HRP1000 (Org Units)", type=["csv", "xlsx"],
                                            help="Must contain 'Object ID' and 'Name'")
        with col2:
            hrp1001_file = st.file_uploader("Upload HRP1001 (Relationships)", type=["csv", "xlsx"],
                                            help="Must contain 'Source ID' and 'Target object ID'")

    if st.button("🚀 Build Hierarchy", type="primary", use_container_width=True):
        if not hrp1000_file or not hrp1001_file:
            st.error("Please upload both files.")
            return
        with st.spinner("Processing..."):
            try:
                hrp1000 = load_data(hrp1000_file)
                hrp1001 = load_data(hrp1001_file)
                hrp1000['Object ID'] = hrp1000['Object ID'].astype(str)
                hrp1001['Source ID'] = hrp1001['Source ID'].astype(str)
                hrp1001['Target object ID'] = hrp1001['Target object ID'].astype(str)

                for col in ['Object ID', 'Name']:
                    if col not in hrp1000.columns:
                        raise ValueError(f"Missing column in HRP1000: {col}")
                for col in ['Source ID', 'Target object ID']:
                    if col not in hrp1001.columns:
                        raise ValueError(f"Missing column in HRP1001: {col}")

                state['hrp1000'] = hrp1000
                state['hrp1001'] = hrp1001
                state['hierarchy'] = build_hierarchy(hrp1000, hrp1001)
                st.success("Hierarchy built successfully.")
            except Exception as e:
                st.error(f"Error: {str(e)}")
                st.stop()

    if state.get('hierarchy'):
        st.divider()
        with st.expander("🔠 Customize Level Names", expanded=False):
            cols = st.columns(4)
            for level in range(1, 21):
                with cols[(level - 1) % 4]:
                    state['level_names'][level] = st.text_input(
                        f"Level {level}",
                        value=state['level_names'].get(level, f"Level {level}"),
                        key=f"level_name_{level}"
                    )

        tab1, tab2 = st.tabs(["📋 Hierarchy Table", "📤 Level Exports"])

        with tab1:
            df = state['hierarchy']['hierarchy_table'].copy()
            df['Level'] = df['Level'].map(state['level_names'])
            df = optimize_table_display(df)
            st.dataframe(df, height=600, use_container_width=True)

        with tab2:
            max_lvl = state['hierarchy']['hierarchy_table']['Level'].max()
            level_tabs = st.tabs([state['level_names'].get(i, f"Level {i}") for i in range(1, max_lvl + 1)])
            for i, level in enumerate(range(1, max_lvl + 1)):
                with level_tabs[i]:
                    lvl_name = state['level_names'][level]
                    lvl_df = state['hierarchy']['hierarchy_table'].query("Level == @level")
                    if not lvl_df.empty:
                        st.subheader(f"{lvl_name} Units")
                        export_df = generate_level_export(lvl_df, lvl_name)
                        st.dataframe(export_df, height=300, use_container_width=True)

                        col1, col2 = st.columns(2)
                        with col1:
                            st.download_button("Download CSV", export_df.to_csv(index=False).encode('utf-8'),
                                               file_name=f"{lvl_name.replace(' ', '_')}_units.csv", mime="text/csv")
                        with col2:
                            output = BytesIO()
                            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                                export_df.to_excel(writer, index=False)
                            st.download_button("Download Excel", output.getvalue(),
                                               file_name=f"{lvl_name.replace(' ', '_')}_units.xlsx",
                                               mime="application/vnd.ms-excel")

                        if level > 1:
                            st.divider()
                            parent_level = level - 1
                            parent_name = state['level_names'].get(parent_level, f"Level {parent_level}")
                            parent_df = state['hierarchy']['hierarchy_table'].query("Level == @parent_level")
                            assoc_df = generate_association_file(
                                lvl_df, parent_df, state['hrp1001'], lvl_name, parent_name
                            )

                            if not assoc_df.empty:
                                st.subheader(f"{lvl_name} → {parent_name} Associations")
                                st.dataframe(assoc_df, height=300, use_container_width=True)

                                col1, col2 = st.columns(2)
                                with col1:
                                    st.download_button("Download CSV", assoc_df.to_csv(index=False).encode('utf-8'),
                                                       file_name=f"{lvl_name}_to_{parent_name}_associations.csv",
                                                       mime="text/csv")
                                with col2:
                                    output = BytesIO()
                                    with pd.ExcelWriter(output, engine='openpyxl') as writer:
                                        assoc_df.to_excel(writer, index=False)
                                    st.download_button("Download Excel", output.getvalue(),
                                                       file_name=f"{lvl_name}_to_{parent_name}_associations.xlsx",
                                                       mime="application/vnd.ms-excel")
                            else:
                                st.warning(f"No valid associations between {lvl_name} and {parent_name}")
