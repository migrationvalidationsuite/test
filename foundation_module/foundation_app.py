import streamlit as st
import pandas as pd
import os
import sys
import json
from datetime import datetime

# Append root directory to sys.path for absolute imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# ✅ FIXED IMPORTS
from foundation_module.panels.hierarchy_panel import show_hierarchy_panel
from foundation_module.panels.transformation_panel import show_transformation_panel
from foundation_module.panels.validation_panel import show_validation_panel
from foundation_module.panels.statistics_panel import show_statistics_panel
from foundation_module.panels.dashboard_panel import show_dashboard_panel
from foundation_module.panels.transformation_logger import TransformationLogger


def render():
    st.markdown("""
        <style>
            .stDataFrame { width: 100% !important; }
            .stDataFrame div[data-testid="stHorizontalBlock"] { overflow-x: auto; }
            .stDataFrame table { width: 100%; font-size: 14px; }
            .stDataFrame th { font-weight: bold !important; background-color: #f0f2f6 !important; }
            .stDataFrame td { white-space: nowrap; max-width: 300px; overflow: hidden; text-overflow: ellipsis; }
            .block-container { padding-top: 2rem; padding-bottom: 2rem; max-width: 1200px; }
            .stButton>button, .stDownloadButton>button { width: 100%; }
        </style>
    """, unsafe_allow_html=True)

    # Initialize session state
    if 'state' not in st.session_state:
        st.session_state.state = {
            'hrp1000': None,
            'hrp1001': None,
            'hierarchy': None,
            'level_names': {i: f"Level {i}" for i in range(1, 21)},
            'transformations': [],
            'validation_results': None,
            'statistics': None,
            'transformation_log': TransformationLogger(),
            'pending_transforms': []
        }

    # Local Sidebar Navigation
    with st.sidebar:
        st.markdown("### Foundation Module")
        panel = st.radio(
            "Go to",
            ["Hierarchy", "Transformation", "Validation", "Statistics", "Dashboard"],
            label_visibility="collapsed",
            key="foundation_nav"
        )

    st.title("Org Hierarchy Visual Explorer v2.3")

    if panel == "Hierarchy":
        show_hierarchy_panel(st.session_state.state)
    elif panel == "Transformation":
        show_transformation_panel(st.session_state.state)
    elif panel == "Validation":
        show_validation_panel(st.session_state.state)
    elif panel == "Statistics":
        show_statistics_panel(st.session_state.state)
    elif panel == "Dashboard":
        show_dashboard_panel(st.session_state.state)
