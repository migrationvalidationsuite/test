import streamlit as st
import pandas as pd
import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import re
from foundation_module.utils.validation_utils import validate_data
from foundation_module.utils.nlp_utils import explain_validation_error, generate_llm_explanation

def show_validation_panel(state):
    st.header("Data Validation Center")
    
    # Check if data is loaded
    if state.get('hrp1000') is None or state.get('hrp1001') is None:
        st.warning("Please load and build the hierarchy first")
        return
    
    if st.button("Run Full Validation"):
        with st.spinner("Validating data..."):
            try:
                results = validate_data(state['hrp1000'], state['hrp1001'])
                state['validation_results'] = results
                
                col1, col2 = st.columns(2)
                with col1:
                    st.subheader("Validation Summary")
                    st.metric("Total Errors", results.get('error_count', 0))
                    st.metric("Total Warnings", results.get('warning_count', 0))
                    
                with col2:
                    st.subheader("Data Lineage")
                    st.graphviz_chart("""
                        digraph {
                            "HRP1000" -> "Hierarchy"
                            "HRP1001" -> "Hierarchy"
                            "Hierarchy" -> "Statistics"
                            "Hierarchy" -> "Dashboard"
                        }
                    """)
            except Exception as e:
                st.error(f"Validation failed: {str(e)}")
                state['validation_results'] = {
                    'errors': [{
                        'Type': 'Validation Error',
                        'Message': f"Validation process failed: {str(e)}",
                        'Severity': 'Critical'
                    }],
                    'warnings': [],
                    'error_count': 1,
                    'warning_count': 0
                }
    
    if state.get('validation_results'):
        tab1, tab2, tab3 = st.tabs(["Errors", "Warnings", "Chat Assistant"])
        
        with tab1:
            errors = state['validation_results'].get('errors', [])
            if errors:
                st.write(f"Found {len(errors)} errors:")
                for error in errors:
                    with st.expander(f"{error.get('Type', 'Error')}: {error.get('Message', 'Unknown error')}"):
                        st.write(f"**Severity**: {error.get('Severity', 'Unknown')}")
                        st.write("**Explanation**:")
                        st.write(explain_validation_error(error))
                        
                        if 'Object ID' in error:
                            try:
                                obj_id = error['Object ID']
                                obj = state['hrp1000'][state['hrp1000']['Object ID'] == obj_id]
                                if not obj.empty:
                                    st.write("**Affected Object**:")
                                    st.dataframe(obj)
                            except Exception as e:
                                st.warning(f"Could not display object {obj_id}: {str(e)}")
            else:
                st.success("No errors found!")
        
        with tab2:
            warnings = state['validation_results'].get('warnings', [])
            if warnings:
                st.write(f"Found {len(warnings)} warnings:")
                for warning in warnings:
                    with st.expander(f"{warning.get('Type', 'Warning')}: {warning.get('Message', 'Unknown warning')}"):
                        st.write(f"**Severity**: {warning.get('Severity', 'Unknown')}")
                        st.write("**Explanation**:")
                        st.write(explain_validation_error(warning))
            else:
                st.success("No warnings found!")
            
        with tab3:
            st.subheader("Validation Chat Assistant")
            st.info("Ask about specific objects (e.g. 'What's wrong with 51010012?') or general validation issues")
            
            user_query = st.text_input("Your question:")
            
            if user_query:
                try:
                    # Extract object ID if mentioned
                    object_id = None
                    numbers = re.findall(r'\d+', user_query)
                    if numbers:
                        object_id = numbers[-1]  # Take last number found
                    
                    if object_id:
                        # Find matching issues
                        matching_issues = []
                        for error in state['validation_results'].get('errors', []):
                            if str(error.get('Object ID', '')) == object_id or str(error.get('Source ID', '')) == object_id:
                                matching_issues.append(error)
                        for warning in state['validation_results'].get('warnings', []):
                            if str(warning.get('Object ID', '')) == object_id or str(warning.get('Source ID', '')) == object_id:
                                matching_issues.append(warning)
                        
                        if matching_issues:
                            st.success(f"Found {len(matching_issues)} issues for object {object_id}:")
                            for issue in matching_issues:
                                with st.expander(f"{issue.get('Type', 'Issue')}: {issue.get('Message', '')}"):
                                    st.write(f"**Severity**: {issue.get('Severity', 'Unknown')}")
                                    st.write("**Explanation**:")
                                    st.write(explain_validation_error(issue))
                        else:
                            st.success(f"No validation issues found for object {object_id}")
                    else:
                        # General query
                        first_error = state['validation_results'].get('errors', [{}])[0]
                        explanation = generate_llm_explanation(first_error)
                        st.info(explanation)
                        
                except Exception as e:
                    st.error(f"Could not process query: {str(e)}")
