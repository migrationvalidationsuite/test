import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json
import traceback
import sys
import psutil
import os
from collections import defaultdict, deque
import time

class SystemMonitor:
    """Real-time system monitoring for developers"""
    
    def __init__(self):
        self.error_log = deque(maxlen=100)  # Keep last 100 errors
        self.performance_log = deque(maxlen=50)  # Keep last 50 performance snapshots
        
    def log_error(self, error_type, error_message, stack_trace, context=None):
        """Log an error with full context"""
        error_entry = {
            'timestamp': datetime.now().isoformat(),
            'type': error_type,
            'message': str(error_message),
            'stack_trace': stack_trace,
            'context': context or {},
            'severity': self._classify_error_severity(error_type, error_message)
        }
        self.error_log.append(error_entry)
        
    def _classify_error_severity(self, error_type, message):
        """Classify error severity for prioritization"""
        critical_keywords = ['critical', 'fatal', 'crash', 'corruption', 'security']
        high_keywords = ['error', 'exception', 'failed', 'invalid', 'missing']
        
        message_lower = str(message).lower()
        type_lower = str(error_type).lower()
        
        if any(keyword in message_lower or keyword in type_lower for keyword in critical_keywords):
            return 'CRITICAL'
        elif any(keyword in message_lower or keyword in type_lower for keyword in high_keywords):
            return 'HIGH'
        else:
            return 'MEDIUM'
    
    def capture_performance_snapshot(self):
        """Capture current system performance metrics"""
        try:
            memory_info = psutil.virtual_memory()
            cpu_percent = psutil.cpu_percent(interval=0.1)
            
            snapshot = {
                'timestamp': datetime.now().isoformat(),
                'memory_used_mb': round(memory_info.used / 1024 / 1024, 2),
                'memory_available_mb': round(memory_info.available / 1024 / 1024, 2),
                'memory_percent': memory_info.percent,
                'cpu_percent': cpu_percent,
                'session_state_size': len(st.session_state.keys()) if hasattr(st, 'session_state') else 0
            }
            
            self.performance_log.append(snapshot)
            return snapshot
        except Exception as e:
            return {'error': str(e), 'timestamp': datetime.now().isoformat()}

def validate_output_files_integrity(state):
    """Analyze generated output files for quality and integrity"""
    
    output_report = {
        'timestamp': datetime.now().isoformat(),
        'output_quality_score': 100,
        'level_files_analysis': {},
        'association_files_analysis': {},
        'transformation_quality': {},
        'issues': [],
        'recommendations': []
    }
    
    try:
        generated_files = state.get('generated_output_files', {})
        metadata = state.get('output_generation_metadata', {})
        
        if not generated_files:
            output_report['issues'].append("No output files generated yet")
            output_report['output_quality_score'] = 0
            return output_report
        
        # Analyze level files
        level_files = generated_files.get('level_files', {})
        for level_num, file_info in level_files.items():
            if 'data' in file_info:
                df = file_info['data']
                analysis = {
                    'total_rows': len(df),
                    'data_rows': max(0, len(df) - 4),  # Subtract header rows
                    'total_columns': len(df.columns),
                    'filename': file_info.get('filename', f'Level_{level_num}'),
                    'empty_cells': df.isnull().sum().sum(),
                    'data_quality_score': 100
                }
                
                # Check for empty data rows (beyond headers)
                if analysis['data_rows'] == 0:
                    output_report['issues'].append(f"Level {level_num} file has no data rows")
                    analysis['data_quality_score'] -= 50
                
                # Check for excessive empty cells in data portion
                if analysis['data_rows'] > 0:
                    data_portion = df.iloc[4:]  # Skip header rows
                    empty_ratio = data_portion.isnull().sum().sum() / (len(data_portion) * len(data_portion.columns))
                    if empty_ratio > 0.3:
                        output_report['issues'].append(f"Level {level_num} file has {empty_ratio:.1%} empty cells")
                        analysis['data_quality_score'] -= 20
                
                output_report['level_files_analysis'][level_num] = analysis
        
        # Analyze association files
        association_files = generated_files.get('association_files', {})
        for level_num, file_info in association_files.items():
            if 'data' in file_info:
                df = file_info['data']
                analysis = {
                    'total_rows': len(df),
                    'data_rows': max(0, len(df) - 4),  # Subtract header rows
                    'total_columns': len(df.columns),
                    'filename': file_info.get('filename', f'Association_{level_num}'),
                    'empty_cells': df.isnull().sum().sum(),
                    'data_quality_score': 100
                }
                
                # Check for empty relationships
                if analysis['data_rows'] == 0:
                    output_report['issues'].append(f"Association file for Level {level_num} has no relationships")
                    analysis['data_quality_score'] -= 50
                
                output_report['association_files_analysis'][level_num] = analysis
        
        # Overall transformation quality assessment
        total_level_files = len(level_files)
        total_association_files = len(association_files)
        expected_levels = metadata.get('max_hierarchy_level', 1)
        
        output_report['transformation_quality'] = {
            'expected_level_files': expected_levels,
            'generated_level_files': total_level_files,
            'expected_association_files': max(0, expected_levels - 1),  # No associations for level 1
            'generated_association_files': total_association_files,
            'generation_success_rate': ((total_level_files + total_association_files) / 
                                      (expected_levels + max(0, expected_levels - 1))) * 100 if expected_levels > 0 else 0
        }
        
        # Calculate overall score
        if total_level_files == 0:
            output_report['output_quality_score'] = 0
        else:
            avg_level_score = sum(analysis['data_quality_score'] for analysis in output_report['level_files_analysis'].values()) / total_level_files
            avg_assoc_score = sum(analysis['data_quality_score'] for analysis in output_report['association_files_analysis'].values()) / total_association_files if total_association_files > 0 else 100
            output_report['output_quality_score'] = (avg_level_score + avg_assoc_score) / 2
        
        # Generate recommendations
        if output_report['output_quality_score'] < 70:
            output_report['recommendations'].append("Output quality is below acceptable threshold. Review transformation process.")
        
        if len(output_report['issues']) > 0:
            output_report['recommendations'].append("Address identified issues in generated files.")
        
        success_rate = output_report['transformation_quality']['generation_success_rate']
        if success_rate < 100:
            output_report['recommendations'].append(f"File generation success rate is {success_rate:.1f}%. Check for missing files.")
    
    except Exception as e:
        output_report['issues'].append(f"Error analyzing output files: {str(e)}")
        output_report['output_quality_score'] = 0
    
    return output_report

def validate_data_integrity(df1, df2):
    """Comprehensive data integrity validation for developers"""
    
    integrity_report = {
        'timestamp': datetime.now().isoformat(),
        'data_integrity_score': 100,
        'critical_issues': [],
        'warnings': [],
        'recommendations': [],
        'detailed_analysis': {}
    }
    
    try:
        # Basic data validation
        if df1 is None or (hasattr(df1, 'empty') and df1.empty):
            integrity_report['critical_issues'].append("HRP1000 dataset is missing or empty")
            integrity_report['data_integrity_score'] -= 50
        
        if df2 is None or (hasattr(df2, 'empty') and df2.empty):
            integrity_report['critical_issues'].append("HRP1001 dataset is missing or empty")
            integrity_report['data_integrity_score'] -= 50
        
        # Only proceed with detailed analysis if both datasets exist and are DataFrames
        if (df1 is not None and hasattr(df1, 'columns') and 
            df2 is not None and hasattr(df2, 'columns') and
            not df1.empty and not df2.empty):
            
            # Schema validation
            required_hrp1000_cols = ['Object ID', 'Name']
            required_hrp1001_cols = ['Source ID', 'Target object ID']
            
            missing_hrp1000_cols = [col for col in required_hrp1000_cols if col not in df1.columns]
            missing_hrp1001_cols = [col for col in required_hrp1001_cols if col not in df2.columns]
            
            if missing_hrp1000_cols:
                integrity_report['critical_issues'].append(f"HRP1000 missing required columns: {missing_hrp1000_cols}")
                integrity_report['data_integrity_score'] -= 20
            
            if missing_hrp1001_cols:
                integrity_report['critical_issues'].append(f"HRP1001 missing required columns: {missing_hrp1001_cols}")
                integrity_report['data_integrity_score'] -= 20
            
            # Data quality checks
            if not missing_hrp1000_cols and not missing_hrp1001_cols:
                # Referential integrity
                unit_ids = set(df1['Object ID'].astype(str))
                source_ids = set(df2['Source ID'].astype(str))
                target_ids = set(df2['Target object ID'].astype(str))
                
                orphaned_sources = source_ids - unit_ids
                orphaned_targets = target_ids - unit_ids
                
                if orphaned_sources:
                    integrity_report['warnings'].append(f"Found {len(orphaned_sources)} orphaned source IDs")
                    integrity_report['data_integrity_score'] -= 10
                
                if orphaned_targets:
                    integrity_report['warnings'].append(f"Found {len(orphaned_targets)} orphaned target IDs")
                    integrity_report['data_integrity_score'] -= 10
                
                # Duplicate detection
                hrp1000_duplicates = df1['Object ID'].duplicated().sum()
                if hrp1000_duplicates > 0:
                    integrity_report['critical_issues'].append(f"HRP1000 has {hrp1000_duplicates} duplicate Object IDs")
                    integrity_report['data_integrity_score'] -= 15
                
                # Null value analysis
                hrp1000_nulls = df1[required_hrp1000_cols].isnull().sum().sum()
                hrp1001_nulls = df2[required_hrp1001_cols].isnull().sum().sum()
                
                if hrp1000_nulls > 0:
                    integrity_report['warnings'].append(f"HRP1000 has {hrp1000_nulls} null values in required fields")
                    integrity_report['data_integrity_score'] -= 5
                
                if hrp1001_nulls > 0:
                    integrity_report['warnings'].append(f"HRP1001 has {hrp1001_nulls} null values in required fields")
                    integrity_report['data_integrity_score'] -= 5
                
                # Detailed analysis
                integrity_report['detailed_analysis'] = {
                    'hrp1000_stats': {
                        'total_rows': len(df1),
                        'total_columns': len(df1.columns),
                        'null_percentage': round((df1.isnull().sum().sum() / (len(df1) * len(df1.columns))) * 100, 2),
                        'duplicate_rows': int(df1.duplicated().sum()),
                        'memory_usage_mb': round(df1.memory_usage(deep=True).sum() / 1024 / 1024, 2)
                    },
                    'hrp1001_stats': {
                        'total_rows': len(df2),
                        'total_columns': len(df2.columns),
                        'null_percentage': round((df2.isnull().sum().sum() / (len(df2) * len(df2.columns))) * 100, 2),
                        'duplicate_rows': int(df2.duplicated().sum()),
                        'memory_usage_mb': round(df2.memory_usage(deep=True).sum() / 1024 / 1024, 2)
                    },
                    'relationship_analysis': {
                        'total_relationships': len(df2),
                        'unique_sources': len(source_ids),
                        'unique_targets': len(target_ids),
                        'orphaned_sources': len(orphaned_sources),
                        'orphaned_targets': len(orphaned_targets),
                        'referential_integrity_score': round(
                            ((len(source_ids) - len(orphaned_sources)) / len(source_ids) * 50 +
                             (len(target_ids) - len(orphaned_targets)) / len(target_ids) * 50) if source_ids and target_ids else 0, 2
                        )
                    }
                }
    
    except Exception as e:
        integrity_report['critical_issues'].append(f"Error during integrity validation: {str(e)}")
        integrity_report['data_integrity_score'] = 0
    
    # Generate recommendations
    if integrity_report['data_integrity_score'] < 70:
        integrity_report['recommendations'].append("Data integrity score is below acceptable threshold (70%). Review critical issues.")
    
    if integrity_report['critical_issues']:
        integrity_report['recommendations'].append("Address critical issues before proceeding with data processing.")
    
    if len(integrity_report['warnings']) > 5:
        integrity_report['recommendations'].append("Multiple warnings detected. Consider data cleaning procedures.")
    
    return integrity_report

def analyze_session_state_health():
    """Analyze session state for potential issues"""
    
    health_report = {
        'timestamp': datetime.now().isoformat(),
        'total_keys': 0,
        'memory_estimate_mb': 0,
        'large_objects': [],
        'potential_issues': [],
        'recommendations': []
    }
    
    try:
        if hasattr(st, 'session_state'):
            health_report['total_keys'] = len(st.session_state.keys())
            
            total_size = 0
            for key, value in st.session_state.items():
                try:
                    # Estimate object size
                    if hasattr(value, 'memory_usage'):  # DataFrame
                        size_mb = value.memory_usage(deep=True).sum() / 1024 / 1024
                        if size_mb > 10:  # Objects larger than 10MB
                            health_report['large_objects'].append({
                                'key': key,
                                'type': 'DataFrame',
                                'size_mb': round(size_mb, 2),
                                'shape': f"{len(value)} x {len(value.columns)}"
                            })
                        total_size += size_mb
                    elif isinstance(value, (list, dict)):
                        estimated_size = sys.getsizeof(value) / 1024 / 1024
                        if estimated_size > 5:  # Objects larger than 5MB
                            health_report['large_objects'].append({
                                'key': key,
                                'type': type(value).__name__,
                                'size_mb': round(estimated_size, 2),
                                'length': len(value) if hasattr(value, '__len__') else 'Unknown'
                            })
                        total_size += estimated_size
                except Exception as e:
                    health_report['potential_issues'].append(f"Could not analyze object '{key}': {str(e)}")
            
            health_report['memory_estimate_mb'] = round(total_size, 2)
            
            # Generate warnings
            if health_report['memory_estimate_mb'] > 500:
                health_report['potential_issues'].append("Session state using excessive memory (>500MB)")
                health_report['recommendations'].append("Consider clearing unused session state objects")
            
            if len(health_report['large_objects']) > 3:
                health_report['potential_issues'].append("Multiple large objects in session state")
                health_report['recommendations'].append("Review large objects and optimize data storage")
            
            if health_report['total_keys'] > 50:
                health_report['potential_issues'].append("High number of session state keys")
                health_report['recommendations'].append("Clean up unnecessary session state variables")
    
    except Exception as e:
        health_report['potential_issues'].append(f"Error analyzing session state: {str(e)}")
    
    return health_report

def create_real_time_dashboard(monitor, df1, df2):
    """Create real-time monitoring dashboard"""
    
    # Capture current performance
    current_perf = monitor.capture_performance_snapshot()
    
    # Create performance trend chart
    if len(monitor.performance_log) > 1:
        perf_df = pd.DataFrame(list(monitor.performance_log))
        perf_df['timestamp'] = pd.to_datetime(perf_df['timestamp'])
        
        fig_perf = make_subplots(
            rows=2, cols=2,
            subplot_titles=('Memory Usage (%)', 'CPU Usage (%)', 'Memory (MB)', 'Session State Keys'),
            specs=[[{"secondary_y": False}, {"secondary_y": False}],
                   [{"secondary_y": False}, {"secondary_y": False}]]
        )
        
        # Memory percentage
        fig_perf.add_trace(
            go.Scatter(x=perf_df['timestamp'], y=perf_df['memory_percent'], 
                      name='Memory %', line=dict(color='#ef4444')),
            row=1, col=1
        )
        
        # CPU percentage
        fig_perf.add_trace(
            go.Scatter(x=perf_df['timestamp'], y=perf_df['cpu_percent'], 
                      name='CPU %', line=dict(color='#3b82f6')),
            row=1, col=2
        )
        
        # Memory in MB
        fig_perf.add_trace(
            go.Scatter(x=perf_df['timestamp'], y=perf_df['memory_used_mb'], 
                      name='Used MB', line=dict(color='#f59e0b')),
            row=2, col=1
        )
        
        # Session state size
        fig_perf.add_trace(
            go.Scatter(x=perf_df['timestamp'], y=perf_df['session_state_size'], 
                      name='SS Keys', line=dict(color='#10b981')),
            row=2, col=2
        )
        
        fig_perf.update_layout(height=400, title_text="Real-time System Performance")
        return fig_perf
    
    return None

def show_dashboard_panel(state):
    """Enhanced dashboard panel with comprehensive developer error monitoring"""
    
    st.title("Developer Dashboard - System Health & Error Monitoring")
    st.markdown("Real-time monitoring and error detection for development and debugging")
    
    # Initialize system monitor
    if 'system_monitor' not in st.session_state:
        st.session_state.system_monitor = SystemMonitor()
    
    monitor = st.session_state.system_monitor
    
    # Get data with safe access
    df1 = state.get("source_hrp1000")
    df2 = state.get("source_hrp1001")
    
    # Auto-refresh option
    auto_refresh = st.sidebar.checkbox("Auto-refresh (30s)", value=False)
    if auto_refresh:
        time.sleep(1)  # Small delay
        st.rerun()
    
    # Current system status
    st.subheader("System Status Overview")
    
    try:
        # Capture current performance
        current_perf = monitor.capture_performance_snapshot()
        
        # Validate data integrity
        integrity_report = validate_data_integrity(df1, df2)
        
        # Analyze output files
        output_report = validate_output_files_integrity(state)
        
        # Analyze session state
        session_health = analyze_session_state_health()
        
        # Status indicators
        col1, col2, col3, col4, col5, col6 = st.columns(6)
        
        with col1:
            data_status = "Healthy" if df1 is not None and df2 is not None else "Missing Data"
            st.metric("Data Status", data_status)
        
        with col2:
            integrity_score = integrity_report['data_integrity_score']
            st.metric("Integrity Score", f"{integrity_score}/100")
        
        with col3:
            output_score = output_report['output_quality_score']
            st.metric("Output Quality", f"{output_score:.0f}/100")
        
        with col4:
            if 'memory_percent' in current_perf:
                st.metric("Memory Usage", f"{current_perf['memory_percent']:.1f}%")
            else:
                st.metric("Memory Usage", "N/A")
        
        with col5:
            error_count = len([e for e in monitor.error_log if e['severity'] in ['CRITICAL', 'HIGH']])
            st.metric("Critical Errors", error_count)
        
        with col6:
            session_size = session_health['memory_estimate_mb']
            st.metric("Session Size", f"{session_size:.1f} MB")
        
    except Exception as e:
        st.error(f"Error in status overview: {str(e)}")
        monitor.log_error("Dashboard Error", str(e), traceback.format_exc(), {"section": "status_overview"})
    
    # Main dashboard tabs
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "Data Health Monitor",
        "Output Files Analysis",
        "Real-time Performance", 
        "Error Tracking",
        "Session State Analysis",
        "System Diagnostics"
    ])
    
    with tab1:
        st.header("Data Health Monitor")
        
        if df1 is None and df2 is None:
            st.error("No data loaded - Upload files in Hierarchy panel")
            st.info("**Debugging Steps:**")
            st.write("1. Go to Hierarchy panel")
            st.write("2. Upload HRP1000 and HRP1001 files")
            st.write("3. Process the files")
            st.write("4. Return to this dashboard")
            
            # Show what's available in state
            available_keys = [k for k in state.keys() if any(term in k.lower() for term in ['source', 'hrp', 'data'])]
            if available_keys:
                st.write("**Available state keys:**", available_keys)
        else:
            # Data integrity dashboard
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("Integrity Score Breakdown")
                
                # Safe access to detailed analysis
                detailed_analysis = integrity_report.get('detailed_analysis', {})
                relationship_analysis = detailed_analysis.get('relationship_analysis', {})
                
                score_components = {
                    'Schema Compliance': 100 if not integrity_report['critical_issues'] else 70,
                    'Referential Integrity': relationship_analysis.get('referential_integrity_score', 0),
                    'Data Completeness': 100 - len(integrity_report['warnings']) * 5,
                    'Format Consistency': 90 if len(integrity_report['warnings']) < 3 else 70
                }
                
                fig_score = go.Figure(data=[
                    go.Bar(x=list(score_components.keys()), y=list(score_components.values()),
                          marker_color=['#22c55e' if v >= 80 else '#f59e0b' if v >= 60 else '#ef4444' for v in score_components.values()])
                ])
                fig_score.update_layout(title="Data Quality Components", yaxis_title="Score")
                st.plotly_chart(fig_score, use_container_width=True)
            
            with col2:
                st.subheader("Issues Summary")
                if integrity_report['critical_issues']:
                    st.error("Critical Issues:")
                    for issue in integrity_report['critical_issues']:
                        st.write(f"- {issue}")
                
                if integrity_report['warnings']:
                    st.warning("Warnings:")
                    for warning in integrity_report['warnings'][:5]:  # Show first 5
                        st.write(f"- {warning}")
                
                if integrity_report['recommendations']:
                    st.info("Recommendations:")
                    for rec in integrity_report['recommendations']:
                        st.write(f"- {rec}")
            
            # Detailed data statistics
            if detailed_analysis:
                st.subheader("Detailed Data Analysis")
                
                hrp1000_stats = detailed_analysis.get('hrp1000_stats', {})
                hrp1001_stats = detailed_analysis.get('hrp1001_stats', {})
                
                # Create comparison chart
                comparison_data = {
                    'Dataset': ['HRP1000', 'HRP1001'],
                    'Rows': [hrp1000_stats.get('total_rows', 0), hrp1001_stats.get('total_rows', 0)],
                    'Columns': [hrp1000_stats.get('total_columns', 0), hrp1001_stats.get('total_columns', 0)],
                    'Null %': [hrp1000_stats.get('null_percentage', 0), hrp1001_stats.get('null_percentage', 0)],
                    'Duplicates': [hrp1000_stats.get('duplicate_rows', 0), hrp1001_stats.get('duplicate_rows', 0)],
                    'Memory MB': [hrp1000_stats.get('memory_usage_mb', 0), hrp1001_stats.get('memory_usage_mb', 0)]
                }
                
                comparison_df = pd.DataFrame(comparison_data)
                st.dataframe(comparison_df, use_container_width=True)
                
                # Relationship analysis
                if relationship_analysis:
                    st.subheader("Relationship Analysis")
                    
                    rel_col1, rel_col2, rel_col3 = st.columns(3)
                    with rel_col1:
                        st.metric("Total Relationships", relationship_analysis.get('total_relationships', 0))
                    with rel_col2:
                        st.metric("Orphaned Sources", relationship_analysis.get('orphaned_sources', 0))
                    with rel_col3:
                        st.metric("Orphaned Targets", relationship_analysis.get('orphaned_targets', 0))
    
    with tab2:
        st.header("Output Files Analysis")
        
        # Get output files analysis
        output_report = validate_output_files_integrity(state)
        generated_files = state.get('generated_output_files', {})
        metadata = state.get('output_generation_metadata', {})
        
        if not generated_files:
            st.warning("No output files have been generated yet")
            st.info("**To generate output files:**")
            st.write("1. Go to the Hierarchy panel")
            st.write("2. Upload and process your HRP1000 and HRP1001 files")
            st.write("3. Click 'Generate All Files'")
            st.write("4. Return to this dashboard for analysis")
        else:
            # Output files overview
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                level_files_count = len(generated_files.get('level_files', {}))
                st.metric("Level Files", level_files_count)
                st.caption("Organizational unit files")
            
            with col2:
                association_files_count = len(generated_files.get('association_files', {}))
                st.metric("Association Files", association_files_count)
                st.caption("Relationship files")
            
            with col3:
                output_score = output_report['output_quality_score']
                st.metric("Quality Score", f"{output_score:.0f}/100")
                st.caption("Overall output quality")
            
            with col4:
                generation_time = metadata.get('generated_at', 'Unknown')
                if generation_time != 'Unknown':
                    from datetime import datetime
                    try:
                        gen_time = datetime.fromisoformat(generation_time)
                        time_diff = datetime.now() - gen_time
                        if time_diff.seconds < 60:
                            time_ago = "Just now"
                        elif time_diff.seconds < 3600:
                            time_ago = f"{time_diff.seconds // 60}m ago"
                        else:
                            time_ago = f"{time_diff.seconds // 3600}h ago"
                        st.metric("Generated", time_ago)
                    except:
                        st.metric("Generated", "Recently")
                else:
                    st.metric("Generated", "Unknown")
                st.caption("Last generation time")
            
            # Transformation quality metrics
            st.subheader("Transformation Quality Assessment")
            
            transformation_quality = output_report.get('transformation_quality', {})
            if transformation_quality:
                col1, col2 = st.columns(2)
                
                with col1:
                    # File generation success rate
                    success_rate = transformation_quality.get('generation_success_rate', 0)
                    fig_success = go.Figure(go.Indicator(
                        mode="gauge+number+delta",
                        value=success_rate,
                        domain={'x': [0, 1], 'y': [0, 1]},
                        title={'text': "File Generation Success Rate"},
                        delta={'reference': 100},
                        gauge={
                            'axis': {'range': [None, 100]},
                            'bar': {'color': "darkblue"},
                            'steps': [
                                {'range': [0, 50], 'color': "lightgray"},
                                {'range': [50, 80], 'color': "yellow"},
                                {'range': [80, 100], 'color': "lightgreen"}
                            ],
                            'threshold': {
                                'line': {'color': "red", 'width': 4},
                                'thickness': 0.75,
                                'value': 90
                            }
                        }
                    ))
                    fig_success.update_layout(height=300)
                    st.plotly_chart(fig_success, use_container_width=True)
                
                with col2:
                    # Files comparison
                    expected_level = transformation_quality.get('expected_level_files', 0)
                    generated_level = transformation_quality.get('generated_level_files', 0)
                    expected_assoc = transformation_quality.get('expected_association_files', 0)
                    generated_assoc = transformation_quality.get('generated_association_files', 0)
                    
                    comparison_data = {
                        'File Type': ['Level Files', 'Association Files'],
                        'Expected': [expected_level, expected_assoc],
                        'Generated': [generated_level, generated_assoc]
                    }
                    comparison_df = pd.DataFrame(comparison_data)
                    
                    fig_comparison = px.bar(comparison_df, x='File Type', y=['Expected', 'Generated'],
                                          title='Expected vs Generated Files',
                                          barmode='group')
                    st.plotly_chart(fig_comparison, use_container_width=True)
            
            # Level files analysis
            st.subheader("Level Files Analysis")
            level_analysis = output_report.get('level_files_analysis', {})
            
            if level_analysis:
                level_data = []
                for level_num, analysis in level_analysis.items():
                    level_data.append({
                        'Level': f"Level {level_num}",
                        'Filename': analysis.get('filename', ''),
                        'Data Rows': analysis.get('data_rows', 0),
                        'Columns': analysis.get('total_columns', 0),
                        'Empty Cells': analysis.get('empty_cells', 0),
                        'Quality Score': f"{analysis.get('data_quality_score', 0):.0f}/100"
                    })
                
                level_df = pd.DataFrame(level_data)
                st.dataframe(level_df, use_container_width=True)
                
                # Level files quality visualization
                quality_scores = [analysis.get('data_quality_score', 0) for analysis in level_analysis.values()]
                level_names = [f"Level {num}" for num in level_analysis.keys()]
                
                fig_quality = px.bar(x=level_names, y=quality_scores,
                                   title='Level Files Quality Scores',
                                   color=quality_scores,
                                   color_continuous_scale='RdYlGn')
                fig_quality.update_layout(yaxis_title='Quality Score', xaxis_title='Level')
                st.plotly_chart(fig_quality, use_container_width=True)
            else:
                st.info("No level files to analyze")
            
            # Association files analysis
            st.subheader("Association Files Analysis")
            association_analysis = output_report.get('association_files_analysis', {})
            
            if association_analysis:
                assoc_data = []
                for level_num, analysis in association_analysis.items():
                    assoc_data.append({
                        'Level': f"Level {level_num}",
                        'Filename': analysis.get('filename', ''),
                        'Relationships': analysis.get('data_rows', 0),
                        'Columns': analysis.get('total_columns', 0),
                        'Empty Cells': analysis.get('empty_cells', 0),
                        'Quality Score': f"{analysis.get('data_quality_score', 0):.0f}/100"
                    })
                
                assoc_df = pd.DataFrame(assoc_data)
                st.dataframe(assoc_df, use_container_width=True)
            else:
                st.info("No association files to analyze")
            
            # Issues and recommendations
            if output_report.get('issues') or output_report.get('recommendations'):
                col1, col2 = st.columns(2)
                
                with col1:
                    if output_report.get('issues'):
                        st.subheader("Issues Found")
                        for issue in output_report['issues']:
                            st.error(f"• {issue}")
                
                with col2:
                    if output_report.get('recommendations'):
                        st.subheader("Recommendations")
                        for rec in output_report['recommendations']:
                            st.info(f"• {rec}")
            
            # Data lineage and transformation tracking
            st.subheader("Data Lineage & Transformation Tracking")
            
            # Show source to output transformation summary
            source_hrp1000 = state.get('source_hrp1000')
            source_hrp1001 = state.get('source_hrp1001')
            
            if source_hrp1000 is not None and source_hrp1001 is not None:
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("Source Records (HRP1000)", len(source_hrp1000))
                    st.caption("Original organizational units")
                
                with col2:
                    st.metric("Source Relationships (HRP1001)", len(source_hrp1001))
                    st.caption("Original relationships")
                
                with col3:
                    total_output_rows = sum(analysis.get('data_rows', 0) for analysis in level_analysis.values())
                    total_output_rows += sum(analysis.get('data_rows', 0) for analysis in association_analysis.values())
                    st.metric("Output Records", total_output_rows)
                    st.caption("Generated records in all files")
                
                # Transformation efficiency
                if len(source_hrp1000) > 0:
                    transformation_efficiency = (total_output_rows / (len(source_hrp1000) + len(source_hrp1001))) * 100
                    if transformation_efficiency > 50:
                        st.success(f"Transformation Efficiency: {transformation_efficiency:.1f}%")
                    elif transformation_efficiency > 25:
                        st.warning(f"Transformation Efficiency: {transformation_efficiency:.1f}%")
                    else:
                        st.error(f"Transformation Efficiency: {transformation_efficiency:.1f}%")
                    
                    st.caption("Percentage of source records successfully transformed to output")

    with tab3:
        st.header("Real-time Performance Monitor")
        
        # Create real-time charts
        perf_chart = create_real_time_dashboard(monitor, df1, df2)
        if perf_chart:
            st.plotly_chart(perf_chart, use_container_width=True)
        else:
            st.info("Collecting performance data... Refresh in a few seconds.")
        
        # Current performance metrics
        if len(monitor.performance_log) > 0:
            latest_perf = list(monitor.performance_log)[-1]
            
            st.subheader("Current Performance Metrics")
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                if 'memory_percent' in latest_perf:
                    st.metric("Memory Usage", f"{latest_perf['memory_percent']:.1f}%")
            
            with col2:
                if 'cpu_percent' in latest_perf:
                    st.metric("CPU Usage", f"{latest_perf['cpu_percent']:.1f}%")
            
            with col3:
                if 'memory_used_mb' in latest_perf:
                    st.metric("Memory Used", f"{latest_perf['memory_used_mb']:.1f} MB")
            
            with col4:
                if 'session_state_size' in latest_perf:
                    st.metric("Session Keys", latest_perf['session_state_size'])
        
        # Performance alerts
        if len(monitor.performance_log) > 5:
            recent_perf = list(monitor.performance_log)[-5:]
            avg_memory = sum(p.get('memory_percent', 0) for p in recent_perf) / len(recent_perf)
            avg_cpu = sum(p.get('cpu_percent', 0) for p in recent_perf) / len(recent_perf)
            
            st.subheader("Performance Alerts")
            if avg_memory > 85:
                st.error(f"High memory usage detected: {avg_memory:.1f}% average over last 5 readings")
            elif avg_memory > 75:
                st.warning(f"Elevated memory usage: {avg_memory:.1f}% average over last 5 readings")
            
            if avg_cpu > 80:
                st.error(f"High CPU usage detected: {avg_cpu:.1f}% average over last 5 readings")
            elif avg_cpu > 60:
                st.warning(f"Elevated CPU usage: {avg_cpu:.1f}% average over last 5 readings")
    
    with tab3:
        st.header("Error Tracking & Logging")
        
        # Error summary
        error_summary = defaultdict(int)
        severity_summary = defaultdict(int)
        
        for error in monitor.error_log:
            error_summary[error['type']] += 1
            severity_summary[error['severity']] += 1
        
        if error_summary:
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("Errors by Type")
                error_df = pd.DataFrame(list(error_summary.items()), columns=['Error_Type', 'Count'])
                fig_errors = px.bar(error_df, x='Error_Type', y='Count', 
                                  title='Error Distribution by Type')
                st.plotly_chart(fig_errors, use_container_width=True)
            
            with col2:
                st.subheader("Errors by Severity")
                severity_df = pd.DataFrame(list(severity_summary.items()), columns=['Severity', 'Count'])
                fig_severity = px.pie(severity_df, values='Count', names='Severity',
                                    title='Error Distribution by Severity')
                st.plotly_chart(fig_severity, use_container_width=True)
            
            # Recent errors
            st.subheader("Recent Errors (Last 10)")
            recent_errors = list(monitor.error_log)[-10:]
            
            for i, error in enumerate(reversed(recent_errors)):
                with st.expander(f"[{error['severity']}] {error['type']} - {error['timestamp'][:19]}"):
                    st.write(f"**Message:** {error['message']}")
                    st.write(f"**Timestamp:** {error['timestamp']}")
                    if error['context']:
                        st.write(f"**Context:** {error['context']}")
                    if error['stack_trace']:
                        st.code(error['stack_trace'], language='python')
        else:
            st.success("No errors logged yet!")
        
        # Manual error test
        st.subheader("Error Testing")
        if st.button("Simulate Test Error"):
            try:
                # Intentionally cause an error for testing
                raise ValueError("This is a test error for monitoring")
            except Exception as e:
                monitor.log_error("Test Error", str(e), traceback.format_exc(), {"test": True})
                st.success("Test error logged successfully!")
    
    with tab4:
        st.header("Session State Analysis")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Session State Overview")
            st.metric("Total Keys", session_health['total_keys'])
            st.metric("Estimated Size", f"{session_health['memory_estimate_mb']:.2f} MB")
            
            if session_health['potential_issues']:
                st.error("Potential Issues:")
                for issue in session_health['potential_issues']:
                    st.write(f"- {issue}")
            
            if session_health['recommendations']:
                st.info("Recommendations:")
                for rec in session_health['recommendations']:
                    st.write(f"- {rec}")
        
        with col2:
            st.subheader("Large Objects")
            if session_health['large_objects']:
                large_obj_df = pd.DataFrame(session_health['large_objects'])
                st.dataframe(large_obj_df, use_container_width=True)
            else:
                st.success("No large objects detected")
        
        # Session state cleanup
        st.subheader("Session State Management")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("Clear Large Objects"):
                keys_to_remove = [obj['key'] for obj in session_health['large_objects']]
                for key in keys_to_remove:
                    if key in st.session_state:
                        del st.session_state[key]
                st.success(f"Removed {len(keys_to_remove)} large objects")
                st.rerun()
        
        with col2:
            if st.button("Clear All Session Data"):
                st.session_state.clear()
                st.success("All session data cleared")
                st.rerun()
        
        with col3:
            if st.button("Refresh Analysis"):
                st.rerun()
    
    with tab5:
        st.header("System Diagnostics")
        
        # Environment information
        st.subheader("Environment Information")
        try:
            env_info = {
                'Python Version': sys.version,
                'Streamlit Version': st.__version__,
                'Platform': sys.platform,
                'Available Memory': f"{psutil.virtual_memory().total / 1024 / 1024 / 1024:.2f} GB",
                'CPU Count': psutil.cpu_count()
            }
            
            for key, value in env_info.items():
                st.write(f"**{key}:** {value}")
        except Exception as e:
            st.error(f"Error getting environment info: {str(e)}")
        
        # Package versions
        st.subheader("Key Package Versions")
        try:
            package_versions = {
                'pandas': pd.__version__,
                'plotly': px.__version__ if hasattr(px, '__version__') else 'Unknown',
                'numpy': np.__version__
            }
            
            for package, version in package_versions.items():
                st.write(f"**{package}:** {version}")
        except Exception as e:
            st.error(f"Error getting package versions: {e}")
        
        # Export system report
        st.subheader("Export System Report")
        if st.button("Generate System Report"):
            try:
                system_report = {
                    'timestamp': datetime.now().isoformat(),
                    'environment': env_info if 'env_info' in locals() else {},
                    'session_health': session_health,
                    'integrity_report': integrity_report,
                    'recent_errors': list(monitor.error_log)[-20:],  # Last 20 errors
                    'performance_log': list(monitor.performance_log)[-20:]  # Last 20 snapshots
                }
                
                report_json = json.dumps(system_report, indent=2, default=str)
                st.download_button(
                    label="Download System Report",
                    data=report_json,
                    file_name=f"system_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                    mime="application/json"
                )
            except Exception as e:
                st.error(f"Error generating system report: {str(e)}")