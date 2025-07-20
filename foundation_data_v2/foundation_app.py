import streamlit as st
import pandas as pd
import os

from .panels.hierarchy_panel_fixed import show_hierarchy_panel
from .panels.enhanced_validation_panel import show_validation_panel
from .panels.statistics_panel import show_statistics_panel
from .panels.dashboard_panel import show_dashboard_panel
from .config_manager import show_admin_panel




# Configure page with improved layout settings
st.set_page_config(
    page_title="Org Hierarchy Visual Explorer v2.4",
    page_icon="📊",
    layout="centered",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': 'https://example.com/help',
        'Report a bug': "https://example.com/bug",
        'About': "### Org Hierarchy Visual Explorer v2.4\n\nIncludes new Admin Configuration features and Enhanced Statistics"
    }
)

import pandas as pd
from panels.hierarchy_panel_fixed import show_hierarchy_panel

# Import enhanced validation panel with fallback
try:
    from panels.enhanced_validation_panel import show_validation_panel
    VALIDATION_ENHANCED = True
except ImportError:
    # Fallback to original validation panel
    try:
        from panels.validation_panel_fixed import show_validation_panel
        VALIDATION_ENHANCED = False
        st.warning("Using basic validation panel. Enhanced version not found.")
    except ImportError:
        def show_validation_panel(state):
            st.title("Validation Panel")
            st.error("Validation panel not implemented yet")
            st.info("This panel is under development")
        VALIDATION_ENHANCED = False

# Import admin panel with fallbacks
try:
    from config_manager import show_admin_panel
except ImportError:
    # Fallback if config_manager is in panels folder
    try:
        from panels.config_manager import show_admin_panel
    except ImportError:
        def show_admin_panel():
            st.error("Admin panel not found. Please ensure config_manager.py exists.")
            st.info("Create config_manager.py or place it in the panels/ folder")

# Import enhanced statistics panel with fallbacks
try:
    from panels.statistics_panel_enhanced import show_statistics_panel
    STATISTICS_ENHANCED = True
except ImportError:
    # Fallback to original statistics panel
    try:
        from panels.statistics_panel import show_statistics_panel
        STATISTICS_ENHANCED = False
        st.warning("Explore enhanced statistics to know your data!")
    except ImportError:
        def show_statistics_panel(state):
            st.title("Statistics Panel") 
            st.error("Statistics panel not implemented yet")
            st.info("This panel is under development")
        STATISTICS_ENHANCED = False

# Import other panels with fallbacks for missing panels
try:
    from panels.transformation_panel import show_transformation_panel, TransformationLogger
except ImportError:
    def show_transformation_panel(state):
        st.title("Transformation Panel")
        st.error("Transformation panel not implemented yet")
        st.info("This panel is under development")
    
    class TransformationLogger:
        def __init__(self):
            self.logs = []

try:
    from panels.dashboard_panel_fixed import show_dashboard_panel
    DASHBOARD_ENHANCED = True
except ImportError:
    # Try regular dashboard panel
    try:
        from panels.dashboard_panel import show_dashboard_panel
        DASHBOARD_ENHANCED = False
    except ImportError:
        def show_dashboard_panel(state):
            st.title("Dashboard Panel")
            st.error("Dashboard panel not implemented yet") 
            st.info("This panel is under development")
        DASHBOARD_ENHANCED = False

# Custom CSS for better display
st.markdown("""
    <style>
        .stDataFrame {
            width: 100% !important;
        }
        .stDataFrame div[data-testid="stHorizontalBlock"] {
            overflow-x: auto;
        }
        .stDataFrame table {
            width: 100%;
            font-size: 14px;
        }
        .stDataFrame th {
            font-weight: bold !important;
            background-color: #f0f2f6 !important;
        }
        .stDataFrame td {
            white-space: nowrap;
            max-width: 300px;
            overflow: hidden;
            text-overflow: ellipsis;
        }
        .css-1v0mbdj {
            max-width: 100%;
        }
        .block-container {
            padding-top: 2rem;
            padding-bottom: 2rem;
            max-width: 1200px;
        }
        .stButton>button {
            width: 100%;
        }
        .stDownloadButton>button {
            width: 100%;
        }
        .admin-section {
            background-color: #f8f9fa;
            padding: 1rem;
            border-radius: 0.5rem;
            border-left: 4px solid #ff4b4b;
            margin-bottom: 1rem;
        }
        .missing-panel {
            background-color: #fff3cd;
            border: 1px solid #ffeaa7;
            padding: 1rem;
            border-radius: 0.5rem;
            border-left: 4px solid #f39c12;
        }
        .enhanced-panel {
            background-color: #e8f5e8;
            border: 1px solid #90ee90;
            padding: 1rem;
            border-radius: 0.5rem;
            border-left: 4px solid #22c55e;
        }
        .statistics-status {
            background: linear-gradient(90deg, #3b82f6, #8b5cf6);
            color: white;
            padding: 10px;
            border-radius: 8px;
            text-align: center;
            margin: 10px 0;
            font-weight: bold;
        }
        .validation-status {
            background: linear-gradient(90deg, #ef4444, #f59e0b);
            color: white;
            padding: 10px;
            border-radius: 8px;
            text-align: center;
            margin: 10px 0;
            font-weight: bold;
        }
        .dashboard-status {
            background: linear-gradient(90deg, #8b5cf6, #3b82f6);
            color: white;
            padding: 10px;
            border-radius: 8px;
            text-align: center;
            margin: 10px 0;
            font-weight: bold;
        }
    </style>
""", unsafe_allow_html=True)

# Initialize session state with admin config
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
        'generated_output_files': {},  # For enhanced statistics
        'output_generation_metadata': {}  # Metadata for statistics
    }

# Sidebar navigation with admin toggle
with st.sidebar:
    st.title("Navigation")
    
    # Show enhancement status for all panels
    if STATISTICS_ENHANCED:
        st.markdown('<div class="statistics-status">Enhanced Statistics Active 🚀</div>', unsafe_allow_html=True)
        st.caption("End-to-end pipeline analysis available")
    else:
        st.warning("Basic Statistics Mode")
        st.caption("Enhanced pipeline analysis not available")
    
    if VALIDATION_ENHANCED:
        st.markdown('<div class="validation-status">Enhanced Validation Active 🔍</div>', unsafe_allow_html=True)
        st.caption("Complete pipeline validation available")
    else:
        st.warning("Basic Validation Mode")
        st.caption("Enhanced pipeline validation not available")
    
    if DASHBOARD_ENHANCED:
        st.markdown('<div class="dashboard-status">Enhanced Dashboard Active 📊</div>', unsafe_allow_html=True)
        st.caption("Output file analysis available")
    else:
        st.warning("Basic Dashboard Mode")
        st.caption("Output file analysis not available")
    
    # Admin mode toggle
    admin_enabled = st.checkbox("Admin Mode", help="Enable configuration options")
    
    if admin_enabled:
        # Check if running locally or if admin password is configured
        try:
            # Try to get admin password from secrets
            admin_password = st.secrets.get("admin_password", "")
            if admin_password:
                entered_pw = st.text_input("Admin Password", type="password")
                if entered_pw == admin_password:
                    st.session_state.state['admin_mode'] = True
                    st.success("Admin mode activated")
                elif entered_pw:
                    st.error("Incorrect password")
                    st.session_state.state['admin_mode'] = False
                else:
                    st.session_state.state['admin_mode'] = False
            else:
                # No password configured - allow admin mode (development)
                st.session_state.state['admin_mode'] = True
                st.info("Admin mode (no password configured)")
        except Exception:
            # Fallback for local development
            st.session_state.state['admin_mode'] = True
            st.info("Admin mode (local development)")
    else:
        st.session_state.state['admin_mode'] = False
    
    # Show current data status
    st.divider()
    st.subheader("Data Status")
    
    # Check data status
    hrp1000_loaded = 'source_hrp1000' in st.session_state.state and st.session_state.state['source_hrp1000'] is not None
    hrp1001_loaded = 'source_hrp1001' in st.session_state.state and st.session_state.state['source_hrp1001'] is not None
    hierarchy_processed = 'hierarchy_structure' in st.session_state.state and st.session_state.state['hierarchy_structure'] is not None
    output_generated = 'generated_output_files' in st.session_state.state and st.session_state.state['generated_output_files']
    
    if hrp1000_loaded:
        st.success("HRP1000 Loaded")
        st.caption(f"{len(st.session_state.state['source_hrp1000']):,} records")
    else:
        st.error("HRP1000 Missing")
    
    if hrp1001_loaded:
        st.success("HRP1001 Loaded") 
        st.caption(f"{len(st.session_state.state['source_hrp1001']):,} records")
    else:
        st.error("HRP1001 Missing")
    
    if hierarchy_processed:
        st.success("Hierarchy Processed")
        max_level = max([info.get('level', 1) for info in st.session_state.state['hierarchy_structure'].values()]) if st.session_state.state['hierarchy_structure'] else 0
        st.caption(f"{max_level} levels")
    else:
        st.warning("Hierarchy Pending")
    
    # Enhanced: Show output file status for statistics
    if output_generated:
        level_files = st.session_state.state['generated_output_files'].get('level_files', {})
        association_files = st.session_state.state['generated_output_files'].get('association_files', {})
        st.success("Output Files Generated")
        st.caption(f"{len(level_files)} level + {len(association_files)} association files")
        if STATISTICS_ENHANCED:
            st.info("🔍 Ready for pipeline analysis")
        if VALIDATION_ENHANCED:
            st.info("🔍 Ready for complete validation")
        if DASHBOARD_ENHANCED:
            st.info("📊 Ready for output analysis")
    else:
        st.warning("Output Files Pending")
        if STATISTICS_ENHANCED or VALIDATION_ENHANCED or DASHBOARD_ENHANCED:
            st.caption("Generate files for full analysis")
    
    st.divider()
    
    # Main navigation
    if st.session_state.state['admin_mode']:
        panel_options = ["Admin", "Hierarchy", "Validation", "Transformation", "Statistics", "Dashboard"]
    else:
        panel_options = ["Hierarchy", "Validation", "Transformation", "Statistics", "Dashboard"]
    
    panel = st.radio(
        "Go to",
        panel_options,
        label_visibility="collapsed"
    )

# Main content
st.title("Org Hierarchy Visual Explorer v2.4")

# Show welcome message for first-time users
if not hrp1000_loaded and not hrp1001_loaded:
    st.markdown("""
    ### Welcome to the Organizational Hierarchy Visual Explorer!
    
    **Getting Started:**
    1. **Upload Data**: Go to the Hierarchy panel to upload your HRP1000 and HRP1001 files
    2. **Process**: Process your organizational structure 
    3. **Validate**: Check data quality in the Validation panel
    4. **Generate**: Create output files for your target system
    5. **Analyze**: Use Statistics panel for end-to-end pipeline analysis
    
    **Enhanced Features:**
    - **🔍 Enhanced Validation**: Complete pipeline validation with drill-down details
    - **📊 Enhanced Statistics**: Complete pipeline analysis from source to target
    - **📊 Enhanced Dashboard**: Output file analysis and system monitoring
    - **🔧 Data Lineage**: Track transformations at column level
    - **📋 Quality Metrics**: Before/after transformation analysis
    
    **Need Help?** 
    - Use the **Admin panel** to configure templates and mappings
    - Check the **Validation panel** for comprehensive data quality analysis
    - Visit **Statistics** for comprehensive pipeline insights
    - Monitor system health in the **Dashboard**
    """)
    
    # Show feature highlights
    col1, col2, col3 = st.columns(3)
    
    with col1:
        enhancement_text = "🚀 Enhanced" if VALIDATION_ENHANCED else "📋 Basic"
        st.info(f"**{enhancement_text} Validation**\nComplete pipeline validation")
    
    with col2:
        enhancement_text = "🚀 Enhanced" if STATISTICS_ENHANCED else "📊 Basic"
        st.info(f"**{enhancement_text} Statistics**\nEnd-to-end pipeline analysis")
    
    with col3:
        enhancement_text = "🚀 Enhanced" if DASHBOARD_ENHANCED else "📊 Basic"
        st.info(f"**{enhancement_text} Dashboard**\nSystem and output monitoring")

# Panel routing with enhanced error handling
try:
    if panel == "Admin" and st.session_state.state['admin_mode']:
        st.markdown("<div class='admin-section'>", unsafe_allow_html=True)
        st.header("Admin Configuration Center")
        show_admin_panel()
        st.markdown("</div>", unsafe_allow_html=True)
        
    elif panel == "Hierarchy":
        show_hierarchy_panel(st.session_state.state)
        
    elif panel == "Validation":
        if VALIDATION_ENHANCED:
            st.markdown("<div class='enhanced-panel'>", unsafe_allow_html=True)
        
        try:
            show_validation_panel(st.session_state.state)
        except Exception as e:
            st.error(f"Error in Validation panel: {str(e)}")
            
            # Enhanced troubleshooting for validation
            st.subheader("Validation Panel Troubleshooting")
            
            if not VALIDATION_ENHANCED:
                st.warning("**Enhanced Validation Not Available**")
                st.info("For complete pipeline validation, ensure you have the enhanced validation panel.")
            
            st.info("**Troubleshooting Steps:**")
            st.write("1. Ensure enhanced_validation_panel.py exists in panels/ folder")
            st.write("2. Check that source data is loaded (HRP1000, HRP1001)")
            st.write("3. Verify all required methods are implemented")
            
            with st.expander("Debug Information", expanded=True):
                st.write("**Error Details:**")
                st.code(f"Error Type: {type(e).__name__}\nError Message: {str(e)}")
        
        if VALIDATION_ENHANCED:
            st.markdown("</div>", unsafe_allow_html=True)
        
    elif panel == "Transformation":
        st.markdown("<div class='missing-panel'>", unsafe_allow_html=True)
        show_transformation_panel(st.session_state.state)
        st.markdown("</div>", unsafe_allow_html=True)
    
    elif panel == "Statistics":
        if STATISTICS_ENHANCED:
            st.markdown("<div class='enhanced-panel'>", unsafe_allow_html=True)
        
        try:
            show_statistics_panel(st.session_state.state)
        except Exception as e:
            st.error(f"Error in Statistics panel: {str(e)}")
            
            # Enhanced troubleshooting for statistics
            st.subheader("Statistics Panel Troubleshooting")
            
            if not STATISTICS_ENHANCED:
                st.warning("**Enhanced Statistics Not Available**")
                st.info("For full pipeline analysis, ensure you have the enhanced statistics panel.")
            
            st.info("**Troubleshooting Steps:**")
            st.write("1. Ensure source data is loaded (HRP1000, HRP1001)")
            st.write("2. Process hierarchy in the Hierarchy panel")
            st.write("3. Generate output files in the Hierarchy panel")
            st.write("4. Check that all required data is available below")
            
            # Enhanced debug info
            with st.expander("Detailed Debug Information", expanded=True):
                st.write("**Session State Overview:**")
                
                # Show what statistics panel expects
                expected_keys = [
                    ('source_hrp1000', 'Source HRP1000 data'),
                    ('source_hrp1001', 'Source HRP1001 data'), 
                    ('hierarchy_structure', 'Processed hierarchy'),
                    ('generated_output_files', 'Generated level/association files'),
                    ('mapping_config', 'Column mapping configuration'),
                    ('output_generation_metadata', 'File generation metadata')
                ]
                
                st.write("**Required Data for Full Analysis:**")
                for key, description in expected_keys:
                    if key in st.session_state.state and st.session_state.state[key] is not None:
                        value = st.session_state.state[key]
                        if isinstance(value, pd.DataFrame):
                            st.success(f"✓ {description}: DataFrame ({len(value)} rows)")
                        elif isinstance(value, dict):
                            if key == 'generated_output_files':
                                level_count = len(value.get('level_files', {}))
                                assoc_count = len(value.get('association_files', {}))
                                if level_count > 0 or assoc_count > 0:
                                    st.success(f"✓ {description}: {level_count} level files, {assoc_count} association files")
                                else:
                                    st.warning(f"⚠️ {description}: Available but empty")
                            else:
                                st.success(f"✓ {description}: Dict ({len(value)} items)")
                        else:
                            st.success(f"✓ {description}: Available ({type(value).__name__})")
                    else:
                        st.error(f"✗ {description}: Missing")
                
                # Show available keys
                st.write("**All Available Session State Keys:**")
                available_keys = list(st.session_state.state.keys())
                st.code(str(available_keys))
                
                # Show error details
                st.write("**Error Details:**")
                st.code(f"Error Type: {type(e).__name__}\nError Message: {str(e)}")
        
        if STATISTICS_ENHANCED:
            st.markdown("</div>", unsafe_allow_html=True)
        
    elif panel == "Dashboard":
        if DASHBOARD_ENHANCED:
            st.markdown("<div class='enhanced-panel'>", unsafe_allow_html=True)
        else:
            st.markdown("<div class='missing-panel'>", unsafe_allow_html=True)
        
        try:
            show_dashboard_panel(st.session_state.state)
        except Exception as e:
            st.error(f"Error in Dashboard panel: {str(e)}")
            
            if not DASHBOARD_ENHANCED:
                st.warning("**Enhanced Dashboard Not Available**")
                st.info("For output file analysis, ensure you have the enhanced dashboard panel.")
            
            with st.expander("Debug Information", expanded=True):
                st.write("**Error Details:**")
                st.code(f"Error Type: {type(e).__name__}\nError Message: {str(e)}")
        
        if DASHBOARD_ENHANCED:
            st.markdown("</div>", unsafe_allow_html=True)
        else:
            st.markdown("</div>", unsafe_allow_html=True)
        
except Exception as e:
    st.error(f"Error loading {panel} panel: {str(e)}")
    st.info("Please check that all required panel files exist and are properly configured")
    
    # Show debug information in admin mode
    if st.session_state.state['admin_mode']:
        with st.expander("Debug Information"):
            st.write(f"**Panel:** {panel}")
            st.write(f"**Error:** {str(e)}")
            st.write(f"**Error Type:** {type(e).__name__}")
            
            # Import status
            st.write("**Panel Import Status:**")
            panel_imports = {
                "Admin": "config_manager",
                "Hierarchy": "panels.hierarchy_panel_fixed", 
                "Validation": "panels.enhanced_validation_panel" if VALIDATION_ENHANCED else "panels.validation_panel_fixed",
                "Statistics": "panels.statistics_panel_enhanced" if STATISTICS_ENHANCED else "panels.statistics_panel",
                "Transformation": "panels.transformation_panel",
                "Dashboard": "panels.dashboard_panel_fixed" if DASHBOARD_ENHANCED else "panels.dashboard_panel"
            }
            
            for panel_name, import_path in panel_imports.items():
                try:
                    __import__(import_path)
                    st.success(f"✓ {panel_name}: {import_path}")
                except ImportError as ie:
                    st.error(f"✗ {panel_name}: {import_path} - {str(ie)}")

# Footer with status information
st.divider()
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
    # Show enhancement status
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
    # Show current pipeline status
    if output_generated:
        st.markdown(
            "<div style='text-align: center; color: #3b82f6; font-weight: bold;'>PIPELINE READY</div>",
            unsafe_allow_html=True
        )
    elif hierarchy_processed:
        st.markdown(
            "<div style='text-align: center; color: #f59e0b;'>GENERATE FILES</div>",
            unsafe_allow_html=True
        )
    else:
        st.markdown(
            "<div style='text-align: center; color: #6b7280;'>LOAD DATA</div>",
            unsafe_allow_html=True
        )

# Quick stats in sidebar footer
with st.sidebar:
    st.divider()
    st.caption("**System Status**")
    
    # Show quick metrics
    if hrp1000_loaded and hrp1001_loaded:
        source_total = len(st.session_state.state['source_hrp1000']) + len(st.session_state.state['source_hrp1001'])
        st.caption(f"📊 Source: {source_total:,} total records")
    
    if output_generated:
        metadata = st.session_state.state.get('output_generation_metadata', {})
        if metadata:
            total_files = metadata.get('total_level_files', 0) + metadata.get('total_association_files', 0)
            st.caption(f"📁 Output: {total_files} files generated")
            
            # Show generation time
            gen_time = metadata.get('generated_at', '')
            if gen_time:
                from datetime import datetime
                try:
                    gen_dt = datetime.fromisoformat(gen_time)
                    time_diff = datetime.now() - gen_dt
                    if time_diff.seconds < 60:
                        time_ago = "Just now"
                    elif time_diff.seconds < 3600:
                        time_ago = f"{time_diff.seconds // 60}m ago"
                    else:
                        time_ago = f"{time_diff.seconds // 3600}h ago"
                    st.caption(f"⏱️ Generated: {time_ago}")
                except:
                    st.caption(f"⏱️ Generated: Recently")
    
    # Show enhancement status
    enhancement_count = sum([STATISTICS_ENHANCED, VALIDATION_ENHANCED, DASHBOARD_ENHANCED])
    if enhancement_count > 0:
        st.caption(f"🚀 {enhancement_count}/3 panels enhanced!")
def render_foundation_v2():
    # Rerun the full file by calling main content here.
    pass

