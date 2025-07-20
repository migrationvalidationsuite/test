import os
import pandas as pd
from datetime import datetime

# Directory paths
TRANSFORMED_DATA_DIR = "/mnt/data/saved_transformations"
AUDIT_LOG_FILE = "/mnt/data/transformation_audit_log.csv"

def ensure_directories_exist():
    """Create necessary directories if they don't exist."""
    os.makedirs(TRANSFORMED_DATA_DIR, exist_ok=True)

def load_uploaded_data(uploaded_file):
    """Load uploaded CSV or Excel file into a DataFrame."""
    if uploaded_file.name.endswith(".csv"):
        return pd.read_csv(uploaded_file)
    elif uploaded_file.name.endswith(".xlsx"):
        return pd.read_excel(uploaded_file)
    else:
        raise ValueError("Unsupported file format. Please upload a CSV or Excel file.")

def save_transformed_data(df, username="unknown_user", journal="", original_filename="data"):
    """Save transformed file with timestamp and return path."""
    ensure_directories()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{username}_{original_filename}_{timestamp}.csv"
    file_path = os.path.join(TRANSFORMED_DATA_DIR, filename)
    df.to_csv(file_path, index=False)
    return file_path

def append_audit_log(username, transformations, journal, file_path):
    """Append an audit log entry to the central CSV file."""
    ensure_directories()
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = {
        "timestamp": timestamp,
        "username": username,
        "file_path": file_path,
        "transformations_applied": transformations,
        "user_notes": journal
    }
    log_df = pd.DataFrame([log_entry])
    if os.path.exists(AUDIT_LOG_FILE):
        log_df.to_csv(AUDIT_LOG_FILE, mode='a', header=False, index=False)
    else:
        log_df.to_csv(AUDIT_LOG_FILE, mode='w', header=True, index=False)

def load_audit_log():
    """Load the audit log as a DataFrame (if exists)."""
    if os.path.exists(AUDIT_LOG_FILE):
        return pd.read_csv(AUDIT_LOG_FILE)
    return pd.DataFrame()
