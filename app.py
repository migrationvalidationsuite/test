import os, sys
import streamlit as st
import base64
from streamlit_option_menu import option_menu
from foundation_module.foundation_app import render as render_foundation
from payroll import app as payroll_app
from employee_app import render_employee_tool
from employeedata.app.data_migration_tool import render_employee_v2
from config_manager import show_admin_panel

# Hide Streamlit style (footer and hamburger menu)
# 🔒 Hide Streamlit footer, menu, and header for a cleaner look
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)

if "page" not in st.session_state:
    st.session_state.page = "Home"
if "tool_subpage" not in st.session_state:
    st.session_state.tool_subpage = "Tool"

sys.path.append(os.path.abspath(os.path.dirname(__file__)))

# ✅ Page setup
st.set_page_config(layout="wide", page_title="MVS", page_icon="📊")
# 👇 Force sidebar collapse control to always show
st.markdown("""
<style>
[data-testid="collapsedControl"] {
    display: block !important;
    visibility: visible !important;
    opacity: 1 !important;
    pointer-events: all !important;
    position: fixed !important;
    bottom: 2rem !important;
    left: 1.5rem !important;
    z-index: 9999 !important;
}
</style>
""", unsafe_allow_html=True)


# ✅ CSS styling (light/dark mode fix + banner)
st.markdown("""
<style>
html, body, [class*="st-"], [class*="css"] {
    color: inherit !important;
}

section.main > div, .block-container {
    background-color: rgba(255, 255, 255, 0.9);
    padding: 1rem;
    border-radius: 10px;
    color: black;
}

@media (prefers-color-scheme: dark) {
    section.main > div, .block-container {
        background-color: rgba(0, 0, 0, 0.6) !important;
        color: white !important;
    }

    .css-6qob1r, .css-1v0mbdj, .css-10trblm, .css-1xarl3l, .css-eczf16, .css-1b0udgb {
        color: black !important;
    }
}

.full-width-banner {
    width: 100%;
    background-color: #e3f0ff;
    text-align: center;
    padding: 1.5rem 0;
    margin-bottom: 2rem;
    border-radius: 12px;
    font-size: 1.5rem;
    font-weight: bold;
}
.sub-banner {
    font-size: 1.2rem;
    font-weight: 400;
}
</style>
""", unsafe_allow_html=True)

st.markdown("""
<style>
/* Force sidebar toggle button to always be visible */
[data-testid="collapsedControl"] {
    display: block !important;
    visibility: visible !important;
    opacity: 1 !important;
    pointer-events: all !important;
}
</style>
""", unsafe_allow_html=True)

# ✅ Background image setup
def set_background(image_file):
    with open(image_file, "rb") as f:
        data = base64.b64encode(f.read()).decode()
    st.markdown(f"""
        <style>
            .stApp {{
                background: linear-gradient(rgba(255,255,255,0.85), rgba(255,255,255,0.85)),
                            url("data:image/jpeg;base64,{data}");
                background-size: cover;
                background-attachment: fixed;
                background-position: center;
            }}
        </style>
    """, unsafe_allow_html=True)

set_background("pexels-googledeepmind-17483873.jpg")

# ✅ Session state
if "selected" not in st.session_state:
    st.session_state.selected = "Home"
if "demo_page" not in st.session_state:
    st.session_state.demo_page = "main"

# ✅ Sidebar navigation
with st.sidebar:
    selected = option_menu(
        menu_title="Navigation",
        options=["Home", "Solutions", "Launch Demo"],
        icons=["house", "layers", "rocket"],
        default_index=0,
        styles={
            "container": {"padding": "5px", "background-color": "#f8f9fa"},
            "icon": {"color": "#003366", "font-size": "18px"},
            "nav-link": {
                "font-size": "16px",
                "text-align": "left",
                "margin": "5px",
                "--hover-color": "#e6f0ff",
            },
            "nav-link-selected": {"background-color": "#cfe2ff", "font-weight": "bold"},
        },
    )
    st.session_state.selected = selected

# ✅ Remove top white space
st.markdown("""
<style>
    .block-container {
        padding-top: 0.5rem !important;
    }
    @media (max-width: 768px) {
        .block-container {
            padding-left: 1rem;
            padding-right: 1rem;
        }
    }
</style>
""", unsafe_allow_html=True)


# -------------------- HOME --------------------
if selected == "Home":
    st.markdown("""
        <style>
        .full-width-banner {
            position: relative;
            left: 50%;
            right: 50%;
            margin-left: -50vw;
            margin-right: -50vw;
            width: 100vw;
            background-color: #e6f0ff;
            padding: 2rem 0;
            text-align: center;
            font-size: 1.8rem;
            font-weight: bold;
            border-radius: 0;
        }
        </style>

        <div class="full-width-banner">
            Effortless Data Migration, Done Right<br>
            <span style="font-size: 1.4rem; font-weight: normal;">MVS (Migration & Validation Suite)</span>
        </div>
    """, unsafe_allow_html=True)


    col1, col2 = st.columns([3, 2.5])
    with col1:
        st.markdown("### Enable secure, scalable, and audit-ready HR data migration across SAP landscapes")
        st.markdown("Supports Migration for SAP HCM (on-premise and cloud), SAP S/4HANA, and legacy HR systems.")
        st.markdown("**Power your transformation with:**")
        st.markdown("""
        - **Schema Mapping & Transformation**  
          Seamlessly aligns and converts source structures into SAP-ready formats across platforms.
        - **Pre-Migration Validation**  
          Identifies data issues early on through audit trials for cloud and S/4HANA adoption.
        - **Rollback & Audit-Ready Tracking**  
          Enables safe, reversible data loads with full traceability of rules, configurations, and actions.
        """)
        st.markdown("**Supported Migration Paths:**")
        st.markdown("""
        - SAP HCM → SuccessFactors  
        - SAP HCM → S/4HANA  
        - Legacy HR Systems → SAP Cloud or On-Premise
        """)

    with col2:
        st.image("pexels-divinetechygirl-1181263.jpg", use_container_width=True)
        st.video("https://youtu.be/o_PcYfH36TI")

    col1, col2 = st.columns([3, 2.5])
    with col1:
        st.markdown("### Why MVS?")
        st.markdown("""
        <p>MVS is a robust solution for orchestrating HR data migration across hybrid environments, including SAP On-Premise, S/4HANA, SuccessFactors, and legacy systems.</p>
        """, unsafe_allow_html=True)

        icons = ["data_icon.png", "check_icon.png", "chart_icon.png"]
        descriptions = [
            "Template-driven, secure transfers between systems.",
            "Detailed checks at the field level to catch issues throughout the migration process.",
            "Automated comparisons between source and target systems."
        ]

        for icon, desc in zip(icons, descriptions):
            icon_col, text_col = st.columns([1, 6])
            with icon_col:
                if os.path.exists(icon):
                    with open(icon, "rb") as f:
                        img_data = base64.b64encode(f.read()).decode()
                    st.markdown(
                        f"""<img src="data:image/png;base64,{img_data}" width="40" style="margin-top:10px;">""",
                        unsafe_allow_html=True
                    )
            with text_col:
                st.markdown(f"<p style='margin-top:18px;'>{desc}</p>", unsafe_allow_html=True)

    with col2:
        st.markdown("#### Key Capabilities:")
        st.markdown("""
        <ul>
            <li>AI-powered mapping & validation</li>
            <li>Real-time preview & profiling</li>
            <li>Cross-object and row-level validation</li>
            <li>Licensing controls & role-based access</li>
            <li>Audit logs, rollback & monitoring</li>
            <li>Designed to reduce manual effort and shorten project timelines</li>
            <li>Supports stakeholder collaboration with clear audit and status visibility</li>
            <li>Ability to easily create and manage transformation rules with an intuitive, interactive interface</li>
        </ul>
        """, unsafe_allow_html=True)

    st.markdown("""
    <div style='background-color:#002b5c;padding:40px;margin-top:50px;border-radius:10px;'>
        <h3 style='color:white;text-align:center;'>Built for SAP Cloud & On-Premise</h3>
        <p style='color:white;text-align:center;'>Our platform is designed to simplify, safeguard, and speed up your transformation journey.</p>
        <div style='display:flex;justify-content:space-around;margin-top:30px;'>
            <div style='width:30%;text-align:center;'>
                <h4 style='color:white;'>Data Migration Made Easy</h4>
                <p style='color:white;'>Supports smooth data preparation and migration for SAP environments.</p>
            </div>
            <div style='width:30%;text-align:center;'>
                <h4 style='color:white;'>Data Integrity & Compliance</h4>
                <p style='color:white;'>Field-level validation ensures readiness for audits and continuity.</p>
            </div>
            <div style='width:30%;text-align:center;'>
                <h4 style='color:white;'>Document-Ready Migrations</h4>
                <p style='color:white;'>Generate structured output files ready for upload and compliance.</p>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

# -------------------- LAUNCH DEMO --------------------
elif selected == "Launch Demo":
    if st.session_state.demo_page == "main":
        st.markdown("""
            <div style='background-color:#e6f0ff;padding:20px;border-radius:10px;margin-bottom:20px;'>
                <h2 style='text-align:center;'>🚀 Launch Pad</h2>
                <h4 style='text-align:center;'>Select a migration scenario to get started</h4>
            </div>
        """, unsafe_allow_html=True)

        col1, col2, col3 = st.columns([1, 3, 1])
        with col2:
            b1, b2, b3 = st.columns(3)

            with b1:
                if st.button("SAP HCM → SuccessFactors", key="btn_sap_sf"):
                    st.session_state.demo_page = "sap_to_sf"
                    st.rerun()  # ✅ ensures single-click transition

            with b2:
                st.button("SAP HCM → S/4HANA (coming soon)", disabled=True)

            with b3:
                st.button("Legacy HR Systems → SAP Cloud or On-Premise (coming soon)", disabled=True)

            st.image("dmigimg.jpg", use_container_width=True)

    elif st.session_state.demo_page == "sap_to_sf":
        back_col, _ = st.columns([1, 5])
        with back_col:
            if st.button("⬅ Back to Scenarios", key="btn_back_scenarios", use_container_width=True):
                st.session_state.demo_page = "main"
                st.rerun()

        st.title("SAP HCM → SuccessFactors")
        st.subheader("What do you want to migrate?")

        def migration_row(label, key, detail_text, next_page=None):
            col1, col2 = st.columns([5, 3.8])
            with col1:
                if st.button(label, key=key, use_container_width=True):
                    if next_page:
                        st.session_state.demo_page = next_page
                        st.rerun()
            with col2:
                with st.expander("ℹ️ Details"):
                    st.markdown(detail_text)
        migration_row("Foundation Data", "fd_demo", "- Legal Entity\n- Job Classification\n- Location\n- Org Units\n...", next_page="foundation_data_view")

        # Time Data — grayed out and disabled
        col1, col2 = st.columns([5, 3.8])
        with col1:
            st.button("Time Data", key="td_demo_disabled", disabled=True, use_container_width=True)
        with col2:
            with st.expander("ℹ️ Details"):
                st.markdown("- Time Type\n- Accruals\n- Time Accounts\n- Absences\n...")
        st.markdown("""
            <style>
            button[data-testid="baseButton-td_demo_disabled"] {
                background-color: #ddd !important;
                color: #888 !important;
                cursor: not-allowed !important;
            }
            </style>
        """, unsafe_allow_html=True)

        # Payroll Data
        migration_row("Payroll Data", "ptd_demo", "- Payment Info\n- Super Funds\n- Cost Allocations\n...", next_page="payroll_data_tool")

        # Employee Data V2 — single version only
        migration_row(
            "Employee Data",
            "pd_demo",
            "- Personal Info\n- Employment Info\n- Compensation Info\n- Time Info\n...",
            next_page="employee_data_v2"
        )

    elif st.session_state.demo_page == "payroll_data_tool":
        back_col, _ = st.columns([1, 5])
        with back_col:
            if st.button("⬅ Back to Demo", key="back_from_payroll", use_container_width=True):
                st.session_state.demo_page = "sap_to_sf"
                st.rerun()
    
        st.sidebar.markdown("---")
        selected_radio = st.radio("Payroll Section:", ["Tool", "Configuration Manager"], key="payroll_radio")
        st.session_state.tool_subpage = selected_radio  # ✅ sync selection
    
        if st.session_state.tool_subpage == "Tool":
            payroll_app.render_payroll_tool()
        else:
            try:
                show_admin_panel(mode="payroll")
            except Exception as e:
                st.error(f"Configuration Manager failed to load: {e}")
    
    elif st.session_state.demo_page == "foundation_data_view":
        back_col, _ = st.columns([1, 5])
        with back_col:
            if st.button("⬅ Back to Demo", key="back_from_foundation", use_container_width=True):
                st.session_state.demo_page = "sap_to_sf"
                st.rerun()
    
        st.sidebar.markdown("---")
        selected_radio = st.radio("Foundation Section:", ["Tool", "Configuration Manager"], key="foundation_radio")
        st.session_state.tool_subpage = selected_radio  # ✅ sync selection
    

    elif st.session_state.demo_page == "employee_data_v2":
        back_col, _ = st.columns([1, 5])
        with back_col:
            if st.button("⬅ Back to Demo", key="back_from_empv2", use_container_width=True):
                st.session_state.demo_page = "sap_to_sf"
                st.rerun()

        st.markdown("### Employee Data V2 – Interactive Migration Tool")
        render_employee_v2()


# -------------------- SOLUTIONS --------------------
elif selected == "Solutions":
    sol_choice = option_menu(
        menu_title="Our Solutions",
        options=["Data Migration", "Validation", "Discrepancy Analysis Report"],
        icons=["cloud-upload", "check2-square", "bar-chart"],
        orientation="horizontal",
        key="solutions_nav"
    )

    # --- DATA MIGRATION ---
    if sol_choice == "Data Migration":
        col1, col2 = st.columns([2.9, 3])

        with col1:
            st.markdown("## End-to-End SAP HR Transformation Journey")
            st.markdown("""
A secure, scalable, audit-ready solution for migrating HR data across SAP On-Premise, S/4HANA, SuccessFactors, and legacy systems.
            """)

            # --- INTERACTIVE BUTTONS WITH TOGGLE ---
            if "show_fd" not in st.session_state:
                st.session_state.show_fd = False
            if "show_emd" not in st.session_state:
                st.session_state.show_emd = False
            if "show_pd" not in st.session_state:
                st.session_state.show_pd = False
            if "show_ptd" not in st.session_state:
                st.session_state.show_ptd = False

            col_a, col_b = st.columns(2)
            with col_a:
                if st.button("Foundation Data", key="fd_btn"):
                    st.session_state.show_fd = not st.session_state.show_fd
                if st.session_state.show_fd:
                    st.info("""
- Org Hierarchy  
- Cost Center  
- Location  
- Pay Scale Info  
- Job Classification  
- Work Schedule
- Position Data
                    """)

                if st.button("Employee Data", key="pd_btn"):
                    st.session_state.show_pd = not st.session_state.show_pd
                if st.session_state.show_pd:
                    st.info("""
- Basic Information  
- Biographical Information  
- Job Information  
- Employment Information  
- Compensation Info  
- Payments  
- Superannuation  
- Tax Information  
- Time  
- Address Information  
- Email Information  
- Work Permit  
- Alternative Cost Distribution  
                    """)

            with col_b:
                if st.button("Time Data", key="emd_btn"):
                    st.session_state.show_emd = not st.session_state.show_emd
                if st.session_state.show_emd:
                    st.info("""
- Time Type  
- Time Account Type  
- Time Account (Accrual/Entitlement)  
- Time Account Details (Accrual/Entitlement)  
- Employee Time (Absences)  
                    """)

                if st.button("Payroll Data", key="ptd_btn"):
                    st.session_state.show_ptd = not st.session_state.show_ptd
                if st.session_state.show_ptd:
                    st.info("""
- Bank Info  
- Super Funds  
- Daily Work Schedule  
- Period Work Schedule  
- Work Schedule Rules  
- Cost Center  
                    """)

        with col2:
            st.image("edmdr.png", use_container_width=True)

            st.markdown("### Supported Scenarios")
            st.markdown("""
- SAP ECC → SuccessFactors (EC, Time, Payroll)  
- SAP ECC → S/4HANA (HCM, Payroll, PA (Personnel Administration), OM (Organizational Management))  
- Legacy/Non-SAP → SAP HCM and SuccessFactors
            """)

            st.markdown("### Key Features")
            st.markdown("""
- **Transformation Engine:** Transformation engine with rollback support  
- **Template Uploads:** Pre-configured mapping, reduced effort  
- **Role-Based Access:** Permission management based on user roles  
- **Validation Reports:** Flags issues across all stages  
- **Rule Engine:** Reusable, localized logic
            """)

        # ✅ Bottom banner image
        st.image("datamig_img.png", use_container_width=True)
    # --- VALIDATION ---
    elif sol_choice == "Validation":
        col1, col2 = st.columns([3, 2.7])
        with col1:
            st.markdown("## Ensuring Data Accuracy Between Systems")
            st.markdown("""
Our validation services ensure HR data is correctly mapped, transformed, and loaded across every migration stage. We validate data between source systems, load files, and reporting outputs to confirm consistency and production readiness.

**What We Validate:**
- Required Fields: Detect missing/null values in critical fields  
- Format Compliance: Enforce expected types and structures  
- Mapping Accuracy: Verify source-to-target alignment  
- Source-to-File Match: Ensure extracted data mirrors load-ready files  
- Post-Load Validation: Confirm target system reflects intended records  
- Change Monitoring: Identify and isolate high-impact issues
            """)

        with col2:
            st.markdown("### Key Features")
            st.markdown("""
- Rules-Based Validation Engine  
- Categorized Exception Reporting  
- Iterative Revalidation Workflow  
- Full Audit Logging for Compliance  
- Support for all Employee Information
            """)
            st.image("validation_lifecycle.png", use_container_width=False, width=350)

    # --- DISCREPANCY ANALYSIS ---
    elif sol_choice == "Discrepancy Analysis Report":
        col1, col2 = st.columns([3, 2.6])
        with col1:
            st.markdown("## Reconciliation Across Systems")
            st.markdown("""
Our monitoring validates accurate data loads post-migration–across platforms like SuccessFactors, S/4HANA, or SAP HCM. It ensures alignment, traceability, and readiness for live HR/payroll processes.

**What We Monitor:**
- **Field-Level Accuracy:** Detect mismatches in critical values  
- **Record Completeness:** Spot missing/extra records  
- **Business-Critical Fields:** Focus on payroll, time, and org structures  
- **Change Tracking:** View changes before/after load

We cover field-level, record-level, and format-level checks to ensure clean post-migration integrity across HR modules.  
Visual dashboards and summary reports offer real-time reconciliation status for faster resolution and compliance.
            """)

        with col2:
            st.markdown("### Key Features")
            st.markdown("""
- Source-to-Target Comparisons  
- Discrepancy Summary Reports  
- Visual Reconciliation Dashboards  
- Logged Issues for Governance & Audit
            """)
            st.image("pexels-divinetechygirl-1181341.jpg", use_container_width=False, width=350)

