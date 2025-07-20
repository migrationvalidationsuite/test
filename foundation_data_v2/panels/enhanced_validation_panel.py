import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import re
from typing import Dict, List, Tuple, Any
from collections import defaultdict
import json
from io import BytesIO

def is_dataframe_available(df):
    """Helper function to check if DataFrame is available and not empty"""
    if df is None:
        return False
    if isinstance(df, pd.DataFrame):
        return not df.empty
    return False

def safe_get_dataframe(state, key):
    """Safely get DataFrame from state"""
    try:
        df = state.get(key)
        if df is None:
            return None
        if isinstance(df, pd.DataFrame) and not df.empty:
            return df
        return None
    except Exception as e:
        st.error(f"Error accessing {key}: {str(e)}")
        return None

class EnhancedMigrationValidator:
    """Enhanced validator that includes source files, generated output files, and hierarchy calculations"""
    
    def __init__(self):
        self.errors = []
        self.warnings = []
        self.error_counts = defaultdict(int)
    
    def validate_complete_pipeline(self, state) -> Dict:
        """Comprehensive validation of entire pipeline: source → processing → output"""
        
        self.errors = []
        self.warnings = []
        self.error_counts = defaultdict(int)
        
        # Get all data
        hrp1000_df = safe_get_dataframe(state, 'source_hrp1000')
        hrp1001_df = safe_get_dataframe(state, 'source_hrp1001')
        hierarchy_structure = state.get('hierarchy_structure', {})
        generated_files = state.get('generated_output_files', {})
        
        validation_results = {
            'timestamp': datetime.now().isoformat(),
            'source_files_validated': False,
            'hierarchy_calculations_validated': False,
            'output_files_validated': False,
            'pipeline_complete': False
        }
        
        # 1. Validate source files (complete validation from clean version)
        if hrp1000_df is not None and hrp1001_df is not None:
            self._validate_source_files(hrp1000_df, hrp1001_df)
            validation_results['source_files_validated'] = True
        
        # 2. Validate hierarchy calculations (complete validation from clean version)
        if hierarchy_structure:
            self._validate_hierarchy_calculations(hrp1000_df, hrp1001_df, hierarchy_structure)
            validation_results['hierarchy_calculations_validated'] = True
        
        # 3. Validate generated output files (complete validation from clean version)
        if generated_files:
            self._validate_output_files(generated_files, hrp1000_df, hrp1001_df, hierarchy_structure)
            validation_results['output_files_validated'] = True
        
        # 4. Validate end-to-end pipeline integrity (complete validation from clean version)
        if all([hrp1000_df is not None, hrp1001_df is not None, hierarchy_structure, generated_files]):
            self._validate_pipeline_integrity(hrp1000_df, hrp1001_df, hierarchy_structure, generated_files)
            validation_results['pipeline_complete'] = True
        
        # Categorize and finalize results
        categorized_errors = self._categorize_errors()
        
        validation_results.update({
            'total_errors': len(self.errors),
            'total_warnings': len(self.warnings),
            'error_summary': dict(self.error_counts),
            'categorized_errors': categorized_errors,
            'all_errors': self.errors,
            'all_warnings': self.warnings,
            'migration_ready': len(self.errors) == 0,
            'critical_blockers': [e for e in self.errors if e['severity'] == 'CRITICAL']
        })
        
        return validation_results
    
    def _validate_source_files(self, hrp1000_df: pd.DataFrame, hrp1001_df: pd.DataFrame):
        """Validate source files with enhanced drill-down details"""
        
        # Enhanced required fields validation with specific row details
        self._validate_required_fields_enhanced(hrp1000_df, hrp1001_df)
        self._validate_data_formats_enhanced(hrp1000_df, hrp1001_df)
        self._validate_referential_integrity_enhanced(hrp1000_df, hrp1001_df)
        self._validate_business_rules_enhanced(hrp1000_df, hrp1001_df)
    
    def _validate_required_fields_enhanced(self, hrp1000_df: pd.DataFrame, hrp1001_df: pd.DataFrame):
        """Enhanced required fields validation with specific details"""
        
        # HRP1000 required fields
        hrp1000_required = {
            'Object ID': 'Organizational unit identifier',
            'Name': 'Unit name',
            'Planning status': 'Active/Inactive status'
        }
        
        for field, description in hrp1000_required.items():
            if field not in hrp1000_df.columns:
                self._add_error(
                    'MISSING_REQUIRED_FIELD',
                    'CRITICAL',
                    f"Missing required field: {field}",
                    f"Field '{field}' ({description}) is required for HRP1000 migration",
                    f"Add column '{field}' to your HRP1000 data",
                    'HRP1000',
                    field
                )
            else:
                # Check for null values with specific row details
                null_mask = hrp1000_df[field].isnull()
                if null_mask.any():
                    null_rows = hrp1000_df[null_mask].index.tolist()
                    null_details = []
                    for row_idx in null_rows[:10]:  # Show first 10
                        other_data = {}
                        for col in ['Object ID', 'Name']:
                            if col in hrp1000_df.columns and col != field:
                                other_data[col] = hrp1000_df.iloc[row_idx][col]
                        null_details.append({
                            'row': row_idx + 2,  # +2 for Excel row (1-indexed + header)
                            'other_data': other_data
                        })
                    
                    self._add_error(
                        'NULL_REQUIRED_FIELD',
                        'CRITICAL',
                        f"Null values in required field: {field}",
                        f"Found {len(null_rows)} null values in required field '{field}'",
                        f"Fill missing values in Excel rows: {[d['row'] for d in null_details[:5]]}",
                        'HRP1000',
                        field,
                        {
                            'affected_rows_count': len(null_rows),
                            'null_details': null_details,
                            'excel_fix_suggestion': f"In Excel, filter column '{field}' for empty cells and fill with appropriate values"
                        }
                    )
        
        # Similar enhanced validation for HRP1001
        hrp1001_required = {
            'Source ID': 'Child unit identifier',
            'Target object ID': 'Parent unit identifier',
            'Relationship': 'Relationship type'
        }
        
        for field, description in hrp1001_required.items():
            if field not in hrp1001_df.columns:
                self._add_error(
                    'MISSING_REQUIRED_FIELD',
                    'CRITICAL',
                    f"Missing required field: {field}",
                    f"Field '{field}' ({description}) is required for HRP1001 migration",
                    f"Add column '{field}' to your HRP1001 data",
                    'HRP1001',
                    field
                )
            else:
                null_mask = hrp1001_df[field].isnull()
                if null_mask.any():
                    null_rows = hrp1001_df[null_mask].index.tolist()
                    null_details = []
                    for row_idx in null_rows[:10]:
                        other_data = {}
                        for col in ['Source ID', 'Target object ID']:
                            if col in hrp1001_df.columns and col != field:
                                other_data[col] = hrp1001_df.iloc[row_idx][col]
                        null_details.append({
                            'row': row_idx + 2,
                            'other_data': other_data
                        })
                    
                    self._add_error(
                        'NULL_REQUIRED_FIELD',
                        'CRITICAL',
                        f"Null values in required field: {field}",
                        f"Found {len(null_rows)} null values in required field '{field}'",
                        f"Fill missing values in Excel rows: {[d['row'] for d in null_details[:5]]}",
                        'HRP1001',
                        field,
                        {
                            'affected_rows_count': len(null_rows),
                            'null_details': null_details,
                            'excel_fix_suggestion': f"In Excel, filter column '{field}' for empty cells and fill with appropriate values"
                        }
                    )

    def _validate_data_formats_enhanced(self, hrp1000_df: pd.DataFrame, hrp1001_df: pd.DataFrame):
        """Enhanced data formats validation with specific examples"""
        
        # Object ID format validation (should be 8 digits)
        if 'Object ID' in hrp1000_df.columns:
            invalid_ids = []
            for idx, obj_id in hrp1000_df['Object ID'].items():
                if pd.notna(obj_id):
                    obj_id_str = str(obj_id).strip()
                    if not re.match(r'^\d{8}$', obj_id_str):
                        invalid_ids.append({
                            'excel_row': idx + 2,
                            'current_value': obj_id_str,
                            'expected_format': '8 digits (e.g., 12345678)',
                            'suggested_fix': obj_id_str.zfill(8) if obj_id_str.isdigit() else f"Fix manually: '{obj_id_str}'"
                        })
            
            if invalid_ids:
                self._add_error(
                    'INVALID_ID_FORMAT',
                    'HIGH',
                    f"Invalid Object ID format",
                    f"Found {len(invalid_ids)} Object IDs that don't match required 8-digit format",
                    "Object IDs must be exactly 8 digits (e.g., 12345678). Pad with leading zeros or fix invalid characters.",
                    'HRP1000',
                    'Object ID',
                    {
                        'invalid_ids': invalid_ids[:15],
                        'total_invalid': len(invalid_ids),
                        'excel_fix_formula': "Use Excel formula: =RIGHT(\"00000000\"&A2,8) to pad with zeros",
                        'common_issues': self._analyze_id_format_issues(invalid_ids)
                    }
                )
        
        # Date format validation
        date_columns = ['Start date', 'End Date', 'End date']
        for df_name, df in [('HRP1000', hrp1000_df), ('HRP1001', hrp1001_df)]:
            for col in date_columns:
                if col in df.columns:
                    invalid_dates = []
                    for idx, date_val in df[col].items():
                        if pd.notna(date_val) and str(date_val).strip():
                            date_str = str(date_val).strip()
                            if not self._is_valid_date_format(date_str):
                                invalid_dates.append({
                                    'excel_row': idx + 2,
                                    'current_value': date_str,
                                    'suggested_format': 'dd.mm.yyyy (e.g., 01.01.2024)',
                                    'issue': self._diagnose_date_issue(date_str)
                                })
                    
                    if invalid_dates:
                        self._add_error(
                            'INVALID_DATE_FORMAT',
                            'MEDIUM',
                            f"Invalid date format in {col}",
                            f"Found {len(invalid_dates)} invalid date formats in {col}",
                            "Use format dd.mm.yyyy (e.g., 01.01.2024) or yyyy-mm-dd. Fix invalid date values.",
                            df_name,
                            col,
                            {
                                'invalid_dates': invalid_dates[:15],
                                'total_invalid': len(invalid_dates),
                                'excel_fix_steps': [
                                    "1. Select the date column",
                                    "2. Use Format Cells → Date → dd.mm.yyyy",
                                    "3. For text dates, use formula: =DATEVALUE(A2)",
                                    "4. Check for typos in day/month/year values"
                                ]
                            }
                        )
        
        # Planning status validation
        valid_statuses = ['1', '2', '3', '0', 1, 2, 3, 0]
        for df_name, df in [('HRP1000', hrp1000_df), ('HRP1001', hrp1001_df)]:
            if 'Planning status' in df.columns:
                invalid_statuses = []
                for idx, status in df['Planning status'].items():
                    if pd.notna(status) and status not in valid_statuses:
                        invalid_statuses.append({
                            'excel_row': idx + 2,
                            'current_value': str(status),
                            'valid_options': '1=Active, 2=Inactive, 3=Planned, 0=Deleted',
                            'suggested_fix': self._suggest_status_fix(status)
                        })
                
                if invalid_statuses:
                    self._add_error(
                        'INVALID_STATUS_CODE',
                        'HIGH',
                        f"Invalid planning status codes",
                        f"Found {len(invalid_statuses)} invalid status codes in {df_name}",
                        "Valid statuses: 1=Active, 2=Inactive, 3=Planned, 0=Deleted. Update invalid status codes.",
                        df_name,
                        'Planning status',
                        {
                            'invalid_statuses': invalid_statuses[:15],
                            'total_invalid': len(invalid_statuses),
                            'replacement_guide': {
                                'Active': '1',
                                'Inactive': '2', 
                                'Planned': '3',
                                'Deleted': '0',
                                'A': '1',
                                'I': '2',
                                'P': '3',
                                'D': '0'
                            }
                        }
                    )
    
    def _analyze_id_format_issues(self, invalid_ids):
        """Analyze common Object ID format issues"""
        issues = defaultdict(int)
        for invalid in invalid_ids:
            value = invalid['current_value']
            if not value.isdigit():
                issues['Contains non-digit characters'] += 1
            elif len(value) < 8:
                issues['Too short (needs padding)'] += 1
            elif len(value) > 8:
                issues['Too long (needs truncation)'] += 1
            else:
                issues['Other format issue'] += 1
        return dict(issues)
    
    def _diagnose_date_issue(self, date_str):
        """Diagnose specific date format issues"""
        if '/' in date_str:
            return "Uses '/' instead of '.'"
        elif '-' in date_str and len(date_str.split('-')[0]) == 4:
            return "YYYY-MM-DD format (needs conversion to DD.MM.YYYY)"
        elif len(date_str.replace('.', '').replace('/', '').replace('-', '')) != 8:
            return "Incomplete date (missing day, month, or year)"
        elif any(char.isalpha() for char in date_str):
            return "Contains text (remove words like 'Jan', 'Feb')"
        else:
            return "Unknown date format issue"
    
    def _suggest_status_fix(self, status):
        """Suggest fix for invalid status codes"""
        status_str = str(status).upper().strip()
        mapping = {
            'ACTIVE': '1',
            'INACTIVE': '2',
            'PLANNED': '3', 
            'DELETED': '0',
            'A': '1',
            'I': '2',
            'P': '3',
            'D': '0',
            'YES': '1',
            'NO': '2',
            'TRUE': '1',
            'FALSE': '2'
        }
        return mapping.get(status_str, 'Replace with 1 (Active) or 2 (Inactive)')
    
    def _is_valid_date_format(self, date_str: str) -> bool:
        """Check if date string is in valid format"""
        date_patterns = [
            r'\d{2}\.\d{2}\.\d{4}',  # dd.mm.yyyy
            r'\d{4}-\d{2}-\d{2}',    # yyyy-mm-dd
            r'\d{2}/\d{2}/\d{4}',    # mm/dd/yyyy
            r'\d{4}/\d{2}/\d{2}'     # yyyy/mm/dd
        ]
        
        return any(re.match(pattern, date_str.strip()) for pattern in date_patterns)

    def _validate_referential_integrity_enhanced(self, hrp1000_df: pd.DataFrame, hrp1001_df: pd.DataFrame):
        """Enhanced referential integrity validation with specific problematic IDs"""
        
        if 'Object ID' not in hrp1000_df.columns or 'Source ID' not in hrp1001_df.columns or 'Target object ID' not in hrp1001_df.columns:
            return
        
        # Get all valid unit IDs
        valid_unit_ids = set(hrp1000_df['Object ID'].astype(str))
        
        # Check Target IDs exist in HRP1000 (enhanced with specific details)
        orphaned_targets = []
        for idx, target_id in hrp1001_df['Target object ID'].items():
            if pd.notna(target_id) and str(target_id) not in valid_unit_ids:
                # Get additional context for this orphaned target
                source_id = hrp1001_df.iloc[idx].get('Source ID', 'N/A')
                relationship = hrp1001_df.iloc[idx].get('Relationship', 'N/A')
                orphaned_targets.append({
                    'excel_row': idx + 2,  # Excel row number
                    'target_id': str(target_id),
                    'source_id': str(source_id),
                    'relationship': str(relationship),
                    'issue': f"Target ID '{target_id}' does not exist in HRP1000"
                })
        
        if orphaned_targets:
            # Group by target ID for better analysis
            target_groups = defaultdict(list)
            for orphan in orphaned_targets:
                target_groups[orphan['target_id']].append(orphan)
            
            self._add_error(
                'ORPHANED_TARGET_ID',
                'CRITICAL',
                f"Orphaned Target IDs",
                f"Found {len(orphaned_targets)} Target IDs that don't exist in HRP1000",
                "Option 1: Create missing organizational units in HRP1000, OR Option 2: Remove invalid relationships from HRP1001",
                'HRP1001',
                'Target object ID',
                {
                    'orphaned_targets': orphaned_targets[:15],  # Show first 15
                    'unique_missing_targets': list(target_groups.keys())[:10],
                    'total_orphaned_relationships': len(orphaned_targets),
                    'excel_fix_steps': [
                        "1. In HRP1001, sort by 'Target object ID' column",
                        "2. Look for Target IDs that appear in the orphaned list below",
                        "3. Either create these units in HRP1000 or delete these rows from HRP1001",
                        f"4. Most common missing Target ID: '{max(target_groups.keys(), key=lambda x: len(target_groups[x]))}'(appears {len(target_groups[max(target_groups.keys(), key=lambda x: len(target_groups[x]))])} times)"
                    ]
                }
            )
        
        # Check Source IDs exist in HRP1000 (enhanced)
        orphaned_sources = []
        for idx, source_id in hrp1001_df['Source ID'].items():
            if pd.notna(source_id) and str(source_id) not in valid_unit_ids:
                target_id = hrp1001_df.iloc[idx].get('Target object ID', 'N/A')
                relationship = hrp1001_df.iloc[idx].get('Relationship', 'N/A')
                orphaned_sources.append({
                    'excel_row': idx + 2,
                    'source_id': str(source_id),
                    'target_id': str(target_id),
                    'relationship': str(relationship),
                    'issue': f"Source ID '{source_id}' does not exist in HRP1000"
                })
        
        if orphaned_sources:
            self._add_error(
                'ORPHANED_SOURCE_ID',
                'CRITICAL',
                f"Orphaned Source IDs",
                f"Found {len(orphaned_sources)} Source IDs that don't exist in HRP1000",
                "Create corresponding organizational units in HRP1000 or remove invalid relationships from HRP1001",
                'HRP1001',
                'Source ID',
                {
                    'orphaned_sources': orphaned_sources[:15],
                    'total_orphaned_relationships': len(orphaned_sources)
                }
            )
    
    def _validate_business_rules_enhanced(self, hrp1000_df: pd.DataFrame, hrp1001_df: pd.DataFrame):
        """Enhanced business rules validation with specific duplicate details"""
        
        # Check for duplicate Object IDs with specific details
        if 'Object ID' in hrp1000_df.columns:
            # Find duplicates with all their details
            duplicate_mask = hrp1000_df['Object ID'].duplicated(keep=False)
            if duplicate_mask.any():
                duplicates_df = hrp1000_df[duplicate_mask].copy()
                duplicate_groups = {}
                
                for obj_id in duplicates_df['Object ID'].unique():
                    duplicate_rows = duplicates_df[duplicates_df['Object ID'] == obj_id]
                    duplicate_details = []
                    for idx, row in duplicate_rows.iterrows():
                        detail = {
                            'excel_row': idx + 2,
                            'object_id': str(row['Object ID']),
                            'name': str(row.get('Name', 'N/A')),
                            'status': str(row.get('Planning status', 'N/A')),
                            'other_fields': {col: str(row[col]) for col in row.index if col not in ['Object ID', 'Name', 'Planning status']}
                        }
                        duplicate_details.append(detail)
                    duplicate_groups[str(obj_id)] = duplicate_details
                
                # Get the most problematic duplicate for the main message
                most_common_duplicate = max(duplicate_groups.keys(), key=lambda x: len(duplicate_groups[x]))
                
                self._add_error(
                    'DUPLICATE_OBJECT_ID',
                    'CRITICAL',
                    f"Duplicate Object IDs",
                    f"Found {len(duplicate_groups)} Object IDs with duplicates (affecting {len(duplicates_df)} rows)",
                    f"Each organizational unit must have a unique Object ID. Review duplicates and merge or remove entries.",
                    'HRP1000',
                    'Object ID',
                    {
                        'duplicate_groups': duplicate_groups,
                        'most_common_duplicate': most_common_duplicate,
                        'total_duplicate_rows': len(duplicates_df),
                        'excel_fix_steps': [
                            "1. In HRP1000, sort by 'Object ID' column",
                            "2. Look for consecutive rows with the same Object ID",
                            "3. Keep the most complete/recent entry and delete others",
                            "4. Or modify Object IDs to make them unique (e.g., add suffix)"
                        ]
                    }
                )
    
    def _validate_hierarchy_calculations(self, hrp1000_df: pd.DataFrame, hrp1001_df: pd.DataFrame, hierarchy_structure: Dict):
        """Validate that hierarchy level calculations are correct"""
        
        if not hierarchy_structure:
            return
        
        # Rebuild hierarchy from scratch to compare with stored hierarchy
        calculated_hierarchy = self._calculate_hierarchy_from_scratch(hrp1000_df, hrp1001_df)
        
        # Compare stored vs calculated hierarchy
        discrepancies = []
        for unit_id, stored_info in hierarchy_structure.items():
            if unit_id in calculated_hierarchy:
                calc_info = calculated_hierarchy[unit_id]
                if stored_info.get('level') != calc_info.get('level'):
                    discrepancies.append({
                        'unit_id': unit_id,
                        'unit_name': stored_info.get('name', 'Unknown'),
                        'stored_level': stored_info.get('level'),
                        'calculated_level': calc_info.get('level'),
                        'issue': 'Level mismatch between stored and calculated values'
                    })
        
        if discrepancies:
            self._add_error(
                'HIERARCHY_CALCULATION_ERROR',
                'HIGH',
                f"Hierarchy level calculation errors",
                f"Found {len(discrepancies)} units with incorrect level calculations",
                "Recalculate hierarchy structure in the Hierarchy panel",
                'Hierarchy Processing',
                'Level Calculation',
                {
                    'discrepancies': discrepancies[:10],
                    'total_discrepancies': len(discrepancies),
                    'fix_suggestion': "Go to Hierarchy panel and click 'Process Hierarchy' to recalculate levels"
                }
            )
        
        # Check for circular references in hierarchy
        circular_refs = self._detect_circular_references(hierarchy_structure)
        if circular_refs:
            self._add_error(
                'CIRCULAR_HIERARCHY_REFERENCE',
                'CRITICAL',
                f"Circular references in hierarchy",
                f"Found {len(circular_refs)} circular reference chains",
                "Fix circular reporting relationships in source data",
                'Hierarchy Structure',
                'Parent-Child Relationships',
                {
                    'circular_chains': circular_refs[:5],
                    'total_circular_refs': len(circular_refs)
                }
            )
        
        # Validate hierarchy depth and breadth
        self._validate_hierarchy_structure_quality(hierarchy_structure)
    
    def _validate_output_files(self, generated_files: Dict, hrp1000_df: pd.DataFrame, hrp1001_df: pd.DataFrame, hierarchy_structure: Dict):
        """Validate generated level and association files"""
        
        level_files = generated_files.get('level_files', {})
        association_files = generated_files.get('association_files', {})
        
        # Validate level files
        for level_num, file_info in level_files.items():
            if 'data' in file_info:
                self._validate_level_file(level_num, file_info['data'], hrp1000_df, hierarchy_structure)
        
        # Validate association files
        for level_num, file_info in association_files.items():
            if 'data' in file_info:
                self._validate_association_file(level_num, file_info['data'], hrp1001_df, hierarchy_structure)
        
        # Validate completeness of generated files
        expected_levels = max([info.get('level', 1) for info in hierarchy_structure.values()]) if hierarchy_structure else 1
        
        missing_level_files = []
        for level in range(1, expected_levels + 1):
            if level not in level_files:
                missing_level_files.append(level)
        
        if missing_level_files:
            self._add_error(
                'MISSING_LEVEL_FILES',
                'HIGH',
                f"Missing level files",
                f"Expected {expected_levels} level files, but missing files for levels: {missing_level_files}",
                "Regenerate files in Hierarchy panel",
                'Output Generation',
                'Level Files',
                {
                    'missing_levels': missing_level_files,
                    'expected_levels': expected_levels,
                    'generated_levels': list(level_files.keys())
                }
            )
    
    def _validate_level_file(self, level_num: int, level_data: pd.DataFrame, hrp1000_df: pd.DataFrame, hierarchy_structure: Dict):
        """Validate individual level file"""
        
        # Check if level file has data rows (beyond headers)
        if len(level_data) <= 4:  # Only headers, no data
            self._add_error(
                'EMPTY_LEVEL_FILE',
                'HIGH',
                f"Empty level file for Level {level_num}",
                f"Level {level_num} file contains no data rows",
                "Check hierarchy processing - ensure units exist at this level",
                'Level File Generation',
                f'Level {level_num}',
                {
                    'level_number': level_num,
                    'file_row_count': len(level_data),
                    'expected_units_count': len([uid for uid, info in hierarchy_structure.items() if info.get('level') == level_num])
                }
            )
        
        # Validate that data matches source
        if len(level_data) > 4:  # Has data rows
            data_rows = level_data.iloc[4:]  # Skip header rows
            
            # Check for excessive empty cells
            empty_cells = data_rows.isnull().sum().sum()
            total_cells = len(data_rows) * len(data_rows.columns)
            if total_cells > 0 and empty_cells / total_cells > 0.3:
                self._add_warning(
                    'HIGH_EMPTY_CELL_RATIO',
                    'MEDIUM',
                    f"High empty cell ratio in Level {level_num}",
                    f"Level {level_num} file has {empty_cells/total_cells:.1%} empty cells",
                    "Review mapping configuration to ensure all fields are properly mapped",
                    'Level File Quality',
                    f'Level {level_num}',
                    {
                        'empty_cell_ratio': empty_cells/total_cells,
                        'empty_cells': empty_cells,
                        'total_cells': total_cells
                    }
                )
    
    def _validate_association_file(self, level_num: int, assoc_data: pd.DataFrame, hrp1001_df: pd.DataFrame, hierarchy_structure: Dict):
        """Validate individual association file"""
        
        if len(assoc_data) <= 4:  # Only headers, no data
            # Check if this level should have associations
            level_units = [uid for uid, info in hierarchy_structure.items() if info.get('level') == level_num]
            expected_associations = 0
            
            # Count expected associations for this level
            for _, row in hrp1001_df.iterrows():
                if pd.notna(row.get('Source ID')) and str(row.get('Source ID')) in level_units:
                    expected_associations += 1
            
            if expected_associations > 0:
                self._add_error(
                    'MISSING_ASSOCIATIONS',
                    'HIGH',
                    f"Missing associations for Level {level_num}",
                    f"Expected {expected_associations} associations but file is empty",
                    "Check association file generation logic",
                    'Association File Generation',
                    f'Level {level_num} Associations',
                    {
                        'level_number': level_num,
                        'expected_associations': expected_associations,
                        'actual_associations': 0
                    }
                )
    
    def _validate_pipeline_integrity(self, hrp1000_df: pd.DataFrame, hrp1001_df: pd.DataFrame, hierarchy_structure: Dict, generated_files: Dict):
        """Validate end-to-end pipeline integrity"""
        
        # Count source records
        source_units = len(hrp1000_df)
        source_relationships = len(hrp1001_df)
        
        # Count processed records
        processed_units = len(hierarchy_structure)
        
        # Count output records
        level_files = generated_files.get('level_files', {})
        total_output_units = 0
        for file_info in level_files.values():
            if 'data' in file_info and len(file_info['data']) > 4:
                total_output_units += len(file_info['data']) - 4  # Subtract header rows
        
        # Check for significant data loss
        if processed_units < source_units * 0.9:  # More than 10% loss
            self._add_error(
                'SIGNIFICANT_DATA_LOSS_PROCESSING',
                'HIGH',
                f"Significant data loss during processing",
                f"Source: {source_units} units → Processed: {processed_units} units ({((source_units-processed_units)/source_units)*100:.1f}% loss)",
                "Review hierarchy processing logic and data quality",
                'Pipeline Integrity',
                'Data Processing',
                {
                    'source_units': source_units,
                    'processed_units': processed_units,
                    'loss_percentage': ((source_units-processed_units)/source_units)*100
                }
            )
        
        if total_output_units < processed_units * 0.9:  # More than 10% loss in output
            self._add_error(
                'SIGNIFICANT_DATA_LOSS_OUTPUT',
                'HIGH',
                f"Significant data loss during output generation",
                f"Processed: {processed_units} units → Output: {total_output_units} units ({((processed_units-total_output_units)/processed_units)*100:.1f}% loss)",
                "Review output file generation and mapping configuration",
                'Pipeline Integrity',
                'Output Generation',
                {
                    'processed_units': processed_units,
                    'output_units': total_output_units,
                    'loss_percentage': ((processed_units-total_output_units)/processed_units)*100
                }
            )
    
    def _calculate_hierarchy_from_scratch(self, hrp1000_df: pd.DataFrame, hrp1001_df: pd.DataFrame) -> Dict:
        """Recalculate hierarchy structure from source data"""
        
        # Build parent-child relationships
        relationships = {}
        for _, row in hrp1001_df.iterrows():
            if pd.notna(row.get('Source ID')) and pd.notna(row.get('Target object ID')):
                child_id = str(row['Source ID'])
                parent_id = str(row['Target object ID'])
                relationships[child_id] = parent_id
        
        # Calculate levels
        hierarchy = {}
        all_units = set(hrp1000_df['Object ID'].astype(str))
        
        for unit_id in all_units:
            level = self._calculate_unit_level(unit_id, relationships)
            unit_name = hrp1000_df[hrp1000_df['Object ID'].astype(str) == unit_id]['Name'].iloc[0] if not hrp1000_df[hrp1000_df['Object ID'].astype(str) == unit_id].empty else f"Unit {unit_id}"
            
            hierarchy[unit_id] = {
                'name': unit_name,
                'level': level,
                'parent': relationships.get(unit_id),
                'children': [k for k, v in relationships.items() if v == unit_id]
            }
        
        return hierarchy
    
    def _calculate_unit_level(self, unit_id: str, relationships: Dict, visited: set = None) -> int:
        """Calculate the level of a unit in the hierarchy"""
        if visited is None:
            visited = set()
        
        if unit_id in visited:
            return 999  # Circular reference
        
        if unit_id not in relationships:
            return 1  # Root level
        
        visited.add(unit_id)
        parent_level = self._calculate_unit_level(relationships[unit_id], relationships, visited.copy())
        return parent_level + 1
    
    def _detect_circular_references(self, hierarchy_structure: Dict) -> List:
        """Detect circular references in hierarchy"""
        circular_refs = []
        
        for unit_id, unit_info in hierarchy_structure.items():
            visited = set()
            path = []
            if self._has_circular_reference(unit_id, hierarchy_structure, visited, path):
                circular_refs.append(path)
        
        return circular_refs
    
    def _has_circular_reference(self, unit_id: str, hierarchy: Dict, visited: set, path: List) -> bool:
        """Check if unit has circular reference"""
        if unit_id in visited:
            # Found circular reference
            cycle_start = path.index(unit_id)
            path.append(unit_id)  # Complete the cycle
            return True
        
        visited.add(unit_id)
        path.append(unit_id)
        
        unit_info = hierarchy.get(unit_id, {})
        parent = unit_info.get('parent')
        
        if parent and parent in hierarchy:
            if self._has_circular_reference(parent, hierarchy, visited, path):
                return True
        
        path.pop()
        visited.remove(unit_id)
        return False
    
    def _validate_hierarchy_structure_quality(self, hierarchy_structure: Dict):
        """Validate hierarchy structure quality metrics"""
        
        # Calculate depth distribution
        levels = [info.get('level', 1) for info in hierarchy_structure.values()]
        max_depth = max(levels) if levels else 0
        
        # Check for excessive depth
        if max_depth > 10:
            deep_units = [(uid, info) for uid, info in hierarchy_structure.items() if info.get('level', 1) > 8]
            self._add_warning(
                'EXCESSIVE_HIERARCHY_DEPTH',
                'MEDIUM',
                f"Excessive hierarchy depth",
                f"Maximum depth: {max_depth} levels. Very deep hierarchies can cause performance issues.",
                "Consider flattening hierarchy structure or reviewing organizational design",
                'Hierarchy Structure',
                'Depth Analysis',
                {
                    'max_depth': max_depth,
                    'deep_units': [{'unit_id': uid, 'name': info.get('name'), 'level': info.get('level')} for uid, info in deep_units[:10]],
                    'units_over_8_levels': len(deep_units)
                }
            )
        
        # Check for span of control issues
        span_issues = []
        for unit_id, unit_info in hierarchy_structure.items():
            children_count = len(unit_info.get('children', []))
            if children_count > 15:  # More than 15 direct reports
                span_issues.append({
                    'unit_id': unit_id,
                    'name': unit_info.get('name'),
                    'direct_reports': children_count,
                    'level': unit_info.get('level')
                })
        
        if span_issues:
            self._add_warning(
                'WIDE_SPAN_OF_CONTROL',
                'LOW',
                f"Wide span of control detected",
                f"Found {len(span_issues)} units with more than 15 direct reports",
                "Review organizational structure for management effectiveness",
                'Hierarchy Structure',
                'Span of Control',
                {
                    'span_issues': span_issues[:5],
                    'total_wide_spans': len(span_issues)
                }
            )
    
    def _add_error(self, error_type: str, severity: str, title: str, description: str, 
                   action: str, source: str, field: str, details: Dict = None):
        """Add an error to the list"""
        error = {
            'type': error_type,
            'severity': severity,
            'title': title,
            'description': description,
            'action': action,
            'source': source,
            'field': field,
            'details': details or {},
            'timestamp': datetime.now().isoformat()
        }
        self.errors.append(error)
        self.error_counts[error_type] += 1
    
    def _add_warning(self, warning_type: str, severity: str, title: str, description: str,
                     action: str, source: str, field: str, details: Dict = None):
        """Add a warning to the list"""
        warning = {
            'type': warning_type,
            'severity': severity,
            'title': title,
            'description': description,
            'action': action,
            'source': source,
            'field': field,
            'details': details or {},
            'timestamp': datetime.now().isoformat()
        }
        self.warnings.append(warning)
    
    def _categorize_errors(self) -> Dict:
        """Categorize errors by type and severity"""
        categories = {
            'CRITICAL': {'errors': [], 'count': 0},
            'HIGH': {'errors': [], 'count': 0},
            'MEDIUM': {'errors': [], 'count': 0},
            'LOW': {'errors': [], 'count': 0}
        }
        
        for error in self.errors:
            severity = error['severity']
            categories[severity]['errors'].append(error)
            categories[severity]['count'] += 1
        
        for warning in self.warnings:
            severity = warning['severity']
            categories[severity]['errors'].append(warning)
            categories[severity]['count'] += 1
        
        return categories

def generate_enhanced_fix_code(error):
    """Generate enhanced SQL/Python code with specific examples"""
    
    error_type = error['type']
    details = error.get('details', {})
    
    if error_type == 'ORPHANED_TARGET_ID':
        orphaned_list = details.get('orphaned_targets', [])
        if orphaned_list:
            example_target = orphaned_list[0]['target_id']
            return f"""-- Fix orphaned Target IDs
-- Example: Target ID '{example_target}' doesn't exist in HRP1000

-- Option 1: Find all orphaned Target IDs
SELECT DISTINCT [Target object ID] as Missing_Target_ID
FROM HRP1001 
WHERE [Target object ID] NOT IN (SELECT [Object ID] FROM HRP1000);

-- Option 2: Remove orphaned relationships
DELETE FROM HRP1001 
WHERE [Target object ID] NOT IN (SELECT [Object ID] FROM HRP1000);

-- Option 3: Create missing units in HRP1000 (replace values as needed)
INSERT INTO HRP1000 ([Object ID], [Name], [Planning status])
VALUES ('{example_target}', 'Unit Name for {example_target}', '1');

# Python equivalent
import pandas as pd
# Remove orphaned relationships
valid_units = set(hrp1000['Object ID'].astype(str))
hrp1001_clean = hrp1001[hrp1001['Target object ID'].astype(str).isin(valid_units)]"""
    
    elif error_type == 'DUPLICATE_OBJECT_ID':
        duplicate_groups = details.get('duplicate_groups', {})
        if duplicate_groups:
            example_id = list(duplicate_groups.keys())[0]
            example_rows = duplicate_groups[example_id]
            second_row = example_rows[1]['excel_row'] if len(example_rows) > 1 else 'N/A'
            return f"""-- Fix duplicate Object IDs
-- Example: Object ID '{example_id}' appears in rows {[r['excel_row'] for r in example_rows]}

-- Find all duplicates
SELECT [Object ID], COUNT(*) as Count, 
       STRING_AGG(CAST(ROW_NUMBER() OVER(ORDER BY [Object ID]) AS VARCHAR), ', ') as Row_Numbers
FROM HRP1000
GROUP BY [Object ID]
HAVING COUNT(*) > 1;

-- Remove duplicates (keep first occurrence)
WITH CTE AS (
    SELECT *, ROW_NUMBER() OVER (PARTITION BY [Object ID] ORDER BY [Name], [Planning status]) as rn
    FROM HRP1000
)
DELETE FROM CTE WHERE rn > 1;

-- Manual fix for Object ID '{example_id}':
-- Keep row {example_rows[0]['excel_row']} and delete row {second_row}

# Python equivalent
df_no_duplicates = hrp1000.drop_duplicates(subset=['Object ID'], keep='first')"""
    
    elif error_type == 'NULL_REQUIRED_FIELD':
        null_details = details.get('null_details', [])
        field_name = error.get('field', 'FIELD_NAME')
        if null_details:
            example_row = null_details[0]['row']
            return f"""-- Fix null values in {field_name}
-- Example: Row {example_row} has null {field_name}

-- Find all null values
SELECT ROW_NUMBER() OVER(ORDER BY [Object ID]) as Row_Number, *
FROM HRP1000 
WHERE [{field_name}] IS NULL;

-- Fill with default value
UPDATE HRP1000 
SET [{field_name}] = 'DEFAULT_VALUE' 
WHERE [{field_name}] IS NULL;

-- Excel steps:
-- 1. Open HRP1000 file
-- 2. Filter column '{field_name}' for blank cells
-- 3. Fill blank cells with appropriate values
-- 4. Save file

# Python equivalent
df['{field_name}'].fillna('DEFAULT_VALUE', inplace=True)"""
    
    elif error_type == 'INVALID_ID_FORMAT':
        invalid_ids = details.get('invalid_ids', [])
        if invalid_ids:
            example_id = invalid_ids[0]['current_value']
            return f"""-- Fix invalid Object ID formats
-- Example: '{example_id}' needs to be 8 digits

-- Find all invalid IDs
SELECT [Object ID], LEN(CAST([Object ID] AS VARCHAR)) as Current_Length
FROM HRP1000 
WHERE LEN(CAST([Object ID] AS VARCHAR)) != 8 
   OR [Object ID] NOT LIKE '________' 
   OR [Object ID] LIKE '%[^0-9]%';

-- Pad with leading zeros (SQL Server)
UPDATE HRP1000 
SET [Object ID] = RIGHT('00000000' + CAST([Object ID] AS VARCHAR), 8)
WHERE LEN(CAST([Object ID] AS VARCHAR)) < 8;

-- Excel formula to pad with zeros:
=RIGHT("00000000"&A2,8)

# Python equivalent
import pandas as pd
# Pad Object IDs to 8 digits
df['Object ID'] = df['Object ID'].astype(str).str.zfill(8)

# Remove non-numeric characters and pad
df['Object ID'] = df['Object ID'].str.replace(r'[^0-9]', '', regex=True).str.zfill(8)"""
    
    elif error_type == 'INVALID_STATUS_CODE':
        invalid_statuses = details.get('invalid_statuses', [])
        if invalid_statuses:
            example_status = invalid_statuses[0]['current_value']
            return f"""-- Fix invalid status codes
-- Example: '{example_status}' is not a valid status

-- Find all invalid statuses
SELECT DISTINCT [Planning status], COUNT(*) as Count
FROM HRP1000 
WHERE [Planning status] NOT IN ('1', '2', '3', '0')
GROUP BY [Planning status];

-- Fix common status mappings
UPDATE HRP1000 SET [Planning status] = '1' WHERE [Planning status] IN ('Active', 'A', 'YES', 'TRUE');
UPDATE HRP1000 SET [Planning status] = '2' WHERE [Planning status] IN ('Inactive', 'I', 'NO', 'FALSE');
UPDATE HRP1000 SET [Planning status] = '3' WHERE [Planning status] IN ('Planned', 'P');
UPDATE HRP1000 SET [Planning status] = '0' WHERE [Planning status] IN ('Deleted', 'D');

# Python equivalent
import pandas as pd
# Create mapping dictionary
status_mapping = {{
    'Active': '1', 'A': '1', 'YES': '1', 'TRUE': '1',
    'Inactive': '2', 'I': '2', 'NO': '2', 'FALSE': '2',
    'Planned': '3', 'P': '3',
    'Deleted': '0', 'D': '0'
}}

# Apply mapping
df['Planning status'] = df['Planning status'].astype(str).str.upper().map(status_mapping).fillna(df['Planning status'])"""
    
    elif error_type == 'HIERARCHY_CALCULATION_ERROR':
        return """-- Fix hierarchy calculation errors
-- Recalculate hierarchy levels from relationships

-- Recursive CTE to calculate levels
WITH HierarchyLevels AS (
    -- Root level units (no parent)
    SELECT [Object ID], [Name], 1 as Level
    FROM HRP1000 
    WHERE [Object ID] NOT IN (SELECT [Source ID] FROM HRP1001)
    
    UNION ALL
    
    -- Child units
    SELECT h.[Object ID], h.[Name], hl.Level + 1
    FROM HRP1000 h
    INNER JOIN HRP1001 r ON h.[Object ID] = r.[Source ID]
    INNER JOIN HierarchyLevels hl ON r.[Target object ID] = hl.[Object ID]
)
SELECT * FROM HierarchyLevels
ORDER BY Level, [Object ID];

# Python equivalent - Calculate hierarchy levels
import pandas as pd
from collections import defaultdict

def calculate_hierarchy_levels(hrp1000, hrp1001):
    # Build parent-child relationships
    relationships = {}
    for _, row in hrp1001.iterrows():
        if pd.notna(row['Source ID']) and pd.notna(row['Target object ID']):
            relationships[str(row['Source ID'])] = str(row['Target object ID'])
    
    # Calculate levels
    def get_level(unit_id, visited=None):
        if visited is None:
            visited = set()
        if unit_id in visited:
            return 999  # Circular reference
        if unit_id not in relationships:
            return 1  # Root level
        visited.add(unit_id)
        parent_level = get_level(relationships[unit_id], visited.copy())
        return parent_level + 1
    
    # Apply to all units
    hrp1000['Calculated_Level'] = hrp1000['Object ID'].astype(str).apply(get_level)
    return hrp1000"""
    
    else:
        return f"""-- Manual review required for {error_type}
-- Check the specific details in the Technical Details section
-- Apply appropriate business logic to resolve the issue

# Python template for custom fixes
import pandas as pd
import numpy as np

# Load your data
hrp1000 = pd.read_csv('your_hrp1000_file.csv')
hrp1001 = pd.read_csv('your_hrp1001_file.csv')

# Your custom validation logic here
# Example: Check for specific conditions
# invalid_rows = hrp1000[hrp1000['COLUMN'].condition]

# Fix the issues
# hrp1000.loc[condition, 'COLUMN'] = 'NEW_VALUE'

# Save cleaned data
hrp1000.to_csv('cleaned_hrp1000.csv', index=False)"""

def generate_html_report(validation_results, state):
    """Generate a professional HTML report with advanced styling (from complete version)"""
    
    timestamp = datetime.now().strftime('%B %d, %Y at %I:%M %p')
    categories = validation_results['categorized_errors']
    
    # Get data stats
    hrp1000_df = safe_get_dataframe(state, 'source_hrp1000')
    hrp1001_df = safe_get_dataframe(state, 'source_hrp1001')
    hierarchy_structure = state.get('hierarchy_structure', {})
    generated_files = state.get('generated_output_files', {})
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Migration Validation Report</title>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            body {{
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                margin: 0;
                padding: 20px;
                background-color: #f8f9fa;
                color: #333;
                line-height: 1.6;
            }}
            .container {{
                max-width: 1200px;
                margin: 0 auto;
                background: white;
                border-radius: 15px;
                box-shadow: 0 0 30px rgba(0,0,0,0.1);
                overflow: hidden;
            }}
            .header {{
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 40px;
                text-align: center;
            }}
            .header h1 {{
                margin: 0;
                font-size: 2.5em;
                font-weight: 300;
                text-shadow: 0 2px 4px rgba(0,0,0,0.3);
            }}
            .header p {{
                margin: 10px 0;
                opacity: 0.9;
                font-size: 1.1em;
            }}
            .status-section {{
                padding: 30px;
                border-bottom: 1px solid #e9ecef;
            }}
            .status-ready {{
                background: linear-gradient(135deg, #28a745, #20c997);
                color: white;
                padding: 25px;
                border-radius: 15px;
                text-align: center;
                margin: 20px 0;
                box-shadow: 0 5px 15px rgba(40, 167, 69, 0.3);
            }}
            .status-blocked {{
                background: linear-gradient(135deg, #dc3545, #fd7e14);
                color: white;
                padding: 25px;
                border-radius: 15px;
                text-align: center;
                margin: 20px 0;
                box-shadow: 0 5px 15px rgba(220, 53, 69, 0.3);
            }}
            .metrics-grid {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                gap: 20px;
                margin: 30px 0;
            }}
            .metric-card {{
                background: linear-gradient(135deg, #f8f9fa, #ffffff);
                padding: 25px;
                border-radius: 15px;
                text-align: center;
                border: 2px solid #e9ecef;
                transition: all 0.3s ease;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            }}
            .metric-card:hover {{
                transform: translateY(-5px);
                box-shadow: 0 10px 25px rgba(0,0,0,0.15);
            }}
            .metric-number {{
                font-size: 3.5em;
                font-weight: bold;
                margin: 15px 0;
                text-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }}
            .critical {{ 
                color: #dc3545; 
                border-color: #dc3545; 
                background: linear-gradient(135deg, #fff5f5, #ffe6e6);
            }}
            .high {{ 
                color: #fd7e14; 
                border-color: #fd7e14; 
                background: linear-gradient(135deg, #fff8f0, #ffebdc);
            }}
            .medium {{ 
                color: #007bff; 
                border-color: #007bff; 
                background: linear-gradient(135deg, #f0f8ff, #e6f3ff);
            }}
            .low {{ 
                color: #6c757d; 
                border-color: #6c757d; 
                background: linear-gradient(135deg, #f8f9fa, #e9ecef);
            }}
            .success {{ 
                color: #28a745; 
                border-color: #28a745; 
                background: linear-gradient(135deg, #f8fff9, #e6f7e6);
            }}
            
            .error-section {{
                padding: 30px;
                border-bottom: 1px solid #e9ecef;
            }}
            .error-item {{
                background: #fff;
                border: 1px solid #e9ecef;
                border-left: 5px solid #dc3545;
                border-radius: 0 12px 12px 0;
                padding: 25px;
                margin: 20px 0;
                box-shadow: 0 3px 10px rgba(0,0,0,0.1);
                transition: all 0.3s ease;
            }}
            .error-item:hover {{
                transform: translateX(5px);
                box-shadow: 0 5px 20px rgba(0,0,0,0.15);
            }}
            .error-critical {{ border-left-color: #dc3545; background: linear-gradient(135deg, #fff, #fff5f5); }}
            .error-high {{ border-left-color: #fd7e14; background: linear-gradient(135deg, #fff, #fff8f0); }}
            .error-medium {{ border-left-color: #007bff; background: linear-gradient(135deg, #fff, #f0f8ff); }}
            .error-low {{ border-left-color: #6c757d; background: linear-gradient(135deg, #fff, #f8f9fa); }}
            
            .data-table {{
                width: 100%;
                border-collapse: collapse;
                margin: 20px 0;
                background: white;
                border-radius: 12px;
                overflow: hidden;
                box-shadow: 0 3px 15px rgba(0,0,0,0.1);
            }}
            .data-table th {{
                background: linear-gradient(135deg, #343a40, #495057);
                color: white;
                padding: 15px;
                text-align: left;
                font-weight: 600;
                text-transform: uppercase;
                font-size: 0.9em;
                letter-spacing: 0.5px;
            }}
            .data-table td {{
                padding: 12px 15px;
                border-bottom: 1px solid #e9ecef;
                transition: background-color 0.2s ease;
            }}
            .data-table tr:hover {{
                background: linear-gradient(135deg, #f8f9fa, #e9ecef);
            }}
            .data-table tr:last-child td {{
                border-bottom: none;
            }}
            .footer {{
                background: linear-gradient(135deg, #343a40, #495057);
                color: white;
                padding: 40px;
                text-align: center;
            }}
            .badge {{
                display: inline-block;
                padding: 8px 12px;
                border-radius: 25px;
                font-size: 0.8em;
                font-weight: bold;
                margin: 2px;
                text-transform: uppercase;
                letter-spacing: 0.5px;
            }}
            .badge-critical {{ background: #dc3545; color: white; }}
            .badge-high {{ background: #fd7e14; color: white; }}
            .badge-medium {{ background: #007bff; color: white; }}
            .badge-low {{ background: #6c757d; color: white; }}
            
            .pipeline-grid {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
                gap: 20px;
                margin: 30px 0;
            }}
            .pipeline-item {{
                background: linear-gradient(135deg, #f8f9fa, #ffffff);
                padding: 20px;
                border-radius: 12px;
                text-align: center;
                border: 2px solid #e9ecef;
                transition: all 0.3s ease;
            }}
            .pipeline-complete {{
                border-color: #28a745;
                color: #28a745;
                background: linear-gradient(135deg, #f8fff9, #e6f7e6);
            }}
            .pipeline-incomplete {{
                border-color: #dc3545;
                color: #dc3545;
                background: linear-gradient(135deg, #fff5f5, #ffe6e6);
            }}
            .stats-grid {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
                gap: 20px;
                margin: 30px 0;
            }}
            .stat-card {{
                background: linear-gradient(135deg, #ffffff, #f8f9fa);
                padding: 25px;
                border-radius: 12px;
                box-shadow: 0 3px 15px rgba(0,0,0,0.1);
                border: 1px solid #e9ecef;
                transition: all 0.3s ease;
            }}
            .stat-card:hover {{
                transform: translateY(-3px);
                box-shadow: 0 6px 20px rgba(0,0,0,0.15);
            }}
            .big-number {{
                font-size: 2.5em;
                font-weight: bold;
                color: #007bff;
                text-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }}
            h2 {{
                color: #343a40;
                border-bottom: 2px solid #e9ecef;
                padding-bottom: 10px;
                margin-bottom: 20px;
            }}
            h3 {{
                color: #495057;
                margin-bottom: 15px;
            }}
            .section-divider {{
                height: 1px;
                background: linear-gradient(to right, transparent, #e9ecef, transparent);
                margin: 40px 0;
            }}
            @media print {{
                .container {{
                    box-shadow: none;
                    margin: 0;
                }}
                .metric-card, .error-item {{
                    break-inside: avoid;
                }}
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🔍 Migration Validation Report</h1>
                <p>Complete Pipeline Analysis & Recommendations</p>
                <p>Generated on {timestamp}</p>
            </div>
    """
    
    # Add migration status
    if validation_results['migration_ready']:
        html_content += """
            <div class="status-section">
                <div class="status-ready">
                    <h2>✅ MIGRATION READY</h2>
                    <p>All validations passed. Your complete pipeline is ready for migration!</p>
                </div>
            </div>
        """
    else:
        critical_count = len(validation_results['critical_blockers'])
        html_content += f"""
            <div class="status-section">
                <div class="status-blocked">
                    <h2>❌ MIGRATION BLOCKED</h2>
                    <p>Found {critical_count} critical error(s) that must be fixed before migration.</p>
                </div>
            </div>
        """
    
    # Add pipeline status
    html_content += """
            <div class="status-section">
                <h2>📊 Pipeline Validation Status</h2>
                <div class="pipeline-grid">
    """
    
    pipeline_items = [
        ('Source Files', validation_results['source_files_validated']),
        ('Hierarchy Processing', validation_results['hierarchy_calculations_validated']),
        ('Output Files', validation_results['output_files_validated']),
        ('End-to-End Pipeline', validation_results['pipeline_complete'])
    ]
    
    for item_name, is_complete in pipeline_items:
        status_class = "pipeline-complete" if is_complete else "pipeline-incomplete"
        status_text = "✅ Validated" if is_complete else "❌ Missing"
        html_content += f"""
                    <div class="pipeline-item {status_class}">
                        <strong>{item_name}</strong><br>
                        {status_text}
                    </div>
        """
    
    html_content += """
                </div>
            </div>
    """
    
    # Add error metrics with professional styling
    html_content += """
            <div class="status-section">
                <h2>📈 Error Summary Dashboard</h2>
                <div class="metrics-grid">
    """
    
    error_types = [
        ('CRITICAL', 'critical', 'Critical Issues'),
        ('HIGH', 'high', 'High Priority'),
        ('MEDIUM', 'medium', 'Medium Priority'),
        ('LOW', 'low', 'Low Priority')
    ]
    
    for error_type, css_class, label in error_types:
        count = categories[error_type]['count']
        metric_class = css_class if count > 0 else 'success'
        html_content += f"""
                    <div class="metric-card {metric_class}">
                        <div class="metric-number">{count}</div>
                        <h3>{label}</h3>
                        <p>{'⚠️ Needs attention' if count > 0 else '✅ All clear'}</p>
                    </div>
        """
    
    total_issues = validation_results['total_errors'] + validation_results['total_warnings']
    html_content += f"""
                    <div class="metric-card {'critical' if total_issues > 0 else 'success'}">
                        <div class="metric-number">{total_issues}</div>
                        <h3>Total Issues</h3>
                        <p>{'⚠️ Issues found' if total_issues > 0 else '✅ Perfect data'}</p>
                    </div>
                </div>
            </div>
    """
    
    # Add detailed errors with enhanced styling
    for severity in ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW']:
        errors = categories[severity]['errors']
        if errors:
            severity_class = f"error-{severity.lower()}"
            html_content += f"""
            <div class="error-section">
                <h2>🚨 {severity.title()} Priority Issues ({len(errors)})</h2>
                <p>Found {len(errors)} {severity.lower()} priority issues that need attention:</p>
            """
            
            for i, error in enumerate(errors[:5]):  # Show first 5 errors
                html_content += f"""
                <div class="error-item {severity_class}">
                    <h3><span class="badge badge-{severity.lower()}">{severity}</span> {error['title']}</h3>
                    <p><strong>Source:</strong> {error['source']} | <strong>Field:</strong> {error['field']}</p>
                    <p><strong>Issue:</strong> {error['description']}</p>
                    <p><strong>Action Required:</strong> {error['action']}</p>
                """
                
                # Add specific details if available
                details = error.get('details', {})
                if 'orphaned_targets' in details and details['orphaned_targets']:
                    html_content += """
                    <h4>🎯 Specific Orphaned Target IDs:</h4>
                    <table class="data-table">
                        <tr>
                            <th>Excel Row</th>
                            <th>Missing Target ID</th>
                            <th>Source ID</th>
                            <th>Relationship</th>
                        </tr>
                    """
                    for orphan in details['orphaned_targets'][:5]:
                        html_content += f"""
                        <tr>
                            <td>{orphan['excel_row']}</td>
                            <td>{orphan['target_id']}</td>
                            <td>{orphan['source_id']}</td>
                            <td>{orphan['relationship']}</td>
                        </tr>
                        """
                    html_content += "</table>"
                
                if 'duplicate_groups' in details:
                    html_content += """
                    <h4>🔄 Specific Duplicate Object IDs:</h4>
                    """
                    for obj_id, duplicates in list(details['duplicate_groups'].items())[:2]:
                        html_content += f"""
                        <p><strong>Object ID '{obj_id}' appears in these rows:</strong></p>
                        <table class="data-table">
                            <tr>
                                <th>Excel Row</th>
                                <th>Object ID</th>
                                <th>Name</th>
                                <th>Status</th>
                            </tr>
                        """
                        for dup in duplicates:
                            html_content += f"""
                            <tr>
                                <td>{dup['excel_row']}</td>
                                <td>{dup['object_id']}</td>
                                <td>{dup['name']}</td>
                                <td>{dup['status']}</td>
                            </tr>
                            """
                        html_content += "</table>"
                
                html_content += "</div>"
            
            if len(errors) > 5:
                html_content += f"<p><em>... and {len(errors) - 5} more {severity.lower()} priority issues</em></p>"
            
            html_content += "</div>"
    
    # Add data statistics
    html_content += """
            <div class="status-section">
                <h2>📊 Data Statistics</h2>
                <div class="stats-grid">
    """
    
    if hrp1000_df is not None:
        html_content += f"""
                    <div class="stat-card">
                        <h4>HRP1000 - Organizational Units</h4>
                        <div class="big-number">{len(hrp1000_df):,}</div>
                        <p>Total records</p>
                        <p><strong>Columns:</strong> {len(hrp1000_df.columns)}</p>
                    </div>
        """
    
    if hrp1001_df is not None:
        html_content += f"""
                    <div class="stat-card">
                        <h4>HRP1001 - Relationships</h4>
                        <div class="big-number">{len(hrp1001_df):,}</div>
                        <p>Total relationships</p>
                        <p><strong>Columns:</strong> {len(hrp1001_df.columns)}</p>
                    </div>
        """
    
    if hierarchy_structure:
        max_level = max([info.get('level', 1) for info in hierarchy_structure.values()])
        html_content += f"""
                    <div class="stat-card">
                        <h4>Hierarchy Structure</h4>
                        <div class="big-number">{max_level}</div>
                        <p>Hierarchy levels</p>
                        <p><strong>Units:</strong> {len(hierarchy_structure):,}</p>
                    </div>
        """
    
    if generated_files:
        level_files = generated_files.get('level_files', {})
        association_files = generated_files.get('association_files', {})
        total_files = len(level_files) + len(association_files)
        html_content += f"""
                    <div class="stat-card">
                        <h4>Generated Output Files</h4>
                        <div class="big-number">{total_files}</div>
                        <p>Total files</p>
                        <p><strong>Level:</strong> {len(level_files)} | <strong>Association:</strong> {len(association_files)}</p>
                    </div>
        """
    
    html_content += """
                </div>
            </div>
    """
    
    # Add quick fix guide
    html_content += """
            <div class="status-section">
                <h2>🛠️ Quick Fix Guide</h2>
                <div class="stats-grid">
                    <div class="stat-card">
                        <h4>🎯 Common Quick Fixes</h4>
                        <ul style="text-align: left;">
                            <li><strong>Missing Required Fields:</strong> Add columns to your CSV files</li>
                            <li><strong>Null Values:</strong> Use Excel VLOOKUP or Python fillna()</li>
                            <li><strong>Invalid IDs:</strong> Use Excel formula =RIGHT("00000000"&A1,8)</li>
                            <li><strong>Date Formats:</strong> Use Excel formula =TEXT(A1,"dd.mm.yyyy")</li>
                            <li><strong>Status Codes:</strong> Replace with 1=Active, 2=Inactive, 3=Planned</li>
                        </ul>
                    </div>
                    <div class="stat-card">
                        <h4>🛠️ Tools & Techniques</h4>
                        <ul style="text-align: left;">
                            <li><strong>Excel:</strong> Data → Remove Duplicates, VLOOKUP, Filter for blanks</li>
                            <li><strong>Python:</strong> pandas.drop_duplicates(), fillna(), merge()</li>
                            <li><strong>SQL:</strong> DELETE, UPDATE, INSERT statements for bulk fixes</li>
                            <li><strong>Text Editor:</strong> Find/Replace with regex for format issues</li>
                            <li><strong>Data Validation:</strong> Excel data validation rules</li>
                        </ul>
                    </div>
                </div>
            </div>
    """
    
    # Add footer
    html_content += f"""
            <div class="footer">
                <h3>📋 Report Summary</h3>
                <p>This report analyzed your complete organizational hierarchy pipeline</p>
                <p>Generated by Enhanced Migration Validation Console | {timestamp}</p>
                <p>Org Hierarchy Visual Explorer v2.4</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    return html_content

def generate_excel_report(validation_results, state):
    """Generate a comprehensive Excel report with multiple sheets"""
    
    output = BytesIO()
    
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        
        # Sheet 1: Executive Summary
        summary_data = []
        categories = validation_results['categorized_errors']
        
        summary_data.append(['Migration Status', 'READY' if validation_results['migration_ready'] else 'BLOCKED'])
        summary_data.append(['Total Issues', validation_results['total_errors'] + validation_results['total_warnings']])
        summary_data.append(['Critical Errors', categories['CRITICAL']['count']])
        summary_data.append(['High Priority', categories['HIGH']['count']])
        summary_data.append(['Medium Priority', categories['MEDIUM']['count']])
        summary_data.append(['Low Priority', categories['LOW']['count']])
        
        # Pipeline Status
        summary_data.append(['', ''])
        summary_data.append(['PIPELINE STATUS', ''])
        summary_data.append(['Source Files Validated', 'YES' if validation_results['source_files_validated'] else 'NO'])
        summary_data.append(['Hierarchy Calculated', 'YES' if validation_results['hierarchy_calculations_validated'] else 'NO'])
        summary_data.append(['Output Files Generated', 'YES' if validation_results['output_files_validated'] else 'NO'])
        summary_data.append(['End-to-End Complete', 'YES' if validation_results['pipeline_complete'] else 'NO'])
        
        summary_df = pd.DataFrame(summary_data, columns=['Metric', 'Value'])
        summary_df.to_excel(writer, sheet_name='Executive Summary', index=False)
        
        # Sheet 2: Error Details
        if validation_results['all_errors']:
            error_data = []
            for error in validation_results['all_errors']:
                error_data.append([
                    error['severity'],
                    error['title'],
                    error['source'],
                    error['field'],
                    error['description'],
                    error['action'],
                    error['timestamp']
                ])
            
            error_df = pd.DataFrame(error_data, columns=[
                'Severity', 'Title', 'Source', 'Field', 'Description', 'Action Required', 'Timestamp'
            ])
            error_df.to_excel(writer, sheet_name='All Errors', index=False)
        
        # Sheet 3: Data Statistics
        stats_data = []
        
        hrp1000_df = safe_get_dataframe(state, 'source_hrp1000')
        hrp1001_df = safe_get_dataframe(state, 'source_hrp1001')
        hierarchy_structure = state.get('hierarchy_structure', {})
        generated_files = state.get('generated_output_files', {})
        
        if hrp1000_df is not None:
            stats_data.append(['HRP1000 Records', len(hrp1000_df)])
            stats_data.append(['HRP1000 Columns', len(hrp1000_df.columns)])
        
        if hrp1001_df is not None:
            stats_data.append(['HRP1001 Records', len(hrp1001_df)])
            stats_data.append(['HRP1001 Columns', len(hrp1001_df.columns)])
        
        if hierarchy_structure:
            max_level = max([info.get('level', 1) for info in hierarchy_structure.values()])
            stats_data.append(['Hierarchy Levels', max_level])
            stats_data.append(['Total Units', len(hierarchy_structure)])
        
        if generated_files:
            level_files = generated_files.get('level_files', {})
            association_files = generated_files.get('association_files', {})
            stats_data.append(['Generated Level Files', len(level_files)])
            stats_data.append(['Generated Association Files', len(association_files)])
        
        stats_df = pd.DataFrame(stats_data, columns=['Statistic', 'Count'])
        stats_df.to_excel(writer, sheet_name='Data Statistics', index=False)
    
    output.seek(0)
    return output.getvalue()

def generate_text_report(validation_results, state):
    """Generate a simple text report"""
    
    timestamp = datetime.now().strftime('%B %d, %Y at %I:%M %p')
    categories = validation_results['categorized_errors']
    
    report = f"""
=================================================================
🔍 ENHANCED MIGRATION VALIDATION REPORT
=================================================================

Generated: {timestamp}
Report Type: Complete Pipeline Validation

=================================================================
📊 MIGRATION STATUS
=================================================================

{"✅ MIGRATION READY" if validation_results['migration_ready'] else "❌ MIGRATION BLOCKED"}
{("All validations passed. Complete pipeline is ready for migration." if validation_results['migration_ready'] 
  else f"Found {len(validation_results['critical_blockers'])} critical error(s) that must be fixed before migration.")}

=================================================================
📈 PIPELINE STATUS
=================================================================

Source Files:           {"✅ Validated" if validation_results['source_files_validated'] else "❌ Missing"}
Hierarchy Processing:   {"✅ Validated" if validation_results['hierarchy_calculations_validated'] else "❌ Missing"} 
Output Files:           {"✅ Validated" if validation_results['output_files_validated'] else "❌ Missing"}
End-to-End Pipeline:    {"✅ Complete" if validation_results['pipeline_complete'] else "❌ Incomplete"}

=================================================================
📊 ERROR SUMMARY
=================================================================

CRITICAL:  {categories['CRITICAL']['count']:3d}  (⚠️  Migration blocking)
HIGH:      {categories['HIGH']['count']:3d}  (⚠️  Data corruption risk)  
MEDIUM:    {categories['MEDIUM']['count']:3d}  (ℹ️  Quality issues)
LOW:       {categories['LOW']['count']:3d}  (ℹ️  Minor issues)
           ----
TOTAL:     {validation_results['total_errors'] + validation_results['total_warnings']:3d}  issues found

=================================================================
📋 DETAILED ISSUES
=================================================================
"""
    
    for severity in ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW']:
        errors = categories[severity]['errors']
        if errors:
            report += f"\n🚨 {severity} PRIORITY ISSUES ({len(errors)})\n"
            report += "=" * 50 + "\n"
            
            for i, error in enumerate(errors[:3], 1):  # Show first 3
                report += f"\n{i}. {error['title']}\n"
                report += f"   Source: {error['source']} | Field: {error['field']}\n"
                report += f"   Issue: {error['description']}\n"
                report += f"   Action: {error['action']}\n"
                
                # Add specific details
                details = error.get('details', {})
                if 'orphaned_targets' in details and details['orphaned_targets']:
                    report += f"   Affected Rows: {[o['excel_row'] for o in details['orphaned_targets'][:5]]}\n"
                if 'duplicate_groups' in details:
                    report += f"   Duplicate IDs: {list(details['duplicate_groups'].keys())[:3]}\n"
                
                report += "\n"
            
            if len(errors) > 3:
                report += f"   ... and {len(errors) - 3} more {severity.lower()} issues\n"
    
    # Data Statistics
    hrp1000_df = safe_get_dataframe(state, 'source_hrp1000')
    hrp1001_df = safe_get_dataframe(state, 'source_hrp1001')
    hierarchy_structure = state.get('hierarchy_structure', {})
    
    report += "\n=================================================================\n"
    report += "📊 DATA STATISTICS\n"
    report += "=================================================================\n"
    
    if hrp1000_df is not None:
        report += f"HRP1000 Records:     {len(hrp1000_df):,}\n"
        report += f"HRP1000 Columns:     {len(hrp1000_df.columns)}\n"
    
    if hrp1001_df is not None:
        report += f"HRP1001 Records:     {len(hrp1001_df):,}\n"
        report += f"HRP1001 Columns:     {len(hrp1001_df.columns)}\n"
    
    if hierarchy_structure:
        max_level = max([info.get('level', 1) for info in hierarchy_structure.values()])
        report += f"Hierarchy Levels:    {max_level}\n"
        report += f"Total Units:         {len(hierarchy_structure):,}\n"
    
    report += "\n=================================================================\n"
    report += "🛠️ QUICK FIX RECOMMENDATIONS\n"
    report += "=================================================================\n"
    
    if validation_results['total_errors'] > 0:
        report += """
COMMON FIXES:
• Missing Required Fields: Add columns to your CSV files
• Null Values: Use Excel VLOOKUP or Python fillna()
• Invalid IDs: Use Excel formula =RIGHT("00000000"&A1,8)
• Date Formats: Use Excel formula =TEXT(A1,"dd.mm.yyyy")
• Status Codes: Replace with 1=Active, 2=Inactive, 3=Planned
• Duplicates: Use Excel Remove Duplicates feature
• Orphaned IDs: Cross-reference with VLOOKUP

TOOLS TO USE:
• Excel: Data → Remove Duplicates, VLOOKUP, Filter for blanks
• Python: pandas.drop_duplicates(), fillna(), merge()
• SQL: DELETE, UPDATE, INSERT statements for bulk fixes
"""
    else:
        report += "\n🎉 Excellent! No errors found. Your pipeline is ready for migration.\n"
    
    report += f"\n=================================================================\n"
    report += f"Report End | Generated by Enhanced Migration Validation Console\n"
    report += f"=================================================================\n"
    
    return report

def show_validation_panel(state):
    """Enhanced validation panel with comprehensive pipeline validation and beautiful HTML reports"""
    
    # Professional CSS (same as complete version)
    st.markdown("""
    <style>
    .dev-header {
        background: linear-gradient(135deg, #1f2937 0%, #374151 50%, #4b5563 100%);
        color: #f9fafb;
        padding: 20px;
        border-radius: 10px;
        text-align: center;
        margin-bottom: 20px;
        font-family: 'Source Code Pro', monospace;
        border: 2px solid #6b7280;
    }
    
    .pipeline-status {
        background: rgba(17, 24, 39, 0.1);
        border: 1px solid #374151;
        border-radius: 8px;
        padding: 10px;
        margin: 5px;
        text-align: center;
        font-size: 12px;
    }
    
    .status-complete { border-color: #16a34a; color: #22c55e; }
    .status-incomplete { border-color: #dc2626; color: #ef4444; }
    
    .error-critical {
        background: rgba(239, 68, 68, 0.1);
        border: 2px solid #ef4444;
        border-radius: 8px;
        padding: 15px;
        margin: 10px 0;
        border-left: 6px solid #dc2626;
    }
    
    .error-high {
        background: rgba(245, 158, 11, 0.1);
        border: 2px solid #f59e0b;
        border-radius: 8px;
        padding: 15px;
        margin: 10px 0;
        border-left: 6px solid #d97706;
    }
    
    .error-medium {
        background: rgba(59, 130, 246, 0.1);
        border: 2px solid #3b82f6;
        border-radius: 8px;
        padding: 15px;
        margin: 10px 0;
        border-left: 6px solid #2563eb;
    }
    
    .error-low {
        background: rgba(107, 114, 128, 0.1);
        border: 2px solid #6b7280;
        border-radius: 8px;
        padding: 15px;
        margin: 10px 0;
        border-left: 6px solid #4b5563;
    }
    
    .action-item {
        background: rgba(17, 24, 39, 0.8);
        border: 1px solid #374151;
        border-radius: 6px;
        padding: 10px;
        margin: 8px 0;
        font-family: 'Source Code Pro', monospace;
    }
    
    .error-count {
        font-size: 1.8em;
        font-weight: bold;
        text-align: center;
        padding: 15px;
        border-radius: 8px;
        margin: 10px 0;
        font-family: 'Source Code Pro', monospace;
    }
    
    .count-critical { 
        background: rgba(239, 68, 68, 0.1); 
        color: #ef4444; 
        border: 2px solid #dc2626;
    }
    .count-high { 
        background: rgba(245, 158, 11, 0.1); 
        color: #f59e0b; 
        border: 2px solid #d97706;
    }
    .count-medium { 
        background: rgba(59, 130, 246, 0.1); 
        color: #3b82f6; 
        border: 2px solid #2563eb;
    }
    .count-low { 
        background: rgba(107, 114, 128, 0.1); 
        color: #6b7280; 
        border: 2px solid #4b5563;
    }
    .count-success { 
        background: rgba(34, 197, 94, 0.1); 
        color: #22c55e; 
        border: 2px solid #16a34a;
    }
    
    .migration-status {
        background: rgba(17, 24, 39, 0.8);
        border-radius: 10px;
        padding: 20px;
        margin: 15px 0;
        border: 2px solid #374151;
        text-align: center;
        font-family: 'Source Code Pro', monospace;
    }
    
    .migration-ready {
        border-color: #16a34a !important;
        color: #22c55e !important;
    }
    
    .migration-blocked {
        border-color: #dc2626 !important;
        color: #ef4444 !important;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Header
    st.markdown('''
    <div class="dev-header">
        <h1>ENHANCED MIGRATION VALIDATION CONSOLE</h1>
        <p>Complete Pipeline Validation: Source → Processing → Output</p>
    </div>
    ''', unsafe_allow_html=True)
    
    # Initialize enhanced validator
    if 'enhanced_migration_validator' not in st.session_state:
        st.session_state.enhanced_migration_validator = EnhancedMigrationValidator()
    
    # Run comprehensive validation
    with st.spinner("Running comprehensive pipeline validation..."):
        validation_results = st.session_state.enhanced_migration_validator.validate_complete_pipeline(state)
    
    # [Rest of the UI implementation continues with all the error display logic from the clean version but keeps the enhanced styling...]
    
    # Pipeline status overview
    st.subheader("Pipeline Validation Status")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        status_class = "status-complete" if validation_results['source_files_validated'] else "status-incomplete"
        st.markdown(f'<div class="pipeline-status {status_class}">Source Files<br>{"✅ Validated" if validation_results["source_files_validated"] else "❌ Missing"}</div>', unsafe_allow_html=True)
    
    with col2:
        status_class = "status-complete" if validation_results['hierarchy_calculations_validated'] else "status-incomplete"
        st.markdown(f'<div class="pipeline-status {status_class}">Hierarchy Processing<br>{"✅ Validated" if validation_results["hierarchy_calculations_validated"] else "❌ Missing"}</div>', unsafe_allow_html=True)
    
    with col3:
        status_class = "status-complete" if validation_results['output_files_validated'] else "status-incomplete"
        st.markdown(f'<div class="pipeline-status {status_class}">Output Files<br>{"✅ Validated" if validation_results["output_files_validated"] else "❌ Missing"}</div>', unsafe_allow_html=True)
    
    with col4:
        status_class = "status-complete" if validation_results['pipeline_complete'] else "status-incomplete"
        st.markdown(f'<div class="pipeline-status {status_class}">End-to-End Pipeline<br>{"✅ Complete" if validation_results["pipeline_complete"] else "❌ Incomplete"}</div>', unsafe_allow_html=True)
    
    # Migration readiness status
    if validation_results['migration_ready']:
        st.markdown('''
        <div class="migration-status migration-ready">
            <h2>MIGRATION READY</h2>
            <p>All validations passed. Complete pipeline is ready for migration.</p>
        </div>
        ''', unsafe_allow_html=True)
    else:
        critical_count = len(validation_results['critical_blockers'])
        st.markdown(f'''
        <div class="migration-status migration-blocked">
            <h2>MIGRATION BLOCKED</h2>
            <p>Found {critical_count} critical error(s) that must be fixed before migration.</p>
        </div>
        ''', unsafe_allow_html=True)
    
    # Error summary dashboard
    st.subheader("Error Summary Dashboard")
    st.info("**Understanding Error Priorities:** Critical = Migration blocking, High = Data corruption risk, Medium = Quality issues, Low = Minor inconsistencies")
    
    col1, col2, col3, col4, col5 = st.columns(5)
    categories = validation_results['categorized_errors']
    
    with col1:
        count = categories['CRITICAL']['count']
        count_class = "count-critical" if count > 0 else "count-success"
        st.markdown(f'''
        <div class="error-count {count_class}">
            {count}<br>
            <small>CRITICAL</small>
        </div>
        ''', unsafe_allow_html=True)
        if count > 0:
            st.caption("⚠️ Blocks migration")
        else:
            st.caption("✅ No blockers")
    
    with col2:
        count = categories['HIGH']['count']
        count_class = "count-high" if count > 0 else "count-success"
        st.markdown(f'''
        <div class="error-count {count_class}">
            {count}<br>
            <small>HIGH</small>
        </div>
        ''', unsafe_allow_html=True)
        if count > 0:
            st.caption("⚠️ Data corruption risk")
        else:
            st.caption("✅ No high risks")
    
    with col3:
        count = categories['MEDIUM']['count']
        count_class = "count-medium" if count > 0 else "count-success"
        st.markdown(f'''
        <div class="error-count {count_class}">
            {count}<br>
            <small>MEDIUM</small>
        </div>
        ''', unsafe_allow_html=True)
        if count > 0:
            st.caption("ℹ️ Quality issues")
        else:
            st.caption("✅ Good quality")
    
    with col4:
        count = categories['LOW']['count']
        count_class = "count-low" if count > 0 else "count-success"
        st.markdown(f'''
        <div class="error-count {count_class}">
            {count}<br>
            <small>LOW</small>
        </div>
        ''', unsafe_allow_html=True)
        if count > 0:
            st.caption("ℹ️ Minor issues")
        else:
            st.caption("✅ Clean data")
    
    with col5:
        total_issues = validation_results['total_errors'] + validation_results['total_warnings']
        st.markdown(f'''
        <div class="error-count count-critical">
            {total_issues}<br>
            <small>TOTAL</small>
        </div>
        ''', unsafe_allow_html=True)
        st.caption(f"All issues combined")
    
    # [Continue with the rest of the UI implementation from clean version...]
    
    # Enhanced Export Options with Multiple Formats including Beautiful HTML
    st.divider()
    st.subheader("📥 Export Validation Report")
    st.info("**Choose your preferred format for the comprehensive validation report. Each format is optimized for different use cases:**")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("📄 Export Beautiful HTML Report", type="primary", use_container_width=True):
            html_report = generate_html_report(validation_results, state)
            st.download_button(
                label="📥 Download HTML Report",
                data=html_report,
                file_name=f"validation_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html",
                mime="text/html",
                key="download_html_report",
                use_container_width=True
            )
            st.success("✅ Beautiful HTML report ready for download!")
            st.caption("**Best for:** Presentations, stakeholder reviews, professional reporting")
    
    with col2:
        if st.button("📊 Export Excel Report", type="secondary", use_container_width=True):
            excel_report = generate_excel_report(validation_results, state)
            st.download_button(
                label="📥 Download Excel Report",
                data=excel_report,
                file_name=f"validation_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                key="download_excel_report",
                use_container_width=True
            )
            st.success("✅ Excel report ready for download!")
            st.caption("**Best for:** Data analysis, filtering, pivot tables")
    
    with col3:
        if st.button("📝 Export Text Report", use_container_width=True):
            text_report = generate_text_report(validation_results, state)
            st.download_button(
                label="📥 Download Text Report",
                data=text_report,
                file_name=f"validation_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                mime="text/plain",
                key="download_text_report",
                use_container_width=True
            )
            st.success("✅ Text report ready for download!")
            st.caption("**Best for:** Email, documentation, simple sharing")
    
    with col4:
        if st.button("🔧 Export JSON Report", use_container_width=True):
            error_report = {
                'timestamp': validation_results['timestamp'],
                'pipeline_status': {
                    'source_files_validated': validation_results['source_files_validated'],
                    'hierarchy_calculations_validated': validation_results['hierarchy_calculations_validated'],
                    'output_files_validated': validation_results['output_files_validated'],
                    'pipeline_complete': validation_results['pipeline_complete']
                },
                'migration_ready': validation_results['migration_ready'],
                'summary': validation_results['error_summary'],
                'all_errors': validation_results['all_errors'],
                'all_warnings': validation_results['all_warnings'],
                'categorized_errors': validation_results['categorized_errors']
            }
            
            report_json = json.dumps(error_report, indent=2, default=str)
            
            st.download_button(
                label="📥 Download JSON Report",
                data=report_json,
                file_name=f"validation_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json",
                key="download_json_report",
                use_container_width=True
            )
            st.success("✅ JSON report ready for download!")
            st.caption("**Best for:** Technical teams, API integration, automated processing")

    # Main error tabs
    tab1, tab2, tab3, tab4 = st.tabs([
        f"Critical Blockers ({categories['CRITICAL']['count']})",
        f"High Priority ({categories['HIGH']['count']})",
        f"Medium Priority ({categories['MEDIUM']['count']})", 
        f"Low Priority & Warnings ({categories['LOW']['count']})"
    ])
    
    # Enhanced error display function
    def display_enhanced_errors(errors_list, severity_class, tab_name):
        if not errors_list:
            st.success(f"No {tab_name.lower()} priority issues found!")
            if tab_name == "Critical":
                st.info("**Excellent!** No critical errors means your complete pipeline is ready for migration.")
            return
        
        st.write(f"**Found {len(errors_list)} {tab_name.lower()} priority issues:**")
        
        if tab_name == "Critical":
            st.error("**IMPORTANT:** These errors will prevent successful migration. Fix all critical errors before proceeding.")
        
        for i, error in enumerate(errors_list):
            with st.container():
                st.markdown(f'''
                <div class="{severity_class}">
                    <h4>{error['title']}</h4>
                    <p><strong>Source:</strong> {error['source']} | <strong>Field:</strong> {error['field']}</p>
                    <p><strong>Issue:</strong> {error['description']}</p>
                </div>
                ''', unsafe_allow_html=True)
                
                st.markdown(f'''
                <div class="action-item">
                    <strong>ACTION REQUIRED:</strong><br>
                    {error['action']}
                </div>
                ''', unsafe_allow_html=True)
                
                # Enhanced technical details
                if error['details']:
                    expander_label = f"🔍 Technical Details & Fix Instructions - {error['title']}"
                    with st.expander(expander_label, expanded=False):
                        
                        details = error['details']
                        
                        # Show specific problematic data
                        if 'orphaned_targets' in details:
                            st.write("**🎯 Specific Orphaned Target IDs:**")
                            orphaned_data = []
                            for orphan in details['orphaned_targets'][:10]:
                                orphaned_data.append({
                                    'Excel Row': orphan['excel_row'],
                                    'Missing Target ID': orphan['target_id'],
                                    'Source ID': orphan['source_id'],
                                    'Relationship': orphan['relationship']
                                })
                            st.dataframe(pd.DataFrame(orphaned_data), use_container_width=True)
                            
                            if 'excel_fix_steps' in details:
                                st.write("**📋 Step-by-Step Fix Instructions:**")
                                for step in details['excel_fix_steps']:
                                    st.write(f"- {step}")
                        
                        if 'duplicate_groups' in details:
                            st.write("**🔄 Specific Duplicate Object IDs:**")
                            for obj_id, duplicates in list(details['duplicate_groups'].items())[:3]:
                                st.write(f"**Object ID '{obj_id}' appears in these rows:**")
                                dup_data = []
                                for dup in duplicates:
                                    dup_data.append({
                                        'Excel Row': dup['excel_row'],
                                        'Object ID': dup['object_id'],
                                        'Name': dup['name'],
                                        'Status': dup['status']
                                    })
                                st.dataframe(pd.DataFrame(dup_data), use_container_width=True)
                        
                        if 'null_details' in details:
                            st.write(f"**❌ Rows with Missing {error['field']}:**")
                            null_data = []
                            for null_detail in details['null_details'][:10]:
                                row_info = {
                                    'Excel Row': null_detail['row'],
                                    'Issue': f"Missing {error['field']}"
                                }
                                row_info.update(null_detail['other_data'])
                                null_data.append(row_info)
                            st.dataframe(pd.DataFrame(null_data), use_container_width=True)
                            
                            if 'excel_fix_suggestion' in details:
                                st.info(f"**💡 Excel Fix:** {details['excel_fix_suggestion']}")
                        
                        if 'discrepancies' in details:
                            st.write("**⚠️ Hierarchy Level Calculation Errors:**")
                            disc_data = []
                            for disc in details['discrepancies'][:10]:
                                disc_data.append({
                                    'Unit ID': disc['unit_id'],
                                    'Unit Name': disc['unit_name'],
                                    'Stored Level': disc['stored_level'],
                                    'Calculated Level': disc['calculated_level']
                                })
                            st.dataframe(pd.DataFrame(disc_data), use_container_width=True)
                        
                        if 'invalid_ids' in details:
                            st.write("**🔢 Invalid Object ID Formats:**")
                            id_data = []
                            for invalid_id in details['invalid_ids'][:10]:
                                id_data.append({
                                    'Excel Row': invalid_id['excel_row'],
                                    'Current Value': invalid_id['current_value'],
                                    'Expected Format': invalid_id['expected_format'],
                                    'Suggested Fix': invalid_id['suggested_fix']
                                })
                            st.dataframe(pd.DataFrame(id_data), use_container_width=True)
                            
                            if 'excel_fix_formula' in details:
                                st.code(details['excel_fix_formula'], language='excel')
                        
                        # Show enhanced fix code
                        st.write("**🛠️ Fix with SQL/Python:**")
                        st.caption("Copy and modify this code to fix the issue in your data:")
                        fix_code = generate_enhanced_fix_code(error)
                        st.code(fix_code, language='sql')
                
                st.divider()
    
    with tab1:
        st.header("Critical Blockers - Fix Immediately")
        st.warning("**Migration will fail if these errors are not resolved**")
        critical_errors = categories['CRITICAL']['errors']
        display_enhanced_errors(critical_errors, 'error-critical', 'Critical')
    
    with tab2:
        st.header("High Priority Issues")
        st.info("**These issues may cause data corruption or unexpected behavior during migration**")
        high_errors = categories['HIGH']['errors']
        display_enhanced_errors(high_errors, 'error-high', 'High')
    
    with tab3:
        st.header("Medium Priority Issues") 
        st.info("**These issues should be reviewed but won't block migration. They may cause data quality problems.**")
        medium_errors = categories['MEDIUM']['errors']
        display_enhanced_errors(medium_errors, 'error-medium', 'Medium')
    
    with tab4:
        st.header("Low Priority & Warnings")
        st.info("**Consider addressing these for optimal data quality and system performance**")
        low_errors = categories['LOW']['errors']
        display_enhanced_errors(low_errors, 'error-low', 'Low')

    # Enhanced Quick Fix Suggestions
    st.divider()
    st.subheader("Enhanced Quick Fix Suggestions")
    st.info("**Comprehensive solutions for the most frequently encountered data issues in organizational hierarchy migrations:**")
    
    if validation_results['total_errors'] > 0:
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("""
            **🎯 Common Quick Fixes:**
            1. **Missing Required Fields**: Add columns to your CSV files
            2. **Null Values**: Use Excel VLOOKUP or Python fillna()
            3. **Invalid IDs**: Use Excel formula `=RIGHT("00000000"&A1,8)` to pad with zeros
            4. **Date Formats**: Use Excel formula `=TEXT(A1,"dd.mm.yyyy")`
            5. **Status Codes**: Replace with `1=Active, 2=Inactive, 3=Planned`
            6. **Duplicates**: Use Excel Remove Duplicates feature or SQL DISTINCT
            7. **Orphaned IDs**: Cross-reference with VLOOKUP to find missing units
            """)
        
        with col2:
            st.markdown("""
            **🛠️ Tools & Techniques:**
            - **Excel**: Data → Remove Duplicates, VLOOKUP, Filter for blanks
            - **Python**: `pandas.drop_duplicates()`, `fillna()`, `merge()` for validation
            - **SQL**: `DELETE`, `UPDATE`, `INSERT` statements for bulk fixes
            - **Text Editor**: Find/Replace with regex for format issues
            - **Data Validation**: Excel data validation rules to prevent future errors
            - **Conditional Formatting**: Highlight duplicates and missing values
            """)
    else:
        st.success("**🎉 Excellent! No errors found.** Your complete pipeline is ready for migration.")
        st.info("**What this means:** All validations passed including source files, hierarchy calculations, and output file generation.")

    # Report Format Descriptions
    with st.expander("📋 Report Format Guide", expanded=False):
        st.markdown("""
        ### 📄 **HTML Report**
        - **Beautiful visual formatting** with charts and tables
        - **Color-coded error severity** for easy identification  
        - **Professional layout** perfect for management presentations
        - **Interactive elements** with hover effects and styling
        - **Best for:** Stakeholder reviews, executive summaries, presentations
        
        ### 📊 **Excel Report**  
        - **Multiple worksheets** organized by error type and severity
        - **Data tables** perfect for filtering and analysis
        - **Detailed error breakdown** with specific row references
        - **Statistical summaries** and pivot-ready data structure
        - **Best for:** Data analysts, detailed investigation, tracking fixes
        
        ### 📝 **Text Report**
        - **Simple, clean format** that works everywhere
        - **Hierarchical structure** for easy scanning
        - **Copy-paste friendly** for emails and documentation
        - **Lightweight format** that opens instantly
        - **Best for:** Quick sharing, email reports, documentation
        
        ### 🔧 **JSON Report**
        - **Machine-readable format** for automated processing
        - **Complete data structure** with all error details
        - **API-friendly format** for integration with other tools
        - **Programmatic access** to all validation results
        - **Best for:** Developers, automation, system integration
        """)
    
    st.caption("**💡 Tip:** Use HTML for presentations, Excel for analysis, Text for quick sharing, and JSON for automation!")