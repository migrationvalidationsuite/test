# app/utils/validation.py

import pandas as pd

def build_validation_panel(logs):
    df = pd.DataFrame(logs, columns=["TargetColumn", "Status", "Message"])
    icon_map = {"Success": "🟢", "Missing": "🟡", "Error": "🔴"}
    df["StatusIcon"] = df["Status"].map(icon_map)
    return df

def build_statistics_panel(dataframe, log_df):
    return pd.DataFrame({
        "Metric": ["Total Columns", "Total Records", "Success Columns", "Missing Columns", "Error Columns"],
        "Value": [
            len(dataframe.columns),
            len(dataframe),
            (log_df["Status"] == "Success").sum(),
            (log_df["Status"] == "Missing").sum(),
            (log_df["Status"] == "Error").sum()
        ]
    })
