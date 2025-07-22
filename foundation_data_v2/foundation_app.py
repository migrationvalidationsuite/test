import streamlit as st
import pandas as pd
import os

# ✅ Panel imports with fallbacks
from .panels.hierarchy_panel_fixed import show_hierarchy_panel

# ✅ Validation panel fallback
try:
    from .panels.enhanced_validation_panel import show_validation_panel
    VALIDATION_ENHANCED = True
except ImportError:
    try:
        from .panels.validation_panel_fixed import show_validation_panel
        VALIDATION_ENHANCED = False
        st.warning("Using basic validation panel. Enhanced version not found.")
    except ImportError:
        def show_validation_panel(state):
            st.title("Validation Panel")
            st.error("Validation panel not implemented yet")
            st.info("This panel is under development")
        VALIDATION_ENHANCED = False

# ✅ Admin panel fallback
try:
    from foundation_data_v2.config_manager import show_admin_panel
except ImportError:
    try:
        from .config_manager import show_admin_panel
    except ImportError:
        def show_admin_panel(state=None):
            st.error("Admin panel not found. Please ensure config_manager.py exists.")
            st.info("Create config_manager.py or place it in the panels/ folder")

# Statistics panel fallback
try:
    from .panels.statistics_panel_enhanced import show_statistics_panel
    STATISTICS_ENHANCED = True
except ImportError:
    try:
        from .panels.statistics_panel import show_statistics_panel
        STATISTICS_ENHANCED = False
        st.warning("Explore enhanced statistics to know your data!")
    except ImportError:
        def show_statistics_panel(state):
            st.title("Statistics Panel")
            st.error("Statistics panel not implemented yet")
            st.info("This panel is under development")
        STATISTICS_ENHANCED = False
# Transformation panel fallback
try:
    from .panels.transformation_panel import show_transformation_panel, TransformationLogger
except ImportError:
    def show_transformation_panel(state):
        st.title("Transformation Panel")
        st.error("Transformation panel not implemented yet")
        st.info("This panel is under development")
    
    class TransformationLogger:
        def __init__(self):
            self.logs = []

# Dashboard panel fallback
try:
    from .panels.dashboard_panel_fixed import show_dashboard_panel
    DASHBOARD_ENHANCED = True
except ImportError:
    try:
        from .panels.dashboard_panel import show_dashboard_panel
        DASHBOARD_ENHANCED = False
    except ImportError:
        def show_dashboard_panel(state):
            st.title("Dashboard Panel")
            st.error("Dashboard panel not implemented yet")
            st.info("This panel is under development")
        DASHBOARD_ENHANCED = False

# Custom CSS
st.markdown("""
<style>
.block-container { padding-top: 0.5rem !important; }
@media (max-width: 768px) {
    .block-container { padding-left: 1rem; padding-right: 1rem; }
}
.stDataFrame table { width: 100%; font-size: 14px; }
.stDataFrame th { font-weight: bold !important; background-color: #f0f2f6 !important; }
.stDataFrame td { white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.stButton>button, .stDownloadButton>button { width: 100%; }
.admin-section {
    background-color: #f8f9fa; padding: 1rem; border-radius: 0.5rem;
    border-left: 4px solid #ff4b4b; margin-bottom: 1rem;
}
.missing-panel {
    background-color: #fff3cd; border: 1px solid #ffeaa7; padding: 1rem;
    border-radius: 0.5rem; border-left: 4px solid #f39c12;
}
.enhanced-panel {
    background-color: #e8f5e8; border: 1px solid #90ee90; padding: 1rem;
    border-radius: 0.5rem; border-left: 4px solid #22c55e;
}
.statistics-status {
    background: linear-gradient(90deg, #3b82f6, #8b5cf6); color: white;
    padding: 10px; border-radius: 8px; text-align: center; margin: 10px 0;
    font-weight: bold;
}
.validation-status {
    background: linear-gradient(90deg, #ef4444, #f59e0b); color: white;
    padding: 10px; border-radius: 8px; text-align: center; margin: 10px 0;
    font-weight: bold;
}
.dashboard-status {
    background: linear-gradient(90deg, #8b5cf6, #3b82f6); color: white;
    padding: 10px; border-radius: 8px; text-align: center; margin: 10px 0;
    font-weight: bold;
}
</style>
""", unsafe_allow_html=True)
# ✅ Initialize session state
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
        'pending_transforms': [],
        'admin_mode': False,
        'generated_output_files': {},
        'output_generation_metadata': {}
    }
back_col, _ = st.columns([1, 6])
with back_col:
    if st.button("⬅ Back to Demo", key="back_from_foundation", use_container_width=True):
        st.session_state.demo_page = "sap_to_sf"
        st.session_state.tool_subpage = "Tool"
        st.rerun()

# ✅ Foundation embedded rendering (used from app.py)
def render_foundation_v2():
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
            'pending_transforms': [],
            'admin_mode': False,
            'generated_output_files': {},
            'output_generation_metadata': {}
        }

    st.title("Org Hierarchy Visual Explorer v2.4")
    
    with st.sidebar:
        if st.button("⬅ Back to Migration Options"):
            st.session_state.demo_page = "sap_to_sf"
            st.rerun()

    
        st.markdown("---")
        st.title("Navigation")
    
        if STATISTICS_ENHANCED:
            st.markdown('<div class="statistics-status">Enhanced Statistics Active 🚀</div>', unsafe_allow_html=True)
        else:
            st.warning("Basic Statistics Mode")
    
        if VALIDATION_ENHANCED:
            st.markdown('<div class="validation-status">Enhanced Validation Active 🔍</div>', unsafe_allow_html=True)
        else:
            st.warning("Basic Validation Mode")
    
        if DASHBOARD_ENHANCED:
            st.markdown('<div class="dashboard-status">Enhanced Dashboard Active 📊</div>', unsafe_allow_html=True)
        else:
            st.warning("Basic Dashboard Mode")
    
        admin_toggle = st.checkbox(
            "Admin Mode",
            help="Enable configuration panel",
            key=f"foundation_admin_toggle_{st.session_state.get('demo_page', 'unknown')}"
        )

        if admin_toggle:
            try:
                admin_pw = st.secrets.get("admin_password", "")
                if admin_pw:
                    entered_pw = st.text_input("Admin Password", type="password")
                    if entered_pw == admin_pw:
                        st.session_state.state["admin_mode"] = True
                        st.success("Admin mode activated")
                    elif entered_pw:
                        st.error("Incorrect password")
                        st.session_state.state["admin_mode"] = False
                else:
                    st.session_state.state["admin_mode"] = True
                    st.info("Admin mode (no password configured)")
            except Exception:
                st.session_state.state["admin_mode"] = True
                st.info("Admin mode (local dev)")
        else:
            st.session_state.state["admin_mode"] = False

        panel_options = ["Hierarchy", "Validation", "Transformation", "Statistics", "Dashboard"]
        if st.session_state.state.get("admin_mode"):
            panel_options.insert(0, "Admin")

        panel = st.radio("Select Panel", panel_options, key="foundation_panel_radio_inline")

    # ✅ Panel routing
    try:
        if panel == "Admin":
            st.markdown("<div class='admin-section'>", unsafe_allow_html=True)
            st.header("Admin Configuration Center")
            show_admin_panel(st.session_state.state) 
            st.markdown("</div>", unsafe_allow_html=True)

        elif panel == "Hierarchy":
            show_hierarchy_panel(st.session_state.state)

        elif panel == "Validation":
            if VALIDATION_ENHANCED:
                st.markdown("<div class='enhanced-panel'>", unsafe_allow_html=True)
            show_validation_panel(st.session_state.state)
            if VALIDATION_ENHANCED:
                st.markdown("</div>", unsafe_allow_html=True)

        elif panel == "Transformation":
            st.markdown("<div class='missing-panel'>", unsafe_allow_html=True)
            show_transformation_panel(st.session_state.state)
            st.markdown("</div>", unsafe_allow_html=True)

        elif panel == "Statistics":
            if STATISTICS_ENHANCED:
                st.markdown("<div class='enhanced-panel'>", unsafe_allow_html=True)
            show_statistics_panel(st.session_state.state)
            if STATISTICS_ENHANCED:
                st.markdown("</div>", unsafe_allow_html=True)

        elif panel == "Dashboard":
            if DASHBOARD_ENHANCED:
                st.markdown("<div class='enhanced-panel'>", unsafe_allow_html=True)
            else:
                st.markdown("<div class='missing-panel'>", unsafe_allow_html=True)
            show_dashboard_panel(st.session_state.state)
            st.markdown("</div>", unsafe_allow_html=True)

    except Exception as e:
        st.error(f"Unexpected error in {panel} panel: {e}")
        with st.expander("Debug Info"):
            st.code(f"{type(e).__name__}: {str(e)}")

    # ✅ Status Footer Grid
    col1, col2, col3 = st.columns(3)

    with col1:
        if st.session_state.state['admin_mode']:
            st.markdown(
                "<div style='text-align: center; color: #ff4b4b; font-weight: bold;'>ADMIN MODE ACTIVE</div>",
                unsafe_allow_html=True
            )
        else:
            st.markdown(
                "<div style='text-align: center; color: #6b7280;'>User Mode</div>",
                unsafe_allow_html=True
            )

    with col2:
        enhancements = []
        if STATISTICS_ENHANCED:
            enhancements.append("Stats")
        if VALIDATION_ENHANCED:
            enhancements.append("Validation")
        if DASHBOARD_ENHANCED:
            enhancements.append("Dashboard")

        if enhancements:
            st.markdown(
                f"<div style='text-align: center; color: #22c55e; font-weight: bold;'>ENHANCED: {', '.join(enhancements)}</div>",
                unsafe_allow_html=True
            )
        else:
            st.markdown(
                "<div style='text-align: center; color: #f59e0b;'>Basic Mode</div>",
                unsafe_allow_html=True
            )

    with col3:
        if st.session_state.state.get('generated_output_files'):
            st.markdown(
                "<div style='text-align: center; color: #3b82f6; font-weight: bold;'>PIPELINE READY</div>",
                unsafe_allow_html=True
            )
        elif st.session_state.state.get('hierarchy_structure'):
            st.markdown(
                "<div style='text-align: center; color: #f59e0b;'>GENERATE FILES</div>",
                unsafe_allow_html=True
            )
        else:
            st.markdown(
                "<div style='text-align: center; color: #6b7280;'>LOAD DATA</div>",
                unsafe_allow_html=True
            )
__all__ = ["render_foundation_v2"]
