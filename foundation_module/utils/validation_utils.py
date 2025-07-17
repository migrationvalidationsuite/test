import pandas as pd

def validate_data(hrp1000, hrp1001):
    """Validate HRP1000 and HRP1001 data"""
    errors = []
    warnings = []
    
    # Check for required columns in HRP1000
    required_hrp1000 = ['Object ID', 'Name']
    for col in required_hrp1000:
        if col not in hrp1000.columns:
            errors.append({
                'Type': 'Error',
                'Message': f"Missing required column in HRP1000: {col}",
                'Severity': 'High'
            })
    
    # Check for required columns in HRP1001
    required_hrp1001 = ['Source ID', 'Target object ID']
    for col in required_hrp1001:
        if col not in hrp1001.columns:
            errors.append({
                'Type': 'Error',
                'Message': f"Missing required column in HRP1001: {col}",
                'Severity': 'High'
            })
    
    # Check for object IDs in HRP1001 that don't exist in HRP1000
    hrp1000_ids = set(hrp1000['Object ID'])
    source_ids = set(hrp1001['Source ID'])
    target_ids = set(hrp1001['Target object ID'])
    
    missing_sources = source_ids - hrp1000_ids
    missing_targets = target_ids - hrp1000_ids
    
    for obj_id in missing_sources:
        errors.append({
            'Type': 'Error',
            'Message': f"Source ID {obj_id} in HRP1001 not found in HRP1000",
            'Severity': 'High',
            'Object ID': obj_id
        })
    
    for obj_id in missing_targets:
        errors.append({
            'Type': 'Error',
            'Message': f"Target object ID {obj_id} in HRP1001 not found in HRP1000",
            'Severity': 'High',
            'Object ID': obj_id
        })
    
    # Check for date consistency (only if date columns exist)
    if 'Start date' in hrp1000.columns and 'End Date' in hrp1000.columns:
        try:
            hrp1000 = hrp1000.copy()
            hrp1000['Start date'] = pd.to_datetime(hrp1000['Start date'], errors='coerce')
            hrp1000['End Date'] = pd.to_datetime(hrp1000['End Date'], errors='coerce')
            
            invalid_dates = hrp1000[hrp1000['Start date'] > hrp1000['End Date']]
            for _, row in invalid_dates.iterrows():
                warnings.append({
                    'Type': 'Warning',
                    'Message': f"Object {row['Object ID']} has start date after end date",
                    'Severity': 'Medium',
                    'Object ID': row['Object ID']
                })
        except Exception as e:
            warnings.append({
                'Type': 'Warning',
                'Message': f"Date validation failed: {str(e)}",
                'Severity': 'Low'
            })
    
    if 'Start date' in hrp1001.columns and 'End Date' in hrp1001.columns:
        try:
            hrp1001 = hrp1001.copy()
            hrp1001['Start date'] = pd.to_datetime(hrp1001['Start date'], errors='coerce')
            hrp1001['End Date'] = pd.to_datetime(hrp1001['End Date'], errors='coerce')
            
            invalid_dates = hrp1001[hrp1001['Start date'] > hrp1001['End Date']]
            for _, row in invalid_dates.iterrows():
                warnings.append({
                    'Type': 'Warning',
                    'Message': f"Relationship for source {row['Source ID']} has start date after end date",
                    'Severity': 'Medium',
                    'Source ID': row['Source ID']
                })
        except Exception as e:
            warnings.append({
                'Type': 'Warning',
                'Message': f"Date validation failed: {str(e)}",
                'Severity': 'Low'
            })
    
    return {
        'errors': errors,
        'warnings': warnings,
        'error_count': len(errors),
        'warning_count': len(warnings)
    }