import os
import json
import pandas as pd
from datetime import datetime
import streamlit as st

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

