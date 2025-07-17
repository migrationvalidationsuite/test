import streamlit as st
import pandas as pd
from io import BytesIO

def load_data(file):
    """Load HRP1000 or HRP1001 file with comprehensive error handling"""
    if file is None:
        raise ValueError("No file uploaded")
    
    try:
        if file.name.endswith('.csv'):
            return pd.read_csv(file)
        elif file.name.endswith(('.xlsx', '.xls')):
            return pd.read_excel(file)
        else:
            raise ValueError("Unsupported file format. Please upload CSV or Excel files.")
    except pd.errors.EmptyDataError:
        raise ValueError("The uploaded file is empty")
    except Exception as e:
        raise ValueError(f"Error loading file: {str(e)}")

def create_download_button(data, file_name, file_type):
    """Create a robust download button for DataFrames"""
    if not isinstance(data, pd.DataFrame):
        st.warning("Invalid data format - must be pandas DataFrame")
        return
    
    if data.empty:
        st.warning("No data available to download - DataFrame is empty")
        return
    
    try:
        if file_type.lower() == 'csv':
            csv = data.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="Download CSV",
                data=csv,
                file_name=f"{file_name}.csv",
                mime="text/csv",
                key=f"csv_{file_name}"
            )
        elif file_type.lower() == 'excel':
            output = BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                data.to_excel(writer, index=False)
            st.download_button(
                label="Download Excel",
                data=output.getvalue(),
                file_name=f"{file_name}.xlsx",
                mime="application/vnd.ms-excel",
                key=f"excel_{file_name}"
            )
        else:
            st.error("Invalid file type specified. Use 'csv' or 'excel'")
    except Exception as e:
        st.error(f"Failed to generate download: {str(e)}")