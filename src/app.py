import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import json

# Integration: Query Parser Agent
from agents.query_parser_agent import parse_and_complete

# Configure the page
st.set_page_config(
    page_title="Fulcrum Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS to match Figma design exactly
st.markdown("""
<style>
    /* Import modern fonts */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500&display=swap');
    
    /* Hide Streamlit default elements */
    #MainMenu {visibility: hidden;}
    .stDeployButton {display:none;}
    footer {visibility: hidden;}
    #stDecoration {display:none;}
    header[data-testid="stHeader"] {display: none;}
    
    /* Main app styling with modern design */
    .stApp {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
        background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%);
    }
    
    /* Enhanced sidebar with glassmorphism effect */
    section[data-testid="stSidebar"] {
        background: rgba(30, 58, 138, 0.95) !important;
        backdrop-filter: blur(20px) !important;
        border-right: 1px solid rgba(255, 255, 255, 0.1) !important;
    }
    
    section[data-testid="stSidebar"] > div {
        background: transparent !important;
        padding-top: 2rem !important;
    }
    
    /* Modern sidebar title with glow effect */
    .stSidebar h1 {
        color: white !important;
        text-align: center !important;
        font-weight: 700 !important;
        font-size: 1.8rem !important;
        margin-bottom: 3rem !important;
        text-shadow: 0 0 20px rgba(255, 255, 255, 0.3) !important;
        letter-spacing: 0.5px !important;
    }
    
    /* Enhanced sidebar buttons with modern design */
    .stSidebar .stButton > button {
        background: rgba(255, 255, 255, 0.08) !important;
        color: #e2e8f0 !important;
        border: 1px solid rgba(255, 255, 255, 0.12) !important;
        padding: 1rem 1.5rem !important;
        border-radius: 12px !important;
        text-align: left !important;
        width: 100% !important;
        font-size: 0.95rem !important;
        font-weight: 500 !important;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
        margin-bottom: 0.5rem !important;
        backdrop-filter: blur(10px) !important;
        position: relative !important;
        overflow: hidden !important;
    }
    
    .stSidebar .stButton > button:before {
        content: '';
        position: absolute;
        top: 0;
        left: -100%;
        width: 100%;
        height: 100%;
        background: linear-gradient(90deg, transparent, rgba(255,255,255,0.1), transparent);
        transition: left 0.5s;
    }
    
    .stSidebar .stButton > button:hover:before {
        left: 100%;
    }
    
    .stSidebar .stButton > button:hover {
        background: rgba(59, 130, 246, 0.3) !important;
        color: white !important;
        transform: translateX(8px) scale(1.02) !important;
        box-shadow: 0 8px 25px rgba(59, 130, 246, 0.4) !important;
        border-color: rgba(59, 130, 246, 0.5) !important;
    }
    
    .stSidebar .stButton > button:focus {
        background: rgba(79, 70, 229, 0.4) !important;
        color: white !important;
        box-shadow: 0 0 0 3px rgba(79, 70, 229, 0.3) !important;
        border-color: rgba(79, 70, 229, 0.6) !important;
    }
    
    /* Modern main content area */
    .main .block-container {
        padding: 1rem 2rem !important;
        max-width: none !important;
        background: transparent !important;
    }
    
    section.main > div {
        padding-left: 0.5rem !important;
        padding-top: 0.5rem !important;
        background: transparent !important;
    }
    
    /* Fix text visibility - ensure main content text is dark */
    .main, .main *,
    .stMarkdown, .stMarkdown *,
    .stText, .stText *,
    section.main p, section.main span, section.main div, 
    section.main h1, section.main h2, section.main h3, 
    section.main h4, section.main h5, section.main h6 {
        color: #1f2937 !important;
    }
    
    /* Keep sidebar text WHITE */
    .stSidebar, .stSidebar *,
    [data-testid="stSidebar"], [data-testid="stSidebar"] *,
    .css-1d391kg, .css-1d391kg *,
    .sidebar .stMarkdown, .sidebar .stMarkdown *,
    .stSidebar .stMarkdown, .stSidebar .stMarkdown *,
    .stSidebar p, .stSidebar span, .stSidebar div,
    .stSidebar h1, .stSidebar h2, .stSidebar h3, 
    .stSidebar h4, .stSidebar h5, .stSidebar h6 {
        color: #e2e8f0 !important;
    }
    
    /* Sidebar button text should be white */
    .stSidebar .stButton > button {
        color: #e2e8f0 !important;
    }
    
    /* Override main content widget text colors (not sidebar) */
    section.main .stSelectbox label, section.main .stMultiSelect label, 
    section.main .stRadio label, section.main .stTextInput label,
    section.main .stNumberInput label, section.main .stSlider label {
        color: #1f2937 !important;
        font-weight: 500 !important;
    }
    
    /* Fix tab text - only in main content */
    section.main .stTabs [data-baseweb="tab-list"] button {
        color: #1f2937 !important;
    }
    
    section.main .stTabs [data-baseweb="tab-list"] button[aria-selected="true"] {
        color: #3b82f6 !important;
    }
    
    /* Fix metric container text - only in main content */
    section.main [data-testid="metric-container"] {
        color: #1f2937 !important;
    }
    
    section.main [data-testid="metric-container"] * {
        color: #1f2937 !important;
    }
    
    /* Fix info/success/warning text - only in main content */
    section.main .stInfo, section.main .stSuccess, 
    section.main .stWarning, section.main .stError {
        color: #1f2937 !important;
    }
    
    /* Ensure main content button text is visible */
    section.main .stButton > button {
        color: #1f2937 !important;
        background-color: #ffffff !important;
        border: 1px solid #d1d5db !important;
    }
    
    section.main .stButton > button:hover {
        color: #ffffff !important;
        background-color: #3b82f6 !important;
    }
    
    /* Fix chart and dataframe text - only in main content */
    section.main .js-plotly-plot * {
        color: #1f2937 !important;
    }
    
    section.main .stDataFrame {
        color: #1f2937 !important;
    }
    
    /* Ensure main content form labels are visible */
    /* Streamlit element spacing optimization */
    .element-container {
        margin-bottom: 0.5rem !important;
    }
    
    .stMarkdown {
        margin-bottom: 0.5rem !important;
    }
    
    .row-widget {
        margin-bottom: 0.5rem !important;
    }
    
    /* Reduce default Streamlit spacing */
    .main .block-container > div {
        gap: 0.5rem !important;
    }
    
    /* Compact columns */
    [data-testid="column"] {
        padding: 0.25rem !important;
    }
    
    /* Enhanced content headers */
    .content-header {
        font-size: 2.5rem !important;
        font-weight: 700 !important;
        color: #1e293b !important;
        margin-bottom: 0.5rem !important;
        background: linear-gradient(135deg, #1e3a8a, #3b82f6) !important;
        background-clip: text !important;
        -webkit-background-clip: text !important;
        -webkit-text-fill-color: transparent !important;
        text-shadow: 0 4px 8px rgba(0,0,0,0.1) !important;
    }
    
    .breadcrumb {
        color: #64748b !important;
        font-size: 0.9rem !important;
        font-weight: 500 !important;
        margin-bottom: 2.5rem !important;
        opacity: 0.8 !important;
    }
    
    /* Modern card design with glassmorphism */
    .modern-card {
        background: rgba(255, 255, 255, 0.95) !important;
        backdrop-filter: blur(20px) !important;
        border: 1px solid rgba(255, 255, 255, 0.2) !important;
        border-radius: 20px !important;
        padding: 2rem !important;
        margin: 1rem 0 !important;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1) !important;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
    }
    
    .modern-card:hover {
        transform: translateY(-4px) !important;
        box-shadow: 0 20px 40px rgba(0, 0, 0, 0.15) !important;
        border-color: rgba(59, 130, 246, 0.3) !important;
    }
    
    /* Enhanced metrics cards */
    div[data-testid="metric-container"] {
        background: rgba(255, 255, 255, 0.95) !important;
        border: 1px solid rgba(255, 255, 255, 0.2) !important;
        border-radius: 16px !important;
        padding: 1.5rem !important;
        backdrop-filter: blur(20px) !important;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08) !important;
        transition: all 0.3s ease !important;
    }
    
    div[data-testid="metric-container"]:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 8px 30px rgba(0, 0, 0, 0.12) !important;
    }
    
    /* Modern buttons */
    .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #3b82f6, #1d4ed8) !important;
        color: white !important;
        border: none !important;
        border-radius: 12px !important;
        padding: 0.75rem 2rem !important;
        font-weight: 600 !important;
        font-size: 0.95rem !important;
        transition: all 0.3s ease !important;
        box-shadow: 0 4px 15px rgba(59, 130, 246, 0.4) !important;
    }
    
    .stButton > button[kind="primary"]:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 8px 25px rgba(59, 130, 246, 0.6) !important;
        background: linear-gradient(135deg, #2563eb, #1e40af) !important;
    }
    
    /* Form styling improvements */
    .stSelectbox > div > div {
        border-radius: 10px !important;
        border: 2px solid #e2e8f0 !important;
        transition: all 0.2s ease !important;
    }
    
    .stSelectbox > div > div:focus-within {
        border-color: #3b82f6 !important;
        box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1) !important;
    }
    
    .stTextInput > div > div > input {
        border-radius: 10px !important;
        border: 2px solid #e2e8f0 !important;
        transition: all 0.2s ease !important;
    }
    
    .stTextInput > div > div > input:focus {
        border-color: #3b82f6 !important;
        box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1) !important;
    }
    
    /* Data table enhancements */
    .stDataFrame {
        border-radius: 12px !important;
        overflow: hidden !important;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08) !important;
    }
    
    /* Chart improvements */
    .stPlotlyChart {
        border-radius: 12px !important;
        overflow: hidden !important;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08) !important;
    }
    
    /* Responsive design */
    @media (max-width: 768px) {
        .main .block-container {
            padding: 0.5rem !important;
        }
        
        .content-header {
            font-size: 1.5rem !important;
        }
        
        .modern-card {
            padding: 1rem !important;
            margin: 0.5rem 0 !important;
        }
    }
    
    /* Loading animations */
    @keyframes fadeInUp {
        from {
            opacity: 0;
            transform: translateY(30px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }
    
    .fade-in {
        animation: fadeInUp 0.6s ease-out;
    }
    
    /* Additional animations for enhanced UI */
    @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.5; }
    }
    
    @keyframes progress-load {
        0% { width: 0%; }
        100% { width: var(--final-width); }
    }
    
    @keyframes slideInRight {
        from {
            opacity: 0;
            transform: translateX(50px);
        }
        to {
            opacity: 1;
            transform: translateX(0);
        }
    }
    
    @keyframes floating {
        0%, 100% { transform: translateY(0px); }
        50% { transform: translateY(-5px); }
    }
    
    @keyframes shimmer {
        0% { background-position: -200px 0; }
        100% { background-position: calc(200px + 100%) 0; }
    }
    
    /* Enhanced hover effects */
    .hover-lift {
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    }
    
    .hover-lift:hover {
        transform: translateY(-4px);
        box-shadow: 0 12px 30px rgba(0, 0, 0, 0.15) !important;
    }
    
    /* Activity item animations */
    .activity-item {
        transition: all 0.3s ease;
        cursor: pointer;
    }
    
    .activity-item:hover {
        transform: translateX(8px);
        background: linear-gradient(135deg, #f8fafc, #f1f5f9) !important;
    }
    
    /* Metric card enhancements */
    .metric-progress {
        transition: width 2s ease-in-out;
    }
    
    /* Scrollbar styling */
    ::-webkit-scrollbar {
        width: 8px;
    }
    
    ::-webkit-scrollbar-track {
        background: rgba(255, 255, 255, 0.1);
        border-radius: 4px;
    }
    
    ::-webkit-scrollbar-thumb {
        background: rgba(59, 130, 246, 0.3);
        border-radius: 4px;
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: rgba(59, 130, 246, 0.5);
    }
</style>
""", unsafe_allow_html=True)

def create_sidebar():
    """Create custom sidebar to match Figma design"""
    st.markdown("""
    <div class="custom-sidebar">
        <div class="sidebar-title">Fulcrum</div>
    </div>
    """, unsafe_allow_html=True)

def main():
    # Initialize session state for navigation
    if 'current_page' not in st.session_state:
        st.session_state.current_page = 'Dashboard'
    
    # Use Streamlit's built-in sidebar
    with st.sidebar:
        st.markdown('<h1 style="color: white; text-align: center; margin-bottom: 2rem;">Fulcrum</h1>', unsafe_allow_html=True)
        
        # Navigation buttons
        if st.button("📊 Dashboard", use_container_width=True, key="nav_dashboard"):
            st.session_state.current_page = 'Dashboard'
            st.rerun()
            
        if st.button("📝 Data Input", use_container_width=True, key="nav_data_input"):
            st.session_state.current_page = 'Data Input'
            st.rerun()
            
        if st.button("� LCA Analysis", use_container_width=True, key="nav_lca_analysis"):
            st.session_state.current_page = 'LCA Analysis'
            st.rerun()
            
        if st.button("📄 Report", use_container_width=True, key="nav_report"):
            st.session_state.current_page = 'Report'
            st.rerun()
            
        if st.button("⚡ Optimization", use_container_width=True, key="nav_optimization"):
            st.session_state.current_page = 'Optimization'
            st.rerun()
            
        if st.button("⚙️ Settings", use_container_width=True, key="nav_settings"):
            st.session_state.current_page = 'Settings'
            st.rerun()
    
    # Main content area - content appears to the right of sidebar
    page = st.session_state.current_page
    
    # Final comprehensive spacing optimization CSS
    st.markdown("""
    <style>
        /* Eliminate all empty space and ensure full width utilization */
        .main .block-container {
            padding-top: 0.5rem !important;
            padding-bottom: 0.5rem !important;
            padding-left: 1rem !important;
            padding-right: 1rem !important;
            max-width: 100% !important;
            width: 100% !important;
        }
        
        /* Remove gaps between elements */
        .element-container {
            margin-bottom: 0.25rem !important;
        }
        
        /* Compact metrics */
        [data-testid="metric-container"] {
            margin-bottom: 0.5rem !important;
            padding: 0.5rem !important;
        }
        
        /* Remove extra padding from columns */
        [data-testid="column"] {
            padding: 0 0.25rem !important;
        }
        
        /* Compact headers and markdown */
        .stMarkdown h1, .stMarkdown h2, .stMarkdown h3 {
            margin-top: 0.5rem !important;
            margin-bottom: 0.5rem !important;
        }
        
        /* Full width for selectboxes and inputs */
        .row-widget.stSelectbox > div,
        .row-widget.stMultiselect > div,
        .row-widget.stTextInput > div {
            width: 100% !important;
        }
        
        /* Compact charts */
        .stPlotlyChart, .stVegaLiteChart {
            margin-bottom: 0.5rem !important;
        }
        
        /* Remove unnecessary spacing in columns */
        .css-1d391kg, .css-12w0qpk {
            padding: 0 !important;
        }
        
        /* Ensure buttons use full width when specified */
        .stButton > button[data-testid="baseButton-secondary"],
        .stButton > button[data-testid="baseButton-primary"] {
            width: 100% !important;
        }
    </style>
    """, unsafe_allow_html=True)
    
    if page == "Dashboard":
        show_dashboard()
    elif page == "Data Input":
        show_data_input()
    elif page == "LCA Analysis":
        show_lca_analysis()
    elif page == "Report":
        show_report()
    elif page == "Optimization":
        show_optimization()
    elif page == "Settings":
        show_settings()
    else:
        # Fallback - show dashboard
        show_dashboard()

def show_dashboard():
    st.markdown('<div class="content-header">AI-Powered LCA Dashboard for Metals Circularity</div>', unsafe_allow_html=True)
    st.markdown('<div class="breadcrumb">Home > Dashboard</div>', unsafe_allow_html=True)
    
    # Welcome section with modern gradient design
    st.markdown("""
    <div class="modern-card fade-in" style="
        background: linear-gradient(135deg, #1e3a8a 0%, #3b82f6 100%) !important;
        color: white;
        text-align: center;
        border: none !important;
        position: relative;
        overflow: hidden;
        padding: 1.5rem !important;
        margin-bottom: 1rem !important;
    ">
        <div style="position: absolute; top: -50%; right: -50%; width: 200%; height: 200%; background: radial-gradient(circle, rgba(255,255,255,0.1) 0%, transparent 70%);"></div>
        <div style="position: relative; z-index: 1;">
            <h2 style="margin: 0; color: white; font-size: 1.8rem; font-weight: 700; text-shadow: 0 2px 10px rgba(0,0,0,0.3);">
                🤖 AI-Powered LCA Dashboard for Metals Circularity
            </h2>
            <p style="margin: 0.5rem 0 0 0; opacity: 0.95; font-size: 1rem; font-weight: 400;">
                Empowering sustainable metal processing
            </p>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Key Performance Indicators
    st.subheader("� Key Performance Indicators")
    
    # Full-width KPI metrics row
    kpi_col1, kpi_col2, kpi_col3, kpi_col4 = st.columns(4)
    
    with kpi_col1:
        st.metric(
            "🌍 Carbon Footprint",
            "2,380 kg CO₂",
            "-12%",
            help="Total carbon emissions reduction"
        )
    
    with kpi_col2:
        st.metric(
            "♻️ Circularity Score",
            "8.6/10",
            "+19%",
            help="AI-calculated circularity assessment score"
        )
    
    with kpi_col3:
        st.metric(
            "⚡ Energy Efficiency",
            "1,020 kWh",
            "-8%",
            help="Energy consumption optimization"
        )
    
    with kpi_col4:
        st.metric(
            "📦 Resource Efficiency",
            "94.2%",
            "+8.7%",
            help="Overall resource utilization efficiency"
        )
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Main dashboard content - full width utilization
    main_col1, main_col2 = st.columns([7, 3])
    
    
    with main_col1:
        # Charts and Analytics Section
        st.subheader("📈 Environmental Analysis Dashboard")
        
        # Charts in two columns
        chart_col1, chart_col2 = st.columns(2)
        
        with chart_col1:
            st.markdown("**Environmental Impact Trends**")
            
            # Sample trend data
            months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun']
            impact_data = pd.DataFrame({
                'Month': months,
                'Carbon (kg CO2)': [2800, 2650, 2750, 2580, 2420, 2380],
                'Energy (kWh)': [1200, 1150, 1180, 1100, 1050, 1020],
                'Circularity': [7.2, 7.5, 7.8, 8.1, 8.4, 8.6]
            })
            
            selected_metrics = st.multiselect(
                "Select metrics:",
                ['Carbon (kg CO2)', 'Energy (kWh)', 'Circularity'],
                default=['Carbon (kg CO2)', 'Energy (kWh)'],
                key="trend_metrics"
            )
            
            if selected_metrics:
                st.line_chart(impact_data.set_index('Month')[selected_metrics])
            else:
                st.info("Select metrics to display")
        
        with chart_col2:
            st.markdown("**Processing Analysis**")
            
            processing_data = pd.DataFrame({
                'Process': ['Primary Al', 'Recycled Al', 'Primary Cu', 'Recycled Cu'],
                'Impact': [100, 25, 100, 15],
                'Score': [3.2, 9.1, 3.8, 9.5]
            })
            
            chart_type = st.radio(
                "View:", ["Environmental Impact", "Circularity Score"], 
                horizontal=True, key="process_chart"
            )
            
            if chart_type == "Environmental Impact":
                st.bar_chart(processing_data.set_index('Process')[['Impact']])
            else:
                st.bar_chart(processing_data.set_index('Process')[['Score']])
        
        # AI Insights Row - Compact Cards
        st.markdown("<br>", unsafe_allow_html=True)
        st.subheader("🤖 AI-Powered Insights")
        
        insight_col1, insight_col2, insight_col3 = st.columns(3)
        
        with insight_col1:
            st.markdown("""
            <div style="background: linear-gradient(135deg, rgba(16, 185, 129, 0.1), rgba(34, 197, 94, 0.05));
                        border-left: 4px solid #10b981; padding: 1rem; border-radius: 8px; margin-bottom: 1rem;">
                <h4 style="color: #047857; margin: 0 0 0.5rem 0; font-size: 0.9rem;">🔍 Recommendation</h4>
                <p style="color: #374151; margin: 0; font-size: 0.8rem; line-height: 1.4;">
                    Switch to <strong>85% recycled aluminum</strong> for <strong>23% impact reduction</strong>
                </p>
                <div style="margin-top: 0.5rem; padding: 0.25rem 0.5rem; background: rgba(16, 185, 129, 0.1); 
                            border-radius: 4px; font-size: 0.7rem; color: #047857;">
                    💡 94% confidence
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        with insight_col2:
            st.markdown("""
            <div style="background: linear-gradient(135deg, rgba(99, 102, 241, 0.1), rgba(139, 92, 246, 0.05));
                        border-left: 4px solid #6366f1; padding: 1rem; border-radius: 8px; margin-bottom: 1rem;">
                <h4 style="color: #4338ca; margin: 0 0 0.5rem 0; font-size: 0.9rem;">⚡ Optimization</h4>
                <p style="color: #374151; margin: 0; font-size: 0.8rem; line-height: 1.4;">
                    <strong>15% energy savings</strong> identified in copper smelting operations
                </p>
                <div style="margin-top: 0.5rem; padding: 0.25rem 0.5rem; background: rgba(99, 102, 241, 0.1); 
                            border-radius: 4px; font-size: 0.7rem; color: #4338ca;">
                    ⚡ $8,200/month savings
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        with insight_col3:
            st.markdown("""
            <div style="background: linear-gradient(135deg, rgba(245, 158, 11, 0.1), rgba(251, 191, 36, 0.05));
                        border-left: 4px solid #f59e0b; padding: 1rem; border-radius: 8px; margin-bottom: 1rem;">
                <h4 style="color: #b45309; margin: 0 0 0.5rem 0; font-size: 0.9rem;">🔄 Recovery</h4>
                <p style="color: #374151; margin: 0; font-size: 0.8rem; line-height: 1.4;">
                    <strong>92% material recovery</strong> potential through improved sorting
                </p>
                <div style="margin-top: 0.5rem; padding: 0.25rem 0.5rem; background: rgba(245, 158, 11, 0.1); 
                            border-radius: 4px; font-size: 0.7rem; color: #b45309;">
                    ♻️ +15% recovery rate
                </div>
            </div>
            """, unsafe_allow_html=True)
    
    with main_col2:
        # Compact sidebar content
        st.subheader("🔧 System Status")
        
        # Compact status indicators
        statuses = [
            ("Data Processing", "Online", "#22c55e"),
            ("AI Model", "Active", "#3b82f6"), 
            ("Database", "Connected", "#22c55e"),
            ("API", "Running", "#22c55e")
        ]
        
        for label, status, color in statuses:
            st.markdown(f"""
            <div style="display: flex; justify-content: space-between; align-items: center; 
                        padding: 0.5rem 0.75rem; margin-bottom: 0.4rem; background: #f8fafc; 
                        border-radius: 6px; border: 1px solid #e2e8f0;">
                <span style="color: #374151; font-size: 0.8rem; font-weight: 500;">{label}</span>
                <div style="display: flex; align-items: center;">
                    <div style="width: 6px; height: 6px; background: {color}; border-radius: 50%; margin-right: 0.4rem;"></div>
                    <span style="color: {color}; font-size: 0.75rem; font-weight: 500;">{status}</span>
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        st.subheader("📋 Recent Activity")
        
        # Compact activity feed
        activities = [
            ("🔄", "Al optimization completed", "2m"),
            ("📊", "Cu assessment started", "15m"),
            ("⚠️", "Energy alert triggered", "1h"),
            ("✅", "Monthly report ready", "2h"),
            ("🔍", "New data processed", "3h")
        ]
        
        for icon, text, time in activities:
            st.markdown(f"""
            <div style="background: white; padding: 0.5rem; margin-bottom: 0.4rem; 
                        border-left: 3px solid #3b82f6; border-radius: 0 6px 6px 0; 
                        box-shadow: 0 1px 2px rgba(0,0,0,0.1);">
                <div style="display: flex; align-items: center; margin-bottom: 0.2rem;">
                    <span style="margin-right: 0.5rem; font-size: 0.9rem;">{icon}</span>
                    <span style="color: #374151; font-size: 0.8rem; font-weight: 500;">{text}</span>
                </div>
                <span style="color: #9ca3af; font-size: 0.7rem;">{time} ago</span>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        st.subheader("⚡ Quick Actions")
        
        if st.button("📊 New Analysis", key="quick_analysis", use_container_width=True, type="primary"):
            st.session_state.current_page = 'LCA Analysis'
            st.rerun()
        
        if st.button("📈 View Reports", key="quick_reports", use_container_width=True):
            st.session_state.current_page = 'Report'
            st.rerun()
        
        if st.button("⚙️ Optimize", key="quick_optimize", use_container_width=True):
            st.session_state.current_page = 'Optimization'
            st.rerun()
    
    # Bottom action row - Full width
    st.markdown("<br>", unsafe_allow_html=True)
    st.subheader("⚡ Additional Tools")
    
    tool_col1, tool_col2, tool_col3, tool_col4 = st.columns(4)
    
    with tool_col1:
        if st.button("📋 Data Input", key="tool_data", use_container_width=True):
            st.session_state.current_page = 'Data Input'
            st.rerun()
    
    with tool_col2:
        if st.button("🎯 Optimization", key="tool_opt", use_container_width=True):
            st.session_state.current_page = 'Optimization'
            st.rerun()
    
    with tool_col3:
        if st.button("📄 Documentation", key="tool_docs", use_container_width=True):
            st.session_state.current_page = 'Documentation'
            st.rerun()
    
    with tool_col4:
        if st.button("⚙️ Settings", key="tool_settings", use_container_width=True):
            st.session_state.current_page = 'Settings'
            st.rerun()

# Final spacing optimization CSS to eliminate empty space
st.markdown("""
<style>
    /* Additional space elimination */
    .main .block-container {
        padding-top: 1rem !important;
        padding-bottom: 1rem !important;
        max-width: 100% !important;
    }
    
    /* Remove gaps between elements */
    .element-container {
        margin-bottom: 0 !important;
    }
    
    /* Ensure full width utilization */
    .row-widget.stSelectbox > div,
    .row-widget.stMultiselect > div {
        width: 100% !important;
    }
    
    /* Compact metrics */
    [data-testid="metric-container"] {
        margin-bottom: 0.5rem !important;
    }
    
    /* Remove extra padding from columns */
    [data-testid="column"] {
        padding: 0 0.25rem !important;
    }
    
    /* Compact headers */
    .stMarkdown h1, .stMarkdown h2, .stMarkdown h3 {
        margin-top: 0.5rem !important;
        margin-bottom: 0.5rem !important;
    }
</style>
""", unsafe_allow_html=True)

def show_lca_analysis():
    st.markdown('<div class="content-header">🔬 Life Cycle Assessment Analysis</div>', unsafe_allow_html=True)
    
    # Page description
    st.markdown("""
    <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                padding: 1.5rem; border-radius: 10px; margin-bottom: 2rem; color: white;">
        <h3 style="margin: 0 0 0.5rem 0; color: white;">🔬 Advanced LCA Analysis Platform</h3>
        <p style="margin: 0; opacity: 0.9; color: white;">
            Comprehensive Life Cycle Assessment for metals processing with AI-powered insights 
            and circularity optimization recommendations.
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Main LCA content would go here
    st.subheader("📊 LCA Analysis Dashboard")

    # Show parsed input summary if available
    payload = st.session_state.get("query_payload")
    prov = st.session_state.get("query_provenance")
    issues = st.session_state.get("query_issues")
    if payload:
        with st.expander("View completed input payload", expanded=False):
            st.json(payload)
        if prov:
            with st.expander("Provenance (field source)", expanded=False):
                st.json(prov)
        if issues:
            st.warning("\n".join(issues))
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Current Analysis Status**")
        st.info("🔄 Ready for new analysis")
        
        if st.button("🚀 Start New LCA Analysis", type="primary", use_container_width=True):
            st.session_state.current_page = 'Data Input'
            st.rerun()
    
    with col2:
        st.markdown("**Recent Results**")
        st.success("✅ Last analysis completed successfully")
        
        if st.button("📈 View Results", use_container_width=True):
            st.session_state.current_page = 'Report'
            st.rerun()

def show_data_input():
    st.markdown('<div class="content-header">Data Input</div>', unsafe_allow_html=True)
    st.markdown('<div class="breadcrumb">Home > Data Input</div>', unsafe_allow_html=True)
    
    # Create a centered form container matching Figma design
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        # Data input form will go here
        st.info("Data input form is being prepared...")
        st.markdown("**Temporary data input placeholder**")
        
        if st.button("Continue to LCA Analysis", use_container_width=True, type="primary"):
            st.session_state.current_page = 'LCA Analysis'
            st.rerun()
        
        # Metric 3: Energy Efficiency
        st.markdown("""
        <div class="modern-card fade-in" style="
            background: linear-gradient(135deg, rgba(99, 102, 241, 0.1), rgba(139, 92, 246, 0.05));
            border-left: 4px solid #6366f1;
            position: relative;
            overflow: hidden;
            margin-bottom: 1rem;
        ">
            <div style="position: absolute; top: -5px; right: -5px; width: 40px; height: 40px; background: rgba(99, 102, 241, 0.1); border-radius: 50%;"></div>
            <div style="position: relative; z-index: 1;">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem;">
                    <span style="color: #4338ca; font-weight: 600; font-size: 0.9rem;">⚡ ENERGY EFFICIENCY</span>
                    <span style="background: #e0e7ff; color: #4338ca; padding: 0.2rem 0.5rem; border-radius: 12px; font-size: 0.75rem; font-weight: 500;">
                        -8% consumption
                    </span>
                </div>
                <div style="display: flex; align-items: baseline; margin-bottom: 0.5rem;">
                    <span style="font-size: 2rem; font-weight: 700; color: #1f2937; margin-right: 0.5rem;">1,020</span>
                    <span style="color: #6b7280; font-size: 0.9rem;">kWh per unit</span>
                </div>
                <div style="background: #e0e7ff; height: 4px; border-radius: 2px; overflow: hidden;">
                    <div style="background: #6366f1; height: 100%; width: 68%; border-radius: 2px; animation: progress-load 1.5s ease-out;"></div>
                </div>
                <div style="font-size: 0.8rem; color: #6b7280; margin-top: 0.5rem;">Target: 900 kWh (68% to goal)</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Real-time status indicator
        st.markdown("""
        <div style="
            background: linear-gradient(135deg, #f8fafc, #f1f5f9);
            border: 1px solid #e2e8f0;
            border-radius: 12px;
            padding: 1rem;
            margin-top: 1rem;
            text-align: center;
        ">
            <div style="display: flex; align-items: center; justify-content: center; margin-bottom: 0.5rem;">
                <div style="width: 8px; height: 8px; background: #22c55e; border-radius: 50%; margin-right: 0.5rem; animation: pulse 2s infinite;"></div>
                <span style="color: #475569; font-weight: 500; font-size: 0.9rem;">Live Data Stream Active</span>
            </div>
            <span style="color: #64748b; font-size: 0.8rem;">Last updated: Just now</span>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("""
        <h3 style="color: #1f2937; margin: 0 0 1.5rem 0; font-weight: 600; display: flex; align-items: center;">
            <span style="margin-right: 0.5rem;">�</span>
            Environmental Trends
        </h3>
        """, unsafe_allow_html=True)
        
        # Interactive chart controls
        chart_tab1, chart_tab2 = st.tabs(["📊 Impact Trends", "🏭 Processing Routes"])
        
        with chart_tab1:
            # Time period selector
            time_period = st.selectbox(
                "Time Period", 
                ["Last 6 months", "Last year", "Last 2 years"],
                index=0,
                key="time_period"
            )
            
            # Sample trend data for metals LCA
            months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun']
            impact_data = pd.DataFrame({
                'Month': months,
                'Carbon Footprint (kg CO2)': [2800, 2650, 2750, 2580, 2420, 2380],
                'Energy Use (kWh)': [1200, 1150, 1180, 1100, 1050, 1020],
                'Circularity Score': [7.2, 7.5, 7.8, 8.1, 8.4, 8.6]
            })
            
            # Metric selector
            selected_metrics = st.multiselect(
                "Select metrics to display",
                ['Carbon Footprint (kg CO2)', 'Energy Use (kWh)', 'Circularity Score'],
                default=['Carbon Footprint (kg CO2)', 'Energy Use (kWh)'],
                key="selected_metrics"
            )
            
            if selected_metrics:
                st.line_chart(impact_data.set_index('Month')[selected_metrics])
            else:
                st.info("Please select at least one metric to display.")
                
        with chart_tab2:
            # Processing routes comparison
            route_type = st.radio(
                "Comparison Type",
                ["Environmental Impact", "Circularity Score", "Both"],
                horizontal=True,
                key="route_type"
            )
            
            processing_data = pd.DataFrame({
                'Route': ['Primary Al', 'Recycled Al', 'Primary Cu', 'Recycled Cu'],
                'Environmental Impact': [100, 25, 100, 15],
                'Circularity Score': [3.2, 9.1, 3.8, 9.5]
            })
            
            if route_type == "Environmental Impact":
                st.bar_chart(processing_data.set_index('Route')[['Environmental Impact']])
            elif route_type == "Circularity Score":
                st.bar_chart(processing_data.set_index('Route')[['Circularity Score']])
            else:
                st.bar_chart(processing_data.set_index('Route'))
    
    # Recent Assessments Section - Full Width
    st.markdown("""
    <h3 style="color: #1f2937; margin: 2rem 0 1rem 0; font-weight: 600; display: flex; align-items: center; font-size: 1.2rem;">
        <span style="margin-right: 0.5rem;">📋</span>
        Recent LCA Assessments
    </h3>
    """, unsafe_allow_html=True)
    
    recent_assessments = pd.DataFrame({
        'Material': ['Aluminum Sheet', 'Copper Wire', 'Steel Beam', 'Aluminum Can', 'Copper Pipe'],
        'Processing Route': ['85% Recycled', 'Primary + 20% Scrap', '70% Recycled', '95% Recycled', 'Primary'],
        'CO₂ Impact (kg)': [156.2, 892.5, 445.8, 89.3, 1205.7],
        'Circularity Score': [8.9, 6.2, 7.8, 9.4, 4.1],
        'Status': ['Completed', 'In Progress', 'Completed', 'Completed', 'Pending Review']
    })
    
    st.dataframe(
        recent_assessments,
        use_container_width=True,
        hide_index=True
    )
    
    # Action items
    st.subheader("🎯 Recommended Actions")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🔍 Start New LCA Assessment", use_container_width=True, type="primary"):
            st.session_state.current_page = 'Data Input'
            st.rerun()
    
    with col2:
        if st.button("📊 View Detailed Analytics", use_container_width=True):
            st.session_state.current_page = 'LCA Analysis'
            st.rerun()
    
    with col3:
        if st.button("📄 Generate Report", use_container_width=True):
            st.session_state.current_page = 'Report'
            st.rerun()

def show_data_input():
    st.markdown('<div class="content-header">Data Input</div>', unsafe_allow_html=True)
    st.markdown('<div class="breadcrumb">Home > Data Input</div>', unsafe_allow_html=True)
    
    # Create a centered form container matching Figma design
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("""
        <div style="
            background: white;
            padding: 3rem;
            border-radius: 12px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.1);
            border: 1px solid #e5e7eb;
            margin: 2rem 0;
        ">
        """, unsafe_allow_html=True)
        
    # Form fields as seen in Figma
        st.markdown("### Transport Parameters")
        
        # Distance field
        distance = st.text_input(
            "Distance (km):",
            placeholder="Enter distance in kilometers",
            help="Total distance for transportation"
        )
        
        # Mode of Transport dropdown
        transport_mode = st.selectbox(
            "Mode of Transport:",
            ["Select transport mode", "Road - Truck", "Road - Car", "Rail - Freight", "Air - Cargo", "Sea - Freight"],
            help="Select the primary mode of transportation"
        )
        
        # Fuel Type dropdown
        fuel_type = st.selectbox(
            "Fuel Type:",
            ["Select fuel type", "Diesel", "Gasoline", "Electric", "Hybrid", "Natural Gas", "Hydrogen"],
            help="Select the fuel type used"
        )
        
    # Expected Product Lifetime
        st.markdown("### Product Information")
        
        product_lifetime = st.selectbox(
            "Expected product lifetime (years):",
            ["Select lifetime", "1-2 years", "3-5 years", "6-10 years", "11-15 years", "16-20 years", "20+ years"],
            help="Expected operational lifetime of the product"
        )
        
        # Energy Consumption
        energy_consumption = st.selectbox(
            "Energy Consumption (kWh/year):",
            ["Select energy consumption", "< 100 kWh", "100-500 kWh", "500-1000 kWh", "1000-2000 kWh", "2000-5000 kWh", "> 5000 kWh"],
            help="Annual energy consumption estimate"
        )
        
        # End of life treatment
        eol_treatment = st.text_input(
            "End of life treatment:",
            placeholder="Describe end-of-life treatment",
            help="How the product will be disposed of or recycled"
        )
        
        # Recycling rate
        recycling_rate = st.slider(
            "Recycling rate (%):",
            min_value=0,
            max_value=100,
            value=50,
            help="Percentage of materials that can be recycled"
        )
        
        # Reuse Potential
        reuse_potential = st.text_input(
            "Reuse Potential (%):",
            placeholder="Enter reuse potential percentage",
            help="Percentage of product that can be reused"
        )
        
        st.markdown("<br>", unsafe_allow_html=True)

        # Additional minimal inputs for LCA schema
        st.markdown("### LCA Basics")
        metal = st.selectbox(
            "Metal:",
            ["Select metal", "Aluminum", "Copper", "Steel", "Zinc"],
            help="Primary metal under assessment",
            key="metal_select",
        )
        process_route = st.selectbox(
            "Process Route:",
            ["Select route", "primary", "recycled", "mixed"],
            help="Production pathway",
            key="process_route_select",
        )
        functional_unit = st.selectbox(
            "Functional unit:",
            ["1 kg", "1 piece", "1 m²", "1 year of service"],
            help="Defines the basis for the LCA",
            key="fu_select",
        )
        system_boundary = st.selectbox(
            "System boundary:",
            ["Cradle-to-Gate", "Cradle-to-Grave", "Gate-to-Gate", "Cradle-to-Cradle", "Gate-to-Grave"],
            index=1,
            help="Scope of the assessment",
            key="sb_select",
        )
        
        # Action buttons matching Figma design
        col_btn1, col_btn2, col_btn3 = st.columns([1, 1, 1])
        
        with col_btn2:
            if st.button("NEXT ➡", use_container_width=True, type="primary"):
                # Build a minimal user_input payload for the Query Parser Agent
                ui_payload = {
                    "metal": None if metal == "Select metal" else metal.lower(),
                    "process_route": None if process_route == "Select route" else process_route,
                    "functional_unit": {"unit": "kg" if functional_unit == "1 kg" else functional_unit, "value": 1.0},
                    "system_boundary": system_boundary,
                    "transport": {
                        "mode": None if transport_mode == "Select transport mode" else transport_mode.split(" - ")[0].lower(),
                        "distance_km": float(distance) if distance else None,
                        "fuel_type": None if fuel_type == "Select fuel type" else fuel_type.lower(),
                    },
                    "product": {
                        "lifetime_years": None,
                        "energy_consumption_kwh_year": None,
                    },
                    "end_of_life": {
                        "recycling_rate_pct": float(recycling_rate) if recycling_rate is not None else None,
                        "reuse_pct": float(reuse_potential) if (reuse_potential or reuse_potential == 0) else None,
                        # landfill_pct will be derived
                    },
                    "notes": eol_treatment or None,
                }

                # Call Query Parser Agent
                completed, issues, prov = parse_and_complete(ui_payload)

                # Store in session for downstream agents
                st.session_state["query_payload"] = completed
                st.session_state["query_provenance"] = prov
                st.session_state["query_issues"] = issues

                # Basic validation feedback
                if issues:
                    st.warning("Some fields were inferred or remain ambiguous. Review in LCA Analysis page.")
                else:
                    st.success("✅ Inputs completed and validated.")

                st.session_state.current_page = 'LCA Analysis'
                st.rerun()
        
        st.markdown('</div>', unsafe_allow_html=True)

def show_lca_analysis():
    st.markdown('<div class="content-header">LCA Analysis</div>', unsafe_allow_html=True)
    st.markdown('<div class="breadcrumb">Home > LCA Analysis</div>', unsafe_allow_html=True)
    
    # Create a centered form container matching Figma design
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("""
        <div style="
            background: white;
            padding: 3rem;
            border-radius: 12px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.1);
            border: 1px solid #e5e7eb;
            margin: 2rem 0;
        ">
        """, unsafe_allow_html=True)
        
        # LCA Analysis form fields as seen in Figma
        st.markdown("### LCA Parameters")
        
        # Metals/Materials dropdown
        metals_materials = st.selectbox(
            "Metals/Materials:",
            ["Select materials", "Steel", "Aluminum", "Copper", "Plastic - PET", "Plastic - PP", "Glass", "Concrete", "Wood", "Composite Materials"],
            help="Select the primary materials used in the product"
        )
        
        # Functional units dropdown
        functional_units = st.selectbox(
            "Functional units:",
            ["Select functional unit", "1 kg product", "1 piece", "1 m²", "1 m³", "1 liter", "1 year of service", "1 km transport"],
            help="Define the functional unit for the LCA assessment"
        )
        
        # System Boundary dropdown
        system_boundary = st.selectbox(
            "System Boundary:",
            ["Select system boundary", "Cradle-to-Gate", "Cradle-to-Grave", "Gate-to-Gate", "Cradle-to-Cradle", "Gate-to-Grave"],
            help="Define the scope of the life cycle assessment"
        )
        
        st.markdown("### Assessment Scope")
        
        # Additional LCA-specific fields
        impact_categories = st.multiselect(
            "Impact Categories:",
            ["Climate Change", "Ozone Depletion", "Acidification", "Eutrophication", "Land Use", "Water Use", "Resource Depletion"],
            default=["Climate Change", "Water Use"],
            help="Select the environmental impact categories to assess"
        )
        
        allocation_method = st.selectbox(
            "Allocation Method:",
            ["Select allocation method", "Mass Allocation", "Economic Allocation", "Energy Allocation", "No Allocation"],
            help="Choose the allocation method for multi-output processes"
        )
        
        assessment_period = st.selectbox(
            "Assessment Period:",
            ["Select time period", "1 year", "5 years", "10 years", "Product lifetime", "Custom period"],
            help="Define the time period for the assessment"
        )
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Action buttons matching Figma design
        col_btn1, col_btn2, col_btn3 = st.columns([1, 1, 1])
        
        with col_btn2:
            if st.button("NEXT ➡", use_container_width=True, type="primary"):
                if (metals_materials != "Select materials" and 
                    functional_units != "Select functional unit" and 
                    system_boundary != "Select system boundary"):
                    st.success("✅ LCA parameters configured successfully!")
                    st.session_state.current_page = 'Report'
                    st.rerun()
                else:
                    st.error("❌ Please fill in all required LCA parameters")
        
        st.markdown('</div>', unsafe_allow_html=True)

def show_optimization():
    st.markdown('<div class="content-header">Optimization</div>', unsafe_allow_html=True)
    st.markdown('<div class="breadcrumb">Home > Optimization</div>', unsafe_allow_html=True)
    
    # Optimization metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Energy Efficiency", "94.2%", "5.1%")
    with col2:
        st.metric("Cost Reduction", "$15,420", "12%")
    with col3:
        st.metric("Process Time", "23.4 min", "-18%")
    with col4:
        st.metric("Resource Usage", "87.6%", "-7%")
    
    # Optimization parameters
    st.subheader("Optimization Parameters")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Current Settings")
        st.slider("Energy Threshold", 0, 100, 85, help="Energy efficiency target percentage")
        st.slider("Cost Target", 0, 50000, 25000, help="Target cost reduction in USD")
        st.selectbox("Optimization Method", ["Genetic Algorithm", "Particle Swarm", "Simulated Annealing"])
        
    with col2:
        st.subheader("Optimization Results")
        optimization_data = pd.DataFrame({
            'Parameter': ['Energy Use', 'Material Cost', 'Production Time', 'Waste Reduction'],
            'Before': [100, 100, 100, 100],
            'After': [85, 78, 67, 45],
            'Improvement': ['15%', '22%', '33%', '55%']
        })
        st.table(optimization_data)
    
    # Run optimization
    if st.button("Run Optimization Analysis", type="primary"):
        with st.spinner("Running optimization algorithm..."):
            import time
            time.sleep(2)  # Simulate processing
            st.success("Optimization completed! New parameters have been calculated.")
            st.balloons()

def show_qa_analysis():
    st.markdown('<div class="content-header">QA Analysis</div>', unsafe_allow_html=True)
    st.markdown('<div class="breadcrumb">Home > QA Analysis</div>', unsafe_allow_html=True)
    
    # QA Metrics
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Test Cases", "1,247", "5%")
    with col2:
        st.metric("Pass Rate", "94.2%", "2.1%")
    with col3:
        st.metric("Defects Found", "23", "-15%")
    
    # QA Analysis Table
    st.subheader("Recent Test Results")
    
    qa_data = pd.DataFrame({
        'Test ID': ['TC001', 'TC002', 'TC003', 'TC004', 'TC005'],
        'Test Name': ['Login Functionality', 'Data Validation', 'API Response', 'UI Elements', 'Performance'],
        'Status': ['Pass', 'Pass', 'Fail', 'Pass', 'Pass'],
        'Execution Date': ['2024-01-15', '2024-01-15', '2024-01-14', '2024-01-14', '2024-01-13'],
        'Tester': ['John Doe', 'Jane Smith', 'Bob Wilson', 'Alice Brown', 'Charlie Davis']
    })
    
    st.dataframe(qa_data, use_container_width=True)

def show_report():
    st.markdown('<div class="content-header">📊 Recycling & Circularity Report</div>', unsafe_allow_html=True)
    st.markdown('<div class="breadcrumb">Home > Reports</div>', unsafe_allow_html=True)
    
    # Main layout
    main_col1, main_col2 = st.columns([7, 3])
    
    with main_col1:
        # Central section - simplified
        st.markdown('<div style="background: white; padding: 2rem; border-radius: 16px; text-align: center;"><h3 style="color: #667eea;">Recycling & Circularity: The Metal Lifecycle</h3></div>', unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Process steps
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.markdown('<div style="background: white; padding: 1rem; border-radius: 8px; text-align: center; border: 2px solid #667eea;"><div style="font-size: 2rem;">📱</div><div style="color: #667eea;">Collection</div></div>', unsafe_allow_html=True)
        with col2:
            st.markdown('<div style="background: white; padding: 1rem; border-radius: 8px; text-align: center; border: 2px solid #667eea;"><div style="font-size: 2rem;">🏭</div><div style="color: #667eea;">Processing</div></div>', unsafe_allow_html=True)
        with col3:
            st.markdown('<div style="background: white; padding: 1rem; border-radius: 8px; text-align: center; border: 2px solid #667eea;"><div style="font-size: 2rem;">📦</div><div style="color: #667eea;">Production</div></div>', unsafe_allow_html=True)
        with col4:
            st.markdown('<div style="background: white; padding: 1rem; border-radius: 8px; text-align: center; border: 2px solid #667eea;"><div style="font-size: 2rem;">�</div><div style="color: #667eea;">Transport</div></div>', unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Central recycling metric
        st.markdown('<div style="background: linear-gradient(135deg, #667eea, #764ba2); padding: 2rem; border-radius: 12px; text-align: center; color: white;"><div style="font-size: 3rem;">♻️</div><h4>Recycled Content:</h4><div style="font-size: 3rem; font-weight: bold;">75%</div><p>in new products</p></div>', unsafe_allow_html=True)
    
    with main_col2:
        # CO2 Emissions Chart
        st.markdown('<div style="background: white; padding: 1.5rem; border-radius: 12px; margin-bottom: 1rem;"><h4 style="color: #667eea; text-align: center;">CO₂ Emission Savings from Recycling</h4></div>', unsafe_allow_html=True)
        
        # Simple bars using metrics
        col_a, col_b = st.columns(2)
        with col_a:
            st.metric("Virgin Metal", "200%", delta=None)
        with col_b:
            st.metric("Recycled", "80%", delta="-60%")
        
        st.success("→ 60% Reduction in CO₂")
        
        # Collection Rate
        st.markdown('<div style="background: white; padding: 1.5rem; border-radius: 12px; margin: 1rem 0; text-align: center;"><h4 style="color: #667eea;">End-of-Life Collection Rate</h4><div style="font-size: 3rem; color: #667eea; font-weight: bold;">82%</div><div style="color: #6b7280;">Materials Collected</div><div style="color: #ef4444; font-size: 0.8rem;">18% Lost to Landfill</div></div>', unsafe_allow_html=True)
        
        # Resource Efficiency
        st.markdown('<div style="background: white; padding: 1.5rem; border-radius: 12px;"><h4 style="color: #667eea; text-align: center;">Resource Efficiency Over Time</h4><div style="color: #10b981; text-align: center; font-weight: 600;">📈 Trending Upward</div></div>', unsafe_allow_html=True)
    
    # KPI Section - simplified and clean
    st.markdown("<br>", unsafe_allow_html=True)
    st.subheader("📈 Key Performance Indicators")
    
    kpi_col1, kpi_col2, kpi_col3, kpi_col4 = st.columns(4)
    
    with kpi_col1:
        st.metric("🌍 Carbon Savings", "2,847 kg", "CO₂ Reduced")
    
    with kpi_col2:
        st.metric("⚡ Energy Saved", "1,320 kWh", "This Month")
    
    with kpi_col3:
        st.metric("♻️ Recovery Rate", "92%", "Material Recovery")
    
    with kpi_col4:
        st.metric("📊 Efficiency Score", "8.6/10", "Overall Rating")
    
    # Data Table
    st.markdown("<br>", unsafe_allow_html=True)
    st.subheader("📋 Detailed Metrics Analysis")
    
    # Create sample data
    import pandas as pd
    report_data = pd.DataFrame({
        'Metal Type': ['Aluminum', 'Copper', 'Steel', 'Lead', 'Zinc'],
        'Recycled Content (%)': [75, 68, 82, 91, 73],
        'CO₂ Savings (kg)': [847, 523, 892, 341, 244],
        'Collection Rate (%)': [82, 79, 88, 94, 76],
        'Efficiency Score': [8.6, 7.9, 9.1, 9.4, 7.8],
        'Status': ['✅ Optimized', '⚠️ Improving', '✅ Excellent', '✅ Excellent', '⚠️ Improving']
    })
    
    st.dataframe(report_data, use_container_width=True)
    
    # Action Buttons
    st.markdown("<br>", unsafe_allow_html=True)
    action_col1, action_col2, action_col3, action_col4 = st.columns(4)
    
    with action_col1:
        if st.button("📥 Download Report", key="download_report", use_container_width=True, type="primary"):
            st.success("✅ Report downloaded successfully!")
    
    with action_col2:
        if st.button("📧 Email Report", key="email_report", use_container_width=True):
            st.info("📧 Report sent to stakeholders")
    
    with action_col3:
        if st.button("📊 Export Data", key="export_data", use_container_width=True):
            st.success("💾 Data exported to CSV")
    
    with action_col4:
        if st.button("🔄 Refresh Data", key="refresh_data", use_container_width=True):
            st.rerun()

def show_organization():
    st.markdown('<div class="content-header">Organization</div>', unsafe_allow_html=True)
    st.markdown('<div class="breadcrumb">Home > Organization</div>', unsafe_allow_html=True)
    
    # Organization structure
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.subheader("Departments")
        departments = ["Engineering", "Marketing", "Sales", "HR", "Finance", "Operations"]
        selected_dept = st.selectbox("Select Department", departments)
    
    with col2:
        st.subheader(f"{selected_dept} Team")
        
        if selected_dept == "Engineering":
            team_data = pd.DataFrame({
                'Name': ['John Doe', 'Jane Smith', 'Bob Wilson'],
                'Role': ['Senior Developer', 'Frontend Developer', 'DevOps Engineer'],
                'Experience': ['5 years', '3 years', '4 years']
            })
        else:
            team_data = pd.DataFrame({
                'Name': ['Alice Brown', 'Charlie Davis'],
                'Role': ['Team Lead', 'Specialist'],
                'Experience': ['6 years', '2 years']
            })
        
        st.table(team_data)

def show_settings():
    st.markdown('<div class="content-header">Settings</div>', unsafe_allow_html=True)
    st.markdown('<div class="breadcrumb">Home > Settings</div>', unsafe_allow_html=True)
    
    # Settings tabs
    tab1, tab2, tab3 = st.tabs(["General", "Security", "Notifications"])
    
    with tab1:
        st.subheader("General Settings")
        col1, col2 = st.columns(2)
        
        with col1:
            st.text_input("Organization Name", value="Fulcrum Analytics")
            st.selectbox("Time Zone", ["UTC", "EST", "PST", "CST"])
            st.selectbox("Language", ["English", "Spanish", "French"])
        
        with col2:
            st.text_input("Admin Email", value="admin@fulcrum.com")
            st.selectbox("Date Format", ["MM/DD/YYYY", "DD/MM/YYYY", "YYYY-MM-DD"])
            st.selectbox("Currency", ["USD", "EUR", "GBP"])
    
    with tab2:
        st.subheader("Security Settings")
        st.checkbox("Enable Two-Factor Authentication", value=True)
        st.checkbox("Require Strong Passwords", value=True)
        st.checkbox("Auto-lock after inactivity", value=False)
        st.slider("Session timeout (minutes)", 15, 480, 60)
    
    with tab3:
        st.subheader("Notification Settings")
        st.checkbox("Email notifications", value=True)
        st.checkbox("Push notifications", value=False)
        st.checkbox("SMS alerts", value=False)
        st.checkbox("Weekly reports", value=True)
    
    st.button("Save Settings", type="primary")

if __name__ == "__main__":
    main()