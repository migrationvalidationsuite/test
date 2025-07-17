# app/utils/transformations.py

import pandas as pd
import numpy as np

def apply_transformations(mapping_df, source_data, date_format, picklists=None):
    transformed_data = []
    logs = []

    header_row_1 = mapping_df['TargetColumn1'].fillna("")
    header_row_2 = mapping_df['Target column 2'].fillna("")

    # Two header rows
    header_rows = pd.DataFrame([header_row_1.values, header_row_2.values], columns=header_row_1.values)

    for idx, row in mapping_df.iterrows():
        target_col = row['TargetColumn1']
        source_table = row['SourceTable']
        source_col = row['SourceColumn']
        transformation = str(row.get('Transformation', '')).strip()
        default_value = row.get('DefaultValue', "")
        picklist_source = row.get('PicklistSource', "")

        series = pd.Series([default_value] * max(len(df) for df in source_data.values()))

        try:
            if source_table and source_col:
                if source_table in source_data and source_col in source_data[source_table].columns:
                    series = source_data[source_table][source_col]
                else:
                    logs.append((target_col, "Missing", f"{source_table}.{source_col} not found"))
                    transformed_data.append(series.rename(target_col))
                    continue

            if transformation.startswith("Type="):
                key = transformation.split("=")[1]
                df = source_data[source_table]
                series = df[df['Type'] == key][source_col].reset_index(drop=True)

            if picklist_source and picklists and picklist_source.replace(".xlsx", "") in picklists:
                pl_df = picklists[picklist_source.replace(".xlsx", "")]
                if not pl_df.empty:
                    series = series.map(lambda val: pl_df.get(val, val))

            logs.append((target_col, "Success", "Transformed"))
        except Exception as e:
            logs.append((target_col, "Error", str(e)))

        transformed_data.append(series.rename(target_col))

    final_df = pd.concat(transformed_data, axis=1)
    return final_df, header_rows, logs
