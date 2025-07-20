import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
from datetime import datetime
import re
from collections import Counter
import json

def analyze_data_quality(df, df_name):
    """Comprehensive data quality analysis for developers"""
    
    quality_metrics = {
        'dataset_name': df_name,
        'total_rows': len(df),
        'total_columns': len(df.columns),
        'memory_usage_mb': round(df.memory_usage(deep=True).sum() / 1024 / 1024, 2),
        'dtypes_summary': {},
        'missing_data': {},
        'duplicate_analysis': {},
        'outlier_analysis': {},
        'pattern_analysis': {},
        'data_consistency': {}
    }
    
    # Convert dtypes to string to avoid ObjectDType serialization issues
    dtypes_summary = df.dtypes.value_counts()
    quality_metrics['dtypes_summary'] = {str(k): int(v) for k, v in dtypes_summary.items()}
    
    # Missing data analysis
    missing_stats = df.isnull().sum()
    quality_metrics['missing_data'] = {
        'total_missing_cells': int(missing_stats.sum()),
        'missing_percentage': round((missing_stats.sum() / (len(df) * len(df.columns))) * 100, 2),
        'columns_with_missing': {str(k): int(v) for k, v in missing_stats[missing_stats > 0].items()},
        'completely_empty_columns': [str(col) for col in missing_stats[missing_stats == len(df)].index.tolist()],
        'rows_with_missing': int(df.isnull().any(axis=1).sum())
    }
    
    # Duplicate analysis
    duplicate_rows = df.duplicated().sum()
    quality_metrics['duplicate_analysis'] = {
        'duplicate_rows': int(duplicate_rows),
        'duplicate_percentage': round((duplicate_rows / len(df)) * 100, 2) if len(df) > 0 else 0,
        'unique_rows': int(len(df) - duplicate_rows)
    }
    
    # Column-specific analysis
    for col in df.columns:
        col_data = df[col].dropna()
        if len(col_data) == 0:
            continue
            
        # Pattern analysis for text columns
        if df[col].dtype == 'object':
            patterns = analyze_text_patterns(col_data, col)
            quality_metrics['pattern_analysis'][str(col)] = patterns
        
        # Outlier analysis for numeric columns
        elif pd.api.types.is_numeric_dtype(df[col]):
            outliers = analyze_numeric_outliers(col_data, col)
            quality_metrics['outlier_analysis'][str(col)] = outliers
    
    # Data consistency checks
    quality_metrics['data_consistency'] = analyze_data_consistency(df, df_name)
    
    return quality_metrics

def analyze_text_patterns(series, column_name):
    """Analyze patterns in text data"""
    
    patterns = {
        'unique_values': int(series.nunique()),
        'unique_percentage': round((series.nunique() / len(series)) * 100, 2),
        'avg_length': round(series.astype(str).str.len().mean(), 2),
        'max_length': int(series.astype(str).str.len().max()),
        'min_length': int(series.astype(str).str.len().min()),
        'common_patterns': {},
        'data_type_consistency': {},
        'special_characters': {}
    }
    
    # Common value analysis - convert to string and limit to prevent serialization issues
    value_counts = series.value_counts().head(10)
    patterns['most_common_values'] = {str(k): int(v) for k, v in value_counts.items()}
    
    # Pattern detection for specific columns
    if 'id' in column_name.lower() or 'code' in column_name.lower():
        # ID/Code pattern analysis
        str_series = series.astype(str)
        numeric_pattern = int(str_series.str.match(r'^\d+$').sum())
        alphanumeric_pattern = int(str_series.str.match(r'^[a-zA-Z0-9]+$').sum())
        
        patterns['common_patterns'] = {
            'purely_numeric': numeric_pattern,
            'alphanumeric': alphanumeric_pattern,
            'contains_spaces': int(str_series.str.contains(' ').sum()),
            'contains_special_chars': int(str_series.str.contains(r'[^a-zA-Z0-9\s]').sum())
        }
    
    elif 'date' in column_name.lower():
        # Date pattern analysis
        str_series = series.astype(str)
        patterns['common_patterns'] = {
            'dd_mm_yyyy': int(str_series.str.match(r'\d{2}\.\d{2}\.\d{4}').sum()),
            'yyyy_mm_dd': int(str_series.str.match(r'\d{4}-\d{2}-\d{2}').sum()),
            'mm_dd_yyyy': int(str_series.str.match(r'\d{2}/\d{2}/\d{4}').sum()),
            'invalid_formats': int(len(str_series) - (
                str_series.str.match(r'\d{2}\.\d{2}\.\d{4}').sum() +
                str_series.str.match(r'\d{4}-\d{2}-\d{2}').sum() +
                str_series.str.match(r'\d{2}/\d{2}/\d{4}').sum()
            ))
        }
    
    elif 'status' in column_name.lower():
        # Status pattern analysis
        patterns['common_patterns'] = {
            'numeric_status': int(series.apply(lambda x: str(x).isdigit()).sum()),
            'text_status': int(series.apply(lambda x: str(x).isalpha()).sum()),
            'mixed_format': int(series.apply(lambda x: not str(x).isdigit() and not str(x).isalpha()).sum())
        }
    
    return patterns

def analyze_numeric_outliers(series, column_name):
    """Analyze outliers in numeric data"""
    
    outliers = {
        'count': int(len(series)),
        'mean': round(float(series.mean()), 2),
        'median': round(float(series.median()), 2),
        'std': round(float(series.std()), 2),
        'min': float(series.min()),
        'max': float(series.max()),
        'outliers': {}
    }
    
    # IQR method for outlier detection
    Q1 = series.quantile(0.25)
    Q3 = series.quantile(0.75)
    IQR = Q3 - Q1
    lower_bound = Q1 - 1.5 * IQR
    upper_bound = Q3 + 1.5 * IQR
    
    outlier_mask = (series < lower_bound) | (series > upper_bound)
    outlier_count = outlier_mask.sum()
    
    outliers['outliers'] = {
        'count': int(outlier_count),
        'percentage': round((outlier_count / len(series)) * 100, 2),
        'lower_bound': round(float(lower_bound), 2),
        'upper_bound': round(float(upper_bound), 2),
        'outlier_values': [float(x) for x in series[outlier_mask].tolist()[:20]]  # First 20 outliers, converted to float
    }
    
    # Zero and negative value analysis
    outliers['special_values'] = {
        'zero_count': int((series == 0).sum()),
        'negative_count': int((series < 0).sum()),
        'positive_count': int((series > 0).sum())
    }
    
    return outliers

def analyze_data_consistency(df, df_name):
    """Analyze data consistency issues"""
    
    consistency = {
        'encoding_issues': 0,
        'case_inconsistency': {},
        'whitespace_issues': {},
        'format_inconsistency': {}
    }
    
    # Check for encoding issues and case inconsistency
    for col in df.select_dtypes(include=['object']).columns:
        col_data = df[col].dropna().astype(str)
        
        # Case inconsistency
        unique_lower = col_data.str.lower().nunique()
        unique_original = col_data.nunique()
        if unique_lower < unique_original:
            consistency['case_inconsistency'][str(col)] = {
                'unique_original': int(unique_original),
                'unique_lowercase': int(unique_lower),
                'case_variants': int(unique_original - unique_lower)
            }
        
        # Whitespace issues
        with_spaces = col_data.str.contains(r'^\s+|\s+$').sum()
        if with_spaces > 0:
            consistency['whitespace_issues'][str(col)] = {
                'leading_trailing_spaces': int(with_spaces),
                'multiple_spaces': int(col_data.str.contains(r'\s{2,}').sum())
            }
    
    return consistency

def analyze_transformation_pipeline(state):
    """Analyze the complete transformation pipeline from source to output"""
    
    pipeline_analysis = {
        'source_stage': {},
        'transformation_stage': {},
        'output_stage': {},
        'pipeline_metrics': {},
        'data_lineage': {}
    }
    
    # Source stage analysis
    source_hrp1000 = state.get('source_hrp1000')
    source_hrp1001 = state.get('source_hrp1001')
    
    if source_hrp1000 is not None:
        pipeline_analysis['source_stage']['hrp1000'] = analyze_data_quality(source_hrp1000, "Source HRP1000")
    
    if source_hrp1001 is not None:
        pipeline_analysis['source_stage']['hrp1001'] = analyze_data_quality(source_hrp1001, "Source HRP1001")
    
    # Output stage analysis - analyze generated files
    output_files = state.get('generated_output_files', {})
    
    if output_files:
        pipeline_analysis['output_stage'] = {}
        
        # Analyze level files
        level_files = output_files.get('level_files', {})
        for level_num, file_info in level_files.items():
            if 'data' in file_info:
                file_data = file_info['data']
                analysis = analyze_data_quality(file_data, f"Level {level_num} Output")
                pipeline_analysis['output_stage'][f'level_{level_num}'] = analysis
        
        # Analyze association files
        association_files = output_files.get('association_files', {})
        for level_num, file_info in association_files.items():
            if 'data' in file_info:
                file_data = file_info['data']
                analysis = analyze_data_quality(file_data, f"Level {level_num} Associations")
                pipeline_analysis['output_stage'][f'association_{level_num}'] = analysis
    
    # Calculate pipeline metrics
    pipeline_analysis['pipeline_metrics'] = calculate_pipeline_metrics(pipeline_analysis)
    
    # Data lineage tracking
    pipeline_analysis['data_lineage'] = build_data_lineage(state)
    
    return pipeline_analysis

def calculate_pipeline_metrics(pipeline_analysis):
    """Calculate metrics across the entire pipeline"""
    
    metrics = {
        'data_volume_flow': {},
        'quality_improvement': {},
        'transformation_efficiency': {},
        'error_rates': {}
    }
    
    # Data volume flow
    source_total = 0
    output_total = 0
    
    for stage_name, stage_data in pipeline_analysis['source_stage'].items():
        source_total += stage_data.get('total_rows', 0)
    
    for stage_name, stage_data in pipeline_analysis['output_stage'].items():
        output_total += stage_data.get('total_rows', 0)
    
    metrics['data_volume_flow'] = {
        'source_total_rows': source_total,
        'output_total_rows': output_total,
        'volume_change': output_total - source_total,
        'volume_change_percentage': round(((output_total - source_total) / source_total * 100), 2) if source_total > 0 else 0
    }
    
    # Quality improvement metrics
    source_missing_avg = 0
    output_missing_avg = 0
    source_count = 0
    output_count = 0
    
    for stage_name, stage_data in pipeline_analysis['source_stage'].items():
        source_missing_avg += stage_data.get('missing_data', {}).get('missing_percentage', 0)
        source_count += 1
    
    for stage_name, stage_data in pipeline_analysis['output_stage'].items():
        output_missing_avg += stage_data.get('missing_data', {}).get('missing_percentage', 0)
        output_count += 1
    
    if source_count > 0:
        source_missing_avg /= source_count
    if output_count > 0:
        output_missing_avg /= output_count
    
    metrics['quality_improvement'] = {
        'source_missing_avg': round(source_missing_avg, 2),
        'output_missing_avg': round(output_missing_avg, 2),
        'missing_data_improvement': round(source_missing_avg - output_missing_avg, 2)
    }
    
    return metrics

def build_data_lineage(state):
    """Build data lineage tracking from source to output"""
    
    lineage = {
        'transformation_steps': [],
        'column_mappings': {},
        'data_flow': {}
    }
    
    # Get mapping configuration if available
    mapping_config = state.get('mapping_config')
    if mapping_config is not None:
        if isinstance(mapping_config, pd.DataFrame):
            mappings = mapping_config.to_dict('records')
        else:
            mappings = mapping_config
        
        # Build column lineage
        for mapping in mappings:
            source_info = {
                'source_file': mapping.get('source_file', ''),
                'source_column': mapping.get('source_column', ''),
                'transformation': mapping.get('transformation', 'None'),
                'default_value': mapping.get('default_value', '')
            }
            
            target_column = mapping.get('target_column1', '')
            lineage['column_mappings'][target_column] = source_info
    
    # Track transformation steps
    hierarchy_structure = state.get('hierarchy_structure', {})
    if hierarchy_structure:
        max_level = max([info.get('level', 1) for info in hierarchy_structure.values()]) if hierarchy_structure else 1
        
        lineage['transformation_steps'] = [
            {'step': 1, 'description': 'Source data ingestion', 'input': 'HRP1000 + HRP1001', 'output': 'Raw source data'},
            {'step': 2, 'description': 'Hierarchy analysis', 'input': 'Raw source data', 'output': f'{max_level} hierarchy levels'},
            {'step': 3, 'description': 'Data transformation', 'input': 'Hierarchy + Mappings', 'output': 'Level files'},
            {'step': 4, 'description': 'Association generation', 'input': 'Level files + Relationships', 'output': 'Association files'}
        ]
    
    return lineage

def generate_detective_report(state):
    """Generate comprehensive record-by-record analysis in plain English"""
    
    detective_report = {
        'all_records': {},
        'successful_transformations': {},
        'issues_found': {},
        'issue_categories': {},
        'analysis_metadata': {}
    }
    
    # Get all data sources
    source_hrp1000 = state.get("source_hrp1000")
    source_hrp1001 = state.get("source_hrp1001")
    output_files = state.get("generated_output_files", {})
    hierarchy_structure = state.get("hierarchy_structure", {})
    
    # Analyze every Object ID from HRP1000
    if source_hrp1000 is not None and 'Object ID' in source_hrp1000.columns:
        for idx, row in source_hrp1000.iterrows():
            object_id = str(row['Object ID'])
            unit_name = row.get('Name', 'Unknown')
            status = row.get('Planning status', 'Unknown')
            
            # Analyze this specific record
            record_analysis = analyze_single_record(
                object_id, unit_name, status, 
                source_hrp1000, source_hrp1001, 
                output_files, hierarchy_structure
            )
            
            detective_report['all_records'][object_id] = record_analysis
            
            # Categorize the result
            if record_analysis['status'] == 'SUCCESS':
                detective_report['successful_transformations'][object_id] = record_analysis
            else:
                detective_report['issues_found'][object_id] = record_analysis
    
    # Analyze relationship IDs from HRP1001
    if source_hrp1001 is not None:
        for idx, row in source_hrp1001.iterrows():
            source_id = str(row.get('Source ID', ''))
            target_id = str(row.get('Target object ID', ''))
            
            # Check if these IDs are orphaned (not in HRP1000)
            if source_id and source_id not in detective_report['all_records']:
                orphan_analysis = analyze_orphaned_relationship_id(
                    source_id, 'Source ID', source_hrp1000, source_hrp1001
                )
                detective_report['all_records'][source_id] = orphan_analysis
                detective_report['issues_found'][source_id] = orphan_analysis
            
            if target_id and target_id not in detective_report['all_records']:
                orphan_analysis = analyze_orphaned_relationship_id(
                    target_id, 'Target object ID', source_hrp1000, source_hrp1001
                )
                detective_report['all_records'][target_id] = orphan_analysis
                detective_report['issues_found'][target_id] = orphan_analysis
    
    # Generate issue categories summary
    detective_report['issue_categories'] = categorize_issues(detective_report['issues_found'])
    
    # Add metadata
    detective_report['analysis_metadata'] = {
        'total_records_analyzed': len(detective_report['all_records']),
        'success_count': len(detective_report['successful_transformations']),
        'issue_count': len(detective_report['issues_found']),
        'success_rate': len(detective_report['successful_transformations']) / len(detective_report['all_records']) * 100 if detective_report['all_records'] else 0,
        'analysis_timestamp': datetime.now().isoformat()
    }
    
    return detective_report

def analyze_single_record(object_id, unit_name, status, hrp1000_df, hrp1001_df, output_files, hierarchy_structure):
    """Analyze a single Object ID through the entire transformation pipeline"""
    
    analysis = {
        'object_id': object_id,
        'unit_name': unit_name,
        'source_status': status,
        'status': 'SUCCESS',  # Will be changed if issues found
        'explanation': '',
        'technical_details': {},
        'appears_in': [],
        'missing_from': [],
        'recommendations': [],
        'issue_type': None,
        'severity': 'LOW',
        'root_cause': '',
        'how_to_fix': []
    }
    
    # Check hierarchy assignment
    if hierarchy_structure and object_id in hierarchy_structure:
        unit_info = hierarchy_structure[object_id]
        assigned_level = unit_info.get('level', 'Unknown')
        parent_id = unit_info.get('parent', 'None')
        children_count = len(unit_info.get('children', []))
        
        analysis['technical_details']['assigned_level'] = assigned_level
        analysis['technical_details']['parent_unit'] = parent_id
        analysis['technical_details']['children_count'] = children_count
        
        # Check if appears in correct level file
        level_files = output_files.get('level_files', {})
        found_in_level_file = False
        
        if assigned_level in level_files:
            level_data = level_files[assigned_level].get('data')
            if level_data is not None:
                # Check if this Object ID appears in the level file
                # Look for the Object ID in any column that might contain it
                for col in level_data.columns:
                    if level_data[col].astype(str).str.contains(object_id, na=False).any():
                        found_in_level_file = True
                        analysis['appears_in'].append(f"Level {assigned_level} file ({level_files[assigned_level].get('filename', 'Unknown')})")
                        break
        
        # Check if appears in association files (if it has relationships)
        association_files = output_files.get('association_files', {})
        found_in_associations = False
        
        # Check if this ID appears as source or target in HRP1001
        has_relationships = False
        if hrp1001_df is not None:
            is_source = hrp1001_df['Source ID'].astype(str).eq(object_id).any() if 'Source ID' in hrp1001_df.columns else False
            is_target = hrp1001_df['Target object ID'].astype(str).eq(object_id).any() if 'Target object ID' in hrp1001_df.columns else False
            has_relationships = is_source or is_target
            
            analysis['technical_details']['appears_as_source'] = is_source
            analysis['technical_details']['appears_as_target'] = is_target
        
        if has_relationships:
            for level_num, assoc_info in association_files.items():
                assoc_data = assoc_info.get('data')
                if assoc_data is not None:
                    # Check if this Object ID appears in association file
                    for col in assoc_data.columns:
                        if assoc_data[col].astype(str).str.contains(object_id, na=False).any():
                            found_in_associations = True
                            analysis['appears_in'].append(f"Association Level {level_num} file ({assoc_info.get('filename', 'Unknown')})")
                            break
        
        # Generate explanation based on findings
        if found_in_level_file:
            explanation_parts = [
                f"Object ID {object_id} ('{unit_name}') was successfully processed.",
                f"It was assigned to hierarchy Level {assigned_level}.",
                f"It correctly appears in the Level {assigned_level} output file."
            ]
            
            if parent_id and parent_id != 'None':
                explanation_parts.append(f"It reports to parent unit {parent_id}.")
            else:
                explanation_parts.append("It appears to be a top-level unit with no parent.")
            
            if children_count > 0:
                explanation_parts.append(f"It has {children_count} subordinate unit(s) reporting to it.")
            
            if has_relationships:
                if found_in_associations:
                    explanation_parts.append("Its reporting relationships are correctly included in association files.")
                else:
                    explanation_parts.append("WARNING: It has relationships in source data but may be missing from association files.")
                    analysis['status'] = 'WARNING'
                    analysis['missing_from'].append("Some association files")
            
            analysis['explanation'] = " ".join(explanation_parts)
            
            if analysis['status'] == 'WARNING':
                analysis['recommendations'] = [
                    "Check why association relationships are missing",
                    "Verify hierarchy processing completed successfully",
                    "Review association file generation logic"
                ]
        else:
            # Found issues
            analysis['status'] = 'ERROR'
            analysis['issue_type'] = 'MISSING_FROM_OUTPUT'
            analysis['severity'] = 'HIGH'
            analysis['explanation'] = f"Object ID {object_id} ('{unit_name}') exists in source HRP1000 data and was assigned to Level {assigned_level}, but it does not appear in the corresponding Level {assigned_level} output file."
            analysis['root_cause'] = "The transformation process failed to include this record in the output files, possibly due to mapping errors, data type issues, or transformation rule problems."
            analysis['how_to_fix'] = [
                "Check the column mapping configuration for Level files",
                "Verify that the Object ID column mapping is correct",
                "Review transformation rules for data type compatibility",
                "Check for any filtering logic that might exclude this record"
            ]
            analysis['missing_from'].append(f"Level {assigned_level} output file")
    else:
        # Object ID not in hierarchy structure
        analysis['status'] = 'ERROR'
        analysis['issue_type'] = 'NOT_IN_HIERARCHY'
        analysis['severity'] = 'HIGH'
        analysis['explanation'] = f"Object ID {object_id} ('{unit_name}') exists in source HRP1000 data but was not assigned to any hierarchy level during processing."
        analysis['root_cause'] = "The hierarchy analysis failed to process this organizational unit, possibly due to missing relationships, circular references, or data quality issues."
        analysis['how_to_fix'] = [
            "Check if this unit has valid relationships in HRP1001",
            "Verify the Object ID format is consistent",
            "Look for circular reference issues in reporting relationships",
            "Check if the unit is marked as inactive but still referenced"
        ]
        analysis['missing_from'].append("Hierarchy structure")
        analysis['missing_from'].append("All output files")
    
    return analysis

def analyze_orphaned_relationship_id(object_id, id_type, hrp1000_df, hrp1001_df):
    """Analyze an Object ID that appears in relationships but not in HRP1000"""
    
    analysis = {
        'object_id': object_id,
        'unit_name': 'Unknown (not in HRP1000)',
        'source_status': 'Missing',
        'status': 'ERROR',
        'explanation': '',
        'technical_details': {},
        'appears_in': [],
        'missing_from': ['HRP1000 source data'],
        'recommendations': [],
        'issue_type': 'ORPHANED_RELATIONSHIP',
        'severity': 'CRITICAL',
        'root_cause': '',
        'how_to_fix': []
    }
    
    # Count how many times this ID appears in relationships
    relationship_count = 0
    if hrp1001_df is not None:
        if 'Source ID' in hrp1001_df.columns:
            relationship_count += hrp1001_df['Source ID'].astype(str).eq(object_id).sum()
        if 'Target object ID' in hrp1001_df.columns:
            relationship_count += hrp1001_df['Target object ID'].astype(str).eq(object_id).sum()
    
    analysis['technical_details']['relationship_count'] = relationship_count
    analysis['technical_details']['id_type'] = id_type
    
    # Generate explanation
    analysis['explanation'] = f"Object ID {object_id} appears {relationship_count} time(s) in HRP1001 relationships as '{id_type}' but does not exist in the HRP1000 organizational units file. This creates an orphaned relationship that cannot be processed."
    
    analysis['root_cause'] = "This ID is referenced in reporting relationships but the corresponding organizational unit is missing from the master data file (HRP1000). This could be due to incomplete data extraction, deleted units still being referenced, or data synchronization issues."
    
    analysis['how_to_fix'] = [
        f"Add the missing organizational unit {object_id} to HRP1000 with proper name and status",
        f"Remove the invalid relationships referencing {object_id} from HRP1001",
        "Check your data extraction process to ensure all referenced units are included",
        "Verify if this unit was recently deleted but relationships weren't updated"
    ]
    
    analysis['appears_in'].append(f"HRP1001 relationships ({relationship_count} times)")
    
    return analysis

def categorize_issues(issues_dict):
    """Categorize and count different types of issues"""
    
    categories = {}
    
    for object_id, issue_info in issues_dict.items():
        issue_type = issue_info.get('issue_type', 'UNKNOWN')
        
        if issue_type not in categories:
            categories[issue_type] = [0, get_issue_description(issue_type)]
        
        categories[issue_type][0] += 1
    
    return categories

def get_issue_description(issue_type):
    """Get human-readable description for issue types"""
    
    descriptions = {
        'MISSING_FROM_OUTPUT': 'Records that exist in source but missing from output files',
        'NOT_IN_HIERARCHY': 'Records that could not be assigned to hierarchy levels',
        'ORPHANED_RELATIONSHIP': 'Relationship references to non-existent organizational units',
        'TRANSFORMATION_ERROR': 'Records that failed during data transformation',
        'MAPPING_ISSUE': 'Records affected by column mapping problems',
        'DATA_QUALITY': 'Records with data quality issues preventing processing',
        'UNKNOWN': 'Issues with unidentified root causes'
    }
    
    return descriptions.get(issue_type, 'Unknown issue type')

def search_object_id_journey(detective_report, search_id, search_type):
    """Search for specific Object ID in the detective report"""
    
    results = []
    
    # Get the appropriate dataset based on search type
    if search_type == "Issues Only":
        search_data = detective_report.get('issues_found', {})
    elif search_type == "Successful Only":
        search_data = detective_report.get('successful_transformations', {})
    else:  # All Records
        search_data = detective_report.get('all_records', {})
    
    # Search for exact match first
    if search_id in search_data:
        results.append(search_data[search_id])
    
    # Search for partial matches (in case of different formatting)
    for record_id, record_info in search_data.items():
        if search_id.lower() in record_id.lower() and record_id != search_id:
            results.append(record_info)
    
    return results

def create_pipeline_visualizations(pipeline_analysis):
    """Create visualizations for the transformation pipeline"""
    
    visualizations = {}
    
    # Data volume flow chart
    metrics = pipeline_analysis.get('pipeline_metrics', {})
    volume_flow = metrics.get('data_volume_flow', {})
    
    if volume_flow:
        fig_flow = go.Figure(data=[
            go.Bar(name='Source Data', x=['Total Records'], y=[volume_flow.get('source_total_rows', 0)], marker_color='#3b82f6'),
            go.Bar(name='Output Data', x=['Total Records'], y=[volume_flow.get('output_total_rows', 0)], marker_color='#10b981')
        ])
        
        fig_flow.update_layout(
            title='Data Volume: Source vs Output',
            yaxis_title='Number of Records',
            barmode='group'
        )
        visualizations['volume_flow'] = fig_flow
    
    # Quality improvement chart
    quality_improvement = metrics.get('quality_improvement', {})
    if quality_improvement:
        fig_quality = go.Figure(data=[
            go.Bar(
                x=['Source Data', 'Output Data'], 
                y=[quality_improvement.get('source_missing_avg', 0), quality_improvement.get('output_missing_avg', 0)],
                marker_color=['#ef4444', '#10b981'],
                text=[f"{quality_improvement.get('source_missing_avg', 0):.1f}%", 
                      f"{quality_improvement.get('output_missing_avg', 0):.1f}%"],
                textposition='auto'
            )
        ])
        
        fig_quality.update_layout(
            title='Data Quality: Missing Data Percentage',
            yaxis_title='Missing Data %',
            showlegend=False
        )
        visualizations['quality_improvement'] = fig_quality
    
    # Pipeline stages chart
    source_stage = pipeline_analysis.get('source_stage', {})
    output_stage = pipeline_analysis.get('output_stage', {})
    
    if source_stage or output_stage:
        stages = []
        row_counts = []
        column_counts = []
        colors = []
        
        # Add source stages
        for stage_name, stage_data in source_stage.items():
            stages.append(f"Source {stage_name.upper()}")
            row_counts.append(stage_data.get('total_rows', 0))
            column_counts.append(stage_data.get('total_columns', 0))
            colors.append('#3b82f6')
        
        # Add output stages
        for stage_name, stage_data in output_stage.items():
            stages.append(f"Output {stage_name.replace('_', ' ').title()}")
            row_counts.append(stage_data.get('total_rows', 0))
            column_counts.append(stage_data.get('total_columns', 0))
            colors.append('#10b981')
        
        fig_pipeline = make_subplots(
            rows=2, cols=1,
            subplot_titles=('Records by Stage', 'Columns by Stage'),
            vertical_spacing=0.1
        )
        
        fig_pipeline.add_trace(
            go.Bar(x=stages, y=row_counts, name='Records', marker_color=colors),
            row=1, col=1
        )
        
        fig_pipeline.add_trace(
            go.Bar(x=stages, y=column_counts, name='Columns', marker_color=colors, showlegend=False),
            row=2, col=1
        )
        
        fig_pipeline.update_layout(
            title='Pipeline Data Flow by Stage',
            height=600,
            showlegend=False
        )
        
        visualizations['pipeline_stages'] = fig_pipeline
    
    return visualizations

def show_statistics_panel(state):
    """Enhanced statistics panel with end-to-end pipeline analysis - FIXED: No nested expanders"""
    
    st.title("End-to-End Data Pipeline Statistics")
    st.markdown("**Complete analysis from source data through transformations to final output files**")
    st.info("**Developer Insight:** Track data quality, transformations, and output generation across the entire pipeline.")
    
    # Check for data availability
    source_hrp1000 = state.get("source_hrp1000")
    source_hrp1001 = state.get("source_hrp1001")
    output_files = state.get("generated_output_files", {})
    
    # Data availability status
    st.subheader("Pipeline Status Overview")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if source_hrp1000 is not None and not source_hrp1000.empty:
            st.success("Source HRP1000 ✓")
            st.caption(f"{len(source_hrp1000):,} records")
        else:
            st.error("Source HRP1000 ✗")
    
    with col2:
        if source_hrp1001 is not None and not source_hrp1001.empty:
            st.success("Source HRP1001 ✓")
            st.caption(f"{len(source_hrp1001):,} records")
        else:
            st.error("Source HRP1001 ✗")
    
    with col3:
        level_files = output_files.get('level_files', {})
        if level_files:
            st.success(f"Level Files ✓")
            st.caption(f"{len(level_files)} files generated")
        else:
            st.warning("Level Files ⏳")
            st.caption("Not generated yet")
    
    with col4:
        association_files = output_files.get('association_files', {})
        if association_files:
            st.success(f"Association Files ✓")
            st.caption(f"{len(association_files)} files generated")
        else:
            st.warning("Association Files ⏳")
            st.caption("Not generated yet")
    
    # If no data is available
    if (source_hrp1000 is None or source_hrp1000.empty) and (source_hrp1001 is None or source_hrp1001.empty):
        st.error("No source data available for analysis")
        st.info("**Next Steps:** Upload and process data in the Hierarchy panel first")
        return
    
    # Generate comprehensive pipeline analysis
    with st.spinner("Analyzing complete data transformation pipeline..."):
        pipeline_analysis = analyze_transformation_pipeline(state)
    
    # FIXED: Main tabs for different analysis views - NO NESTED EXPANDERS
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "Pipeline Overview",
        "Source Data Analysis", 
        "Output Data Analysis",
        "Transformation Impact",
        "Data Lineage",
        "Data Detective"
    ])
    
    with tab1:
        st.header("End-to-End Pipeline Overview")
        st.info("**Pipeline View:** Shows the complete data flow from source files through transformations to final output files.")
        
        # Pipeline metrics summary
        pipeline_metrics = pipeline_analysis.get('pipeline_metrics', {})
        
        if pipeline_metrics:
            st.subheader("Pipeline Metrics")
            
            col1, col2, col3, col4 = st.columns(4)
            
            volume_flow = pipeline_metrics.get('data_volume_flow', {})
            quality_improvement = pipeline_metrics.get('quality_improvement', {})
            
            with col1:
                source_total = volume_flow.get('source_total_rows', 0)
                st.metric("Source Records", f"{source_total:,}")
                st.caption("Total input records")
            
            with col2:
                output_total = volume_flow.get('output_total_rows', 0)
                st.metric("Output Records", f"{output_total:,}")
                st.caption("Total output records")
            
            with col3:
                volume_change = volume_flow.get('volume_change', 0)
                volume_change_pct = volume_flow.get('volume_change_percentage', 0)
                st.metric("Volume Change", f"{volume_change:,}", f"{volume_change_pct:+.1f}%")
                st.caption("Record count difference")
            
            with col4:
                missing_improvement = quality_improvement.get('missing_data_improvement', 0)
                st.metric("Quality Improvement", f"{missing_improvement:+.1f}%")
                st.caption("Missing data reduction")
        
        # Pipeline visualizations
        visualizations = create_pipeline_visualizations(pipeline_analysis)
        
        if 'volume_flow' in visualizations:
            st.plotly_chart(visualizations['volume_flow'], use_container_width=True)
        
        if 'quality_improvement' in visualizations:
            st.plotly_chart(visualizations['quality_improvement'], use_container_width=True)
        
        if 'pipeline_stages' in visualizations:
            st.plotly_chart(visualizations['pipeline_stages'], use_container_width=True)
        
        # Pipeline health summary - USING REGULAR SECTIONS INSTEAD OF EXPANDERS
        st.subheader("Pipeline Health Summary")
        
        health_items = []
        
        # Check source data quality
        source_stage = pipeline_analysis.get('source_stage', {})
        for stage_name, stage_data in source_stage.items():
            missing_pct = stage_data.get('missing_data', {}).get('missing_percentage', 0)
            duplicate_pct = stage_data.get('duplicate_analysis', {}).get('duplicate_percentage', 0)
            
            if missing_pct < 5 and duplicate_pct < 1:
                health_items.append(f"✅ {stage_name.upper()}: Excellent quality")
            elif missing_pct < 10 and duplicate_pct < 2:
                health_items.append(f"⚠️ {stage_name.upper()}: Good quality")
            else:
                health_items.append(f"❌ {stage_name.upper()}: Needs attention")
        
        # Check output data quality
        output_stage = pipeline_analysis.get('output_stage', {})
        for stage_name, stage_data in output_stage.items():
            missing_pct = stage_data.get('missing_data', {}).get('missing_percentage', 0)
            
            if missing_pct < 5:
                health_items.append(f"✅ {stage_name.replace('_', ' ').title()}: Clean output")
            else:
                health_items.append(f"⚠️ {stage_name.replace('_', ' ').title()}: Review needed")
        
        for item in health_items:
            st.write(item)
    
    with tab2:
        st.header("Source Data Analysis")
        st.info("**Source Analysis:** Detailed quality metrics for your input HRP1000 and HRP1001 files.")
        
        source_stage = pipeline_analysis.get('source_stage', {})
        
        for stage_name, stage_data in source_stage.items():
            st.subheader(f"{stage_name.upper()} Quality Analysis")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Total Records", f"{stage_data.get('total_rows', 0):,}")
                st.metric("Total Columns", stage_data.get('total_columns', 0))
            
            with col2:
                missing_pct = stage_data.get('missing_data', {}).get('missing_percentage', 0)
                st.metric("Missing Data", f"{missing_pct:.2f}%")
                
                duplicate_pct = stage_data.get('duplicate_analysis', {}).get('duplicate_percentage', 0)
                st.metric("Duplicates", f"{duplicate_pct:.2f}%")
            
            with col3:
                memory_mb = stage_data.get('memory_usage_mb', 0)
                st.metric("Memory Usage", f"{memory_mb:.1f} MB")
                
                unique_rows = stage_data.get('duplicate_analysis', {}).get('unique_rows', 0)
                st.metric("Unique Records", f"{unique_rows:,}")
            
            # Column-level analysis - USING SUBHEADER INSTEAD OF EXPANDER
            st.subheader(f"{stage_name.upper()} Column Analysis")
            
            pattern_analysis = stage_data.get('pattern_analysis', {})
            if pattern_analysis:
                pattern_data = []
                for col, patterns in pattern_analysis.items():
                    pattern_data.append({
                        'Column': col,
                        'Unique_Values': patterns.get('unique_values', 0),
                        'Unique_Percentage': f"{patterns.get('unique_percentage', 0):.1f}%",
                        'Avg_Length': patterns.get('avg_length', 0),
                        'Max_Length': patterns.get('max_length', 0)
                    })
                
                if pattern_data:
                    st.dataframe(pd.DataFrame(pattern_data), use_container_width=True)
            
            st.divider()
    
    with tab3:
        st.header("Output Data Analysis")
        st.info("**Output Analysis:** Quality metrics for generated level files and association files after transformation.")
        
        output_stage = pipeline_analysis.get('output_stage', {})
        
        if not output_stage:
            st.warning("No output files generated yet")
            st.info("**Next Steps:** Generate files in the Hierarchy panel to see output analysis")
            return
        
        for stage_name, stage_data in output_stage.items():
            st.subheader(f"{stage_name.replace('_', ' ').title()} Analysis")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Output Records", f"{stage_data.get('total_rows', 0):,}")
                st.metric("Output Columns", stage_data.get('total_columns', 0))
            
            with col2:
                missing_pct = stage_data.get('missing_data', {}).get('missing_percentage', 0)
                st.metric("Missing Data", f"{missing_pct:.2f}%")
                
                if missing_pct < 5:
                    st.success("Excellent data completeness")
                elif missing_pct < 10:
                    st.warning("Good data completeness")
                else:
                    st.error("Review data completeness")
            
            with col3:
                memory_mb = stage_data.get('memory_usage_mb', 0)
                st.metric("File Size", f"{memory_mb:.1f} MB")
                
                # Show quality grade
                quality_score = 100 - missing_pct
                if quality_score >= 95:
                    st.success(f"Quality: A+ ({quality_score:.0f}%)")
                elif quality_score >= 85:
                    st.success(f"Quality: A ({quality_score:.0f}%)")
                elif quality_score >= 75:
                    st.warning(f"Quality: B ({quality_score:.0f}%)")
                else:
                    st.error(f"Quality: C ({quality_score:.0f}%)")
            
            st.divider()
    
    with tab4:
        st.header("Transformation Impact Analysis")
        st.info("**Impact Analysis:** Shows how transformations affected your data from source to output.")
        
        # Before/After comparison
        source_stage = pipeline_analysis.get('source_stage', {})
        output_stage = pipeline_analysis.get('output_stage', {})
        
        if source_stage and output_stage:
            st.subheader("Before vs After Transformation")
            
            # Calculate aggregated metrics
            source_total_rows = sum(stage.get('total_rows', 0) for stage in source_stage.values())
            source_missing_avg = sum(stage.get('missing_data', {}).get('missing_percentage', 0) for stage in source_stage.values()) / len(source_stage)
            
            output_total_rows = sum(stage.get('total_rows', 0) for stage in output_stage.values())
            output_missing_avg = sum(stage.get('missing_data', {}).get('missing_percentage', 0) for stage in output_stage.values()) / len(output_stage) if output_stage else 0
            
            comparison_df = pd.DataFrame({
                'Metric': ['Total Records', 'Average Missing Data %', 'Data Quality Score'],
                'Source (Before)': [
                    f"{source_total_rows:,}",
                    f"{source_missing_avg:.2f}%",
                    f"{100 - source_missing_avg:.0f}/100"
                ],
                'Output (After)': [
                    f"{output_total_rows:,}",
                    f"{output_missing_avg:.2f}%",
                    f"{100 - output_missing_avg:.0f}/100"
                ],
                'Change': [
                    f"{output_total_rows - source_total_rows:+,}",
                    f"{output_missing_avg - source_missing_avg:+.2f}%",
                    f"{(100 - output_missing_avg) - (100 - source_missing_avg):+.0f}"
                ]
            })
            
            st.dataframe(comparison_df, use_container_width=True)
            
            # Transformation effectiveness
            st.subheader("Transformation Effectiveness")
            
            effectiveness_metrics = []
            
            # Data completeness improvement
            missing_improvement = source_missing_avg - output_missing_avg
            if missing_improvement > 0:
                effectiveness_metrics.append(f"✅ Missing data reduced by {missing_improvement:.2f}%")
            elif missing_improvement == 0:
                effectiveness_metrics.append(f"➖ Missing data unchanged")
            else:
                effectiveness_metrics.append(f"⚠️ Missing data increased by {abs(missing_improvement):.2f}%")
            
            # Volume processing
            volume_change = output_total_rows - source_total_rows
            if volume_change > 0:
                effectiveness_metrics.append(f"📈 Output expanded by {volume_change:,} records")
            elif volume_change == 0:
                effectiveness_metrics.append(f"➖ Record count preserved")
            else:
                effectiveness_metrics.append(f"📉 Record count reduced by {abs(volume_change):,}")
            
            # Structure enhancement
            source_cols = sum(stage.get('total_columns', 0) for stage in source_stage.values()) / len(source_stage)
            output_cols = sum(stage.get('total_columns', 0) for stage in output_stage.values()) / len(output_stage) if output_stage else 0
            col_change = output_cols - source_cols
            
            if col_change > 0:
                effectiveness_metrics.append(f"🔧 Structure enhanced with {col_change:.0f} additional columns on average")
            elif col_change == 0:
                effectiveness_metrics.append(f"➖ Column structure maintained")
            else:
                effectiveness_metrics.append(f"🔧 Structure simplified by {abs(col_change):.0f} columns on average")
            
            for metric in effectiveness_metrics:
                st.write(metric)
    
    with tab5:
        st.header("Data Lineage & Transformation Tracking")
        st.info("**Lineage Tracking:** Shows how data flows from source columns through transformations to output columns.")
        
        lineage = pipeline_analysis.get('data_lineage', {})
        
        # Transformation steps
        transformation_steps = lineage.get('transformation_steps', [])
        if transformation_steps:
            st.subheader("Transformation Pipeline Steps")
            
            for step in transformation_steps:
                st.write(f"**Step {step['step']}:** {step['description']}")
                st.write(f"   Input: {step['input']} → Output: {step['output']}")
        
        # Column mappings
        column_mappings = lineage.get('column_mappings', {})
        if column_mappings:
            st.subheader("Column-Level Data Lineage")
            
            lineage_data = []
            for target_col, source_info in column_mappings.items():
                lineage_data.append({
                    'Target_Column': target_col,
                    'Source_File': source_info.get('source_file', ''),
                    'Source_Column': source_info.get('source_column', ''),
                    'Transformation': source_info.get('transformation', 'None'),
                    'Default_Value': source_info.get('default_value', '')
                })
            
            if lineage_data:
                lineage_df = pd.DataFrame(lineage_data)
                st.dataframe(lineage_df, use_container_width=True)
                
                # Transformation summary
                st.subheader("Transformation Summary")
                
                transformation_counts = lineage_df['Transformation'].value_counts()
                
                fig_transformations = px.pie(
                    values=transformation_counts.values,
                    names=transformation_counts.index,
                    title="Distribution of Transformation Types"
                )
                st.plotly_chart(fig_transformations, use_container_width=True)
        
        # Export lineage report
        if st.button("Export Complete Pipeline Report", type="primary"):
            report_data = {
                'pipeline_analysis': pipeline_analysis,
                'generated_at': datetime.now().isoformat(),
                'summary': {
                    'source_files_analyzed': len(pipeline_analysis.get('source_stage', {})),
                    'output_files_analyzed': len(pipeline_analysis.get('output_stage', {})),
                    'transformation_steps': len(transformation_steps),
                    'column_mappings': len(column_mappings)
                }
            }
            
            report_json = json.dumps(report_data, indent=2, default=str)
            st.download_button(
                label="Download Pipeline Analysis Report (JSON)",
                data=report_json,
                file_name=f"pipeline_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json"
            )
            st.caption("**Complete report includes:** Source analysis, output analysis, transformation impact, data lineage, and pipeline metrics.")
    
    with tab6:
        st.header("Data Detective - Record-by-Record Analysis")
        st.info("**Data Detective:** Track every single Object ID through the transformation pipeline and see exactly what happened to each record in plain English.")
        
        # Check if we have the necessary data
        source_hrp1000 = state.get("source_hrp1000")
        source_hrp1001 = state.get("source_hrp1001")
        output_files = state.get("generated_output_files", {})
        hierarchy_structure = state.get("hierarchy_structure", {})
        
        if not all([source_hrp1000 is not None, source_hrp1001 is not None]):
            st.error("Source data not available for detective analysis")
            st.info("Load HRP1000 and HRP1001 files in the Hierarchy panel first")
            return
        
        if not output_files:
            st.warning("Output files not generated yet")
            st.info("Generate level and association files in the Hierarchy panel to see complete analysis")
            return
        
        # Generate detective report
        with st.spinner("Analyzing every record through the transformation pipeline..."):
            detective_report = generate_detective_report(state)
        
        # Summary statistics
        st.subheader("Detective Analysis Summary")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            total_ids = len(detective_report.get('all_records', {}))
            st.metric("Total IDs Analyzed", f"{total_ids:,}")
            st.caption("All unique Object IDs from source")
        
        with col2:
            successful = len(detective_report.get('successful_transformations', {}))
            st.metric("Successfully Processed", f"{successful:,}")
            st.caption("IDs correctly transformed")
        
        with col3:
            issues = len(detective_report.get('issues_found', {}))
            st.metric("Issues Detected", f"{issues:,}")
            st.caption("IDs with problems")
        
        with col4:
            success_rate = (successful / total_ids * 100) if total_ids > 0 else 0
            st.metric("Success Rate", f"{success_rate:.1f}%")
            st.caption("Overall transformation success")
        
        # Issue categories breakdown - USING REGULAR SUBHEADER INSTEAD OF EXPANDER
        if detective_report.get('issue_categories'):
            st.subheader("Issue Categories")
            
            issue_categories = detective_report['issue_categories']
            category_df = pd.DataFrame([
                {'Issue Type': category, 'Count': count, 'Description': desc}
                for category, (count, desc) in issue_categories.items()
            ])
            
            if not category_df.empty:
                # Create pie chart of issues
                fig_issues = px.pie(
                    category_df, 
                    values='Count', 
                    names='Issue Type',
                    title="Distribution of Data Issues"
                )
                st.plotly_chart(fig_issues, use_container_width=True)
                
                # Show issue table
                st.dataframe(category_df, use_container_width=True)
        
        # Search functionality
        st.subheader("Search Specific Object IDs")
        
        col1, col2 = st.columns([3, 1])
        
        with col1:
            search_id = st.text_input(
                "Enter Object ID to investigate:",
                placeholder="e.g., 51003010",
                help="Search for a specific Object ID to see its complete transformation journey"
            )
        
        with col2:
            search_type = st.selectbox(
                "Search in:",
                ["All Records", "Issues Only", "Successful Only"],
                help="Filter search results"
            )
        
        # Show search results - NO EXPANDERS, USING REGULAR SECTIONS
        if search_id:
            search_results = search_object_id_journey(detective_report, search_id, search_type)
            
            if search_results:
                st.subheader(f"Journey of Object ID: {search_id}")
                
                for result in search_results:
                    # FIXED: Using container instead of expander
                    st.markdown(f"### Object ID {result['object_id']} - {result['status']}")
                    
                    # Status indicator
                    if result['status'] == 'SUCCESS':
                        st.success(f"✅ **{result['status']}**")
                    elif result['status'] == 'WARNING':
                        st.warning(f"⚠️ **{result['status']}**")
                    else:
                        st.error(f"❌ **{result['status']}**")
                    
                    # Journey explanation
                    st.markdown("**📖 What Happened (Plain English):**")
                    st.write(result['explanation'])
                    
                    # Technical details - USING SEPARATE SECTION INSTEAD OF EXPANDER
                    st.markdown("**Technical Details:**")
                    for detail_key, detail_value in result['technical_details'].items():
                        st.write(f"**{detail_key}:** {detail_value}")
                    
                    # Recommendations
                    if result.get('recommendations'):
                        st.markdown("**💡 Recommendations:**")
                        for rec in result['recommendations']:
                            st.write(f"• {rec}")
                    
                    st.divider()
            else:
                st.info(f"No results found for Object ID '{search_id}' in {search_type.lower()}")
        
        # Sample problematic records - NO EXPANDERS
        issues_found = detective_report.get('issues_found', {})
        if issues_found:
            st.subheader("Sample Problematic Records")
            st.info("**Review these examples to understand common data issues in your transformation pipeline.**")
            
            # Show first 10 issues as examples - USING SIMPLE SECTIONS
            sample_issues = list(issues_found.items())[:10]
            
            for i, (object_id, issue_info) in enumerate(sample_issues):
                st.markdown(f"#### Issue #{i+1}: Object ID {object_id} - {issue_info['issue_type']}")
                
                # Issue type indicator
                if issue_info['severity'] == 'HIGH':
                    st.error(f"🔥 **{issue_info['issue_type']}** (High Severity)")
                elif issue_info['severity'] == 'MEDIUM':
                    st.warning(f"⚠️ **{issue_info['issue_type']}** (Medium Severity)")
                else:
                    st.info(f"ℹ️ **{issue_info['issue_type']}** (Low Severity)")
                
                # Plain English explanation
                st.markdown("**📖 What Went Wrong:**")
                st.write(issue_info['explanation'])
                
                # Root cause
                st.markdown("**🔍 Root Cause:**")
                st.write(issue_info['root_cause'])
                
                # How to fix
                st.markdown("**🔧 How to Fix:**")
                for fix_step in issue_info['how_to_fix']:
                    st.write(f"• {fix_step}")
                
                st.divider()
        
        # Show successful records sample - NO EXPANDERS
        successful_transformations = detective_report.get('successful_transformations', {})
        if successful_transformations:
            st.subheader("Sample Successful Transformations")
            st.info("**See examples of records that were processed correctly through the pipeline.**")
            
            # Show first 5 successful transformations
            sample_success = list(successful_transformations.items())[:5]
            
            for i, (object_id, success_info) in enumerate(sample_success):
                st.markdown(f"#### Success #{i+1}: Object ID {object_id} - Level {success_info.get('assigned_level', 'Unknown')}")
                
                st.success("✅ **Successfully Processed**")
                
                # Success story
                st.markdown("**📖 Success Story:**")
                st.write(success_info['explanation'])
                
                # Show where it appears
                st.markdown("**📍 Where This Record Appears:**")
                for location in success_info['appears_in']:
                    st.write(f"• {location}")
                
                st.divider()
        
        # Export detective report
        if st.button("Export Complete Detective Report", type="primary"):
            detective_export = {
                'detective_analysis': detective_report,
                'generated_at': datetime.now().isoformat(),
                'summary': {
                    'total_ids_analyzed': len(detective_report.get('all_records', {})),
                    'successful_transformations': len(detective_report.get('successful_transformations', {})),
                    'issues_found': len(detective_report.get('issues_found', {})),
                    'issue_categories': detective_report.get('issue_categories', {})
                }
            }
            
            export_json = json.dumps(detective_export, indent=2, default=str)
            st.download_button(
                label="Download Detective Report (JSON)",
                data=export_json,
                file_name=f"detective_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json"
            )
            st.caption("**Detective report includes:** Complete record-by-record analysis, issue explanations, root causes, and fix recommendations.")