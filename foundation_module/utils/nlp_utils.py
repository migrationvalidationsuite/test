# utils/nlp_utils.py
import pandas as pd
from typing import Dict, Any

def explain_validation_error(error: Dict[str, Any]) -> str:
    """
    Generates human-readable explanations for validation errors.
    
    Args:
        error: Dictionary containing error details (Type, Message, Severity, etc.)
    
    Returns:
        str: Detailed explanation of the error
    """
    error_type = error.get('Type', 'Validation Error')
    message = error.get('Message', '')
    severity = error.get('Severity', 'Unknown')
    
    # Basic error explanations
    explanations = {
        "Missing Column": f"This error occurs when required data columns are missing. {message}",
        "Data Type Mismatch": f"The data type doesn't match what's expected. {message}",
        "Relationship Error": f"There's an issue with how data elements relate to each other. {message}",
        "Date Inconsistency": f"Dates are not in the correct format or range. {message}"
    }
    
    # Default explanation template
    default_explanation = (
        f"**{error_type}** (Severity: {severity})\n\n"
        f"**Problem:** {message}\n\n"
        "This typically indicates a data quality issue that needs to be addressed "
        "before the hierarchy can be properly built."
    )
    
    return explanations.get(error_type, default_explanation)

def generate_llm_explanation(error: Dict[str, Any]) -> str:
    """
    Placeholder for LLM-powered explanation (can be implemented later)
    """
    return explain_validation_error(error)  # Falls back to basic explanation