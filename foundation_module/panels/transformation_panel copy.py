import streamlit as st
import pandas as pd

def show_transformation_panel(state):
    st.header("Data Transformation")
    
    if state['hrp1000'] is None or state['hrp1001'] is None:
        st.warning("Please load HRP1000 and HRP1001 files in the Hierarchy panel first.")
        return
    
    st.subheader("Original Data")
    
    tab1, tab2 = st.tabs(["HRP1000 Data", "HRP1001 Data"])
    
    with tab1:
        st.dataframe(state['hrp1000'])
    
    with tab2:
        st.dataframe(state['hrp1001'])
    
    st.subheader("Transformations")
    
    # Transformation options
    transformation = st.selectbox(
        "Select Transformation",
        [
            "Clean Object Names",
            "Standardize Dates",
            "Remove Test Data",
            "Custom Transformation"
        ]
    )
    
    if transformation == "Clean Object Names":
        st.write("This will clean object names by removing extra spaces and special characters.")
        if st.button("Apply Name Cleaning"):
            # Apply transformation
            state['hrp1000']['Name'] = state['hrp1000']['Name'].str.strip()
            state['transformations'].append("Cleaned object names")
            st.success("Transformation applied!")
    
    elif transformation == "Standardize Dates":
        st.write("This will standardize date formats across both files.")
        if st.button("Apply Date Standardization"):
            # Apply transformation
            for col in ['Start date', 'End Date', 'Changed on']:
                if col in state['hrp1000']:
                    state['hrp1000'][col] = pd.to_datetime(state['hrp1000'][col], errors='coerce')
                if col in state['hrp1001']:
                    state['hrp1001'][col] = pd.to_datetime(state['hrp1001'][col], errors='coerce')
            state['transformations'].append("Standardized date formats")
            st.success("Transformation applied!")
    
    elif transformation == "Remove Test Data":
        st.write("This will remove rows that appear to be test data.")
        if st.button("Apply Test Data Removal"):
            # Apply transformation
            state['hrp1000'] = state['hrp1000'][~state['hrp1000']['Name'].str.contains('TEST', case=False, na=False)]
            state['hrp1001'] = state['hrp1001'][~state['hrp1001']['Source ID'].astype(str).str.contains('9999')]
            state['transformations'].append("Removed test data")
            st.success("Transformation applied!")
    
    elif transformation == "Custom Transformation":
        custom_code = st.text_area("Enter custom transformation code (Python pandas)")
        if st.button("Apply Custom Transformation"):
            try:
                # Apply custom transformation
                exec(custom_code, {'df1000': state['hrp1000'], 'df1001': state['hrp1001']})
                state['transformations'].append("Applied custom transformation")
                st.success("Custom transformation applied successfully!")
            except Exception as e:
                st.error(f"Error applying transformation: {str(e)}")
    
    # Show applied transformations
    if state['transformations']:
        st.subheader("Applied Transformations")
        for i, trans in enumerate(state['transformations'], 1):
            st.write(f"{i}. {trans}")
        
        if st.button("Reset All Transformations"):
            state['transformations'] = []
            st.success("Transformations reset. Please reload original files from Hierarchy panel.")
    
    # Show transformed data preview
    if state['transformations']:
        st.subheader("Transformed Data Preview")
        
        tab1, tab2 = st.tabs(["Transformed HRP1000", "Transformed HRP1001"])
        
        with tab1:
            st.dataframe(state['hrp1000'].head())
        
        with tab2:
            st.dataframe(state['hrp1001'].head())