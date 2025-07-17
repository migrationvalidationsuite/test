import streamlit as st
import pandas as pd
import json
import os
import sys
from datetime import datetime

# Fix sys.path for local dev (not needed in Streamlit Cloud if modules are structured)
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# ✅ FIXED IMPORTS
from foundation_module.utils.file_utils import create_download_button
from foundation_module.panels.transformation_logger import TransformationLogger


class TransformationLogger:
    def __init__(self):
        self.log_dir = "transformation_logs"
        os.makedirs(self.log_dir, exist_ok=True)
        self.session_log = []
        self.rollback_stack = []
    
    def add_entry(self, operation, details, before_snapshot, after_snapshot):
        timestamp = datetime.now().isoformat()
        log_entry = {
            "timestamp": timestamp,
            "operation": operation,
            "details": details,
            "before": before_snapshot.to_dict(orient='records') if isinstance(before_snapshot, pd.DataFrame) else None,
            "after": after_snapshot.to_dict(orient='records') if isinstance(after_snapshot, pd.DataFrame) else None
        }
        
        self.session_log.append(log_entry)
        self.rollback_stack.append({
            'operation': operation,
            'snapshot': before_snapshot.copy()
        })
        
        today = datetime.now().strftime("%Y-%m-%d")
        log_file = os.path.join(self.log_dir, f"transforms_{today}.json")
        
        try:
            existing_logs = []
            if os.path.exists(log_file):
                with open(log_file, 'r') as f:
                    existing_logs = json.load(f)
            
            existing_logs.append(log_entry)
            
            with open(log_file, 'w') as f:
                json.dump(existing_logs, f, indent=2)
        except Exception as e:
            st.error(f"Could not save log: {str(e)}")

    def get_rollback_options(self):
        return [entry['operation'] for entry in self.rollback_stack]
    
    def rollback_to(self, operation_name):
        for i, entry in enumerate(reversed(self.rollback_stack)):
            if entry['operation'] == operation_name:
                return self.rollback_stack.pop(len(self.rollback_stack)-1-i)['snapshot']
        return None

    def get_session_log(self):
        return self.session_log
    
    def get_full_history(self):
        all_logs = []
        if os.path.exists(self.log_dir):
            for filename in os.listdir(self.log_dir):
                if filename.startswith("transforms_") and filename.endswith(".json"):
                    try:
                        with open(os.path.join(self.log_dir, filename), 'r') as f:
                            all_logs.extend(json.load(f))
                    except:
                        continue
        return sorted(all_logs, key=lambda x: x['timestamp'], reverse=True)

def show_transformation_panel(state):
    st.header("Data Transformation Center")
    
    # Initialize session state components
    if 'transformation_log' not in state:
        state['transformation_log'] = TransformationLogger()
    if 'pending_transforms' not in state:
        state['pending_transforms'] = []
    
    # Check if data is loaded
    if state.get('hrp1000') is None:
        st.warning("Please load and build the hierarchy first")
        return
    
    # Before/After comparison
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Current Data (First 10 Rows)")
        st.dataframe(
            state['hrp1000'].head(10),
            use_container_width=True,
            height=400
        )
    
    # Transformation selection
    transform_type = st.selectbox(
        "Select Transformation Type",
        ["Clean Text", "Standardize Dates", "Remove Test Data", "Custom Transformation"],
        index=0
    )
    
    # Transformation parameters
    if transform_type == "Clean Text":
        cols_to_clean = st.multiselect(
            "Select columns to clean",
            options=state['hrp1000'].columns,
            default=["Name"]
        )
        operation = f"Clean text in columns: {', '.join(cols_to_clean)}"
        
    elif transform_type == "Standardize Dates":
        date_cols = st.multiselect(
            "Select date columns",
            options=[col for col in state['hrp1000'].columns if 'date' in col.lower() or 'Date' in col]
        )
        operation = f"Standardize dates in columns: {', '.join(date_cols)}"
        
    elif transform_type == "Remove Test Data":
        test_keywords = st.text_input(
            "Keywords indicating test data (comma separated)",
            value="test, temp, dummy"
        )
        operation = f"Remove rows containing: {test_keywords}"
        
    elif transform_type == "Custom Transformation":
        operation = "Custom transformation"
        custom_code = st.text_area(
            "Enter your pandas transformation code",
            height=200,
            value="""# Example: Create new column combining two fields
df1000['New_Column'] = df1000['Client'].astype(str) + '_' + df1000['Object ID'].astype(str)

# Available variables:
# - df1000: HRP1000 DataFrame (modify this)
# - df1001: HRP1001 DataFrame (read-only)
# - pd: pandas library"""
        )
    
    # Preview and apply
    if st.button("Preview Transformation"):
        try:
            preview_df = state['hrp1000'].copy()
            
            if transform_type == "Clean Text":
                for col in cols_to_clean:
                    preview_df[col] = preview_df[col].astype(str).str.strip().str.title()
                    
            elif transform_type == "Standardize Dates":
                for col in date_cols:
                    preview_df[col] = pd.to_datetime(..., format='%d.%m.%Y', errors='coerce')
                    
            elif transform_type == "Remove Test Data":
                keywords = [k.strip().lower() for k in test_keywords.split(",")]
                mask = preview_df.astype(str).apply(
                    lambda x: x.str.lower().str.contains('|'.join(keywords))
                ).any(axis=1)
                preview_df = preview_df[~mask]
                
            elif transform_type == "Custom Transformation":
                local_vars = {'df1000': preview_df, 'df1001': state.get('hrp1001'), 'pd': pd}
                exec(custom_code, globals(), local_vars)
                preview_df = local_vars['df1000']
            
            with col2:
                st.subheader("Transformed Preview (First 10 Rows)")
                st.dataframe(preview_df.head(10), use_container_width=True, height=400)
            
            state['pending_transforms'].append({
                'type': transform_type,
                'operation': operation,
                'preview': preview_df,
                'code': custom_code if transform_type == "Custom Transformation" else None
            })
            st.success("Transformation preview generated!")
            
        except Exception as e:
            st.error(f"Transformation error: {str(e)}")
    
    # Transformation queue
    if state['pending_transforms']:
        st.divider()
        st.subheader("Pending Transformations")
        
        for i, transform in enumerate(state['pending_transforms']):
            cols = st.columns([1, 8, 1])
            with cols[0]:
                st.checkbox("Apply", value=True, key=f"transform_{i}_active", label_visibility="collapsed")
            with cols[1]:
                st.write(f"**{transform['type']}**: {transform['operation']}")
                if transform['code']:
                    st.code(transform['code'], language='python')
            with cols[2]:
                if st.button("❌", key=f"remove_{i}"):
                    state['pending_transforms'].pop(i)
                    st.rerun()
        
        if st.button("✅ Apply All Transformations", type="primary"):
            for transform in state['pending_transforms']:
                try:
                    before = state['hrp1000'].copy()
                    
                    if transform['type'] == "Clean Text":
                        cols = transform['operation'].split(": ")[1].split(", ")
                        for col in cols:
                            state['hrp1000'][col] = state['hrp1000'][col].astype(str).str.strip().str.title()
                            
                    elif transform['type'] == "Standardize Dates":
                        cols = transform['operation'].split(": ")[1].split(", ")
                        for col in cols:
                            state['hrp1000'][col] = pd.to_datetime(state['hrp1000'][col], format='%d/%m/%Y', errors='coerce')
                            
                    elif transform['type'] == "Remove Test Data":
                        keywords = transform['operation'].split(": ")[1].split(", ")
                        mask = state['hrp1000'].astype(str).apply(
                            lambda x: x.str.lower().str.contains('|'.join(keywords))
                        ).any(axis=1)
                        state['hrp1000'] = state['hrp1000'][~mask]
                        
                    elif transform['type'] == "Custom Transformation":
                        local_vars = {'df1000': state['hrp1000'], 'df1001': state.get('hrp1001'), 'pd': pd}
                        exec(transform['code'], globals(), local_vars)
                        state['hrp1000'] = local_vars['df1000']
                    
                    state['transformation_log'].add_entry(
                        operation=transform['operation'],
                        details={
                            'type': transform['type'],
                            'rows_affected': len(state['hrp1000'])
                        },
                        before_snapshot=before,
                        after_snapshot=state['hrp1000'].copy()
                    )
                    
                except Exception as e:
                    st.error(f"Failed to apply {transform['type']}: {str(e)}")
            
            state['pending_transforms'] = []
            st.success("All transformations applied successfully!")
            st.rerun()
    
    # Transformation history and rollback
    st.divider()
    history_tab1, history_tab2, rollback_tab = st.tabs(["Session History", "Full Audit Log", "Rollback"])
    
    with history_tab1:
        session_history = state['transformation_log'].get_session_log()
        if not session_history:
            st.info("No transformations in current session")
        else:
            st.subheader("Current Session Transformations")
            for entry in reversed(session_history):
                with st.expander(f"{entry['timestamp']} - {entry['operation']}"):
                    st.json(entry, expanded=False)
    
    with history_tab2:
        full_history = state['transformation_log'].get_full_history()
        if not full_history:
            st.info("No historical transformations found")
        else:
            st.subheader("Complete Transformation History")
            for entry in full_history[:50]:  # Limit to 50 most recent
                with st.expander(f"{entry['timestamp']} - {entry['operation']}"):
                    st.json(entry, expanded=False)
    
    with rollback_tab:
        st.subheader("Rollback Transformations")
        if not state['transformation_log'].rollback_stack:
            st.info("No transformations available for rollback")
        else:
            rollback_options = state['transformation_log'].get_rollback_options()
            selected_rollback = st.selectbox(
                "Select transformation to rollback",
                options=rollback_options,
                index=0
            )
            
            if st.button("⏮️ Rollback Selected Transformation"):
                rolled_back_df = state['transformation_log'].rollback_to(selected_rollback)
                if rolled_back_df is not None:
                    state['hrp1000'] = rolled_back_df
                    st.success(f"Successfully rolled back: {selected_rollback}")
                    st.rerun()
                else:
                    st.error("Failed to rollback transformation")
