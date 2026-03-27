import streamlit as st
import pandas as pd
import numpy as np
import time

st.set_page_config(page_title="Legal - SENTINEL", layout="wide", initial_sidebar_state="expanded")

with open("frontend/assets/style.css") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

st.markdown("""
<div class="navbar">
    <div style="font-size: 1.6em; color: #CCFF00; margin-right: 40px; font-weight: 800; letter-spacing: 2px;">SENTINEL_NODE</div>
    <div class="tab"><a href="?page=1_Dashboard" style="color: #8c8c8c; text-decoration: none;">DASHBOARD</a></div>
    <div class="tab"><a href="?page=2_Ingest" style="color: #8c8c8c; text-decoration: none;">INGEST</a></div>
    <div class="tab"><a href="?page=3_Detection" style="color: #8c8c8c; text-decoration: none;">DETECTION</a></div>
    <div class="tab"><a href="?page=4_Evidence" style="color: #8c8c8c; text-decoration: none;">EVIDENCE</a></div>
    <div class="tab active-tab">LEGAL</div>
    <div style="flex-grow: 1;"></div>
    <div style="color: #666; font-size: 0.8em; border: 1px solid #222; padding: 10px 20px; border-radius: 4px; background-color: #1C1D1F;">((•)) NODE_8829-X_ACTIVE</div>
</div>
""", unsafe_allow_html=True)

# Main content
st.markdown("<div style='font-size: 2.5em; font-weight: 800; color: #FFF; margin-bottom: 10px;'>LEGAL COMPLIANCE</div>", unsafe_allow_html=True)
st.markdown("<div style='font-size: 0.9em; color: #888; margin-bottom: 30px;'>DMCA enforcement and legal document management</div>", unsafe_allow_html=True)

main_col, sidebar_col = st.columns([3, 1], gap="large")

with main_col:
    # Active Cases Section
    st.markdown("<div style='font-size: 1.4em; font-weight: 800; color: #FFF; margin-bottom: 20px;'>Active Legal Cases</div>", unsafe_allow_html=True)
    
    # Cases table
    cases_data = pd.DataFrame({
        'Case ID': ['CASE_001', 'CASE_002', 'CASE_003', 'CASE_004', 'CASE_005'],
        'Platform': ['YouTube', 'Twitch', 'Facebook', 'Twitter', 'Instagram'],
        'Infringement Type': ['Video Stream', 'Live Broadcast', 'Post Content', 'Video Clip', 'Story Content'],
        'Status': ['Under Review', 'Action Required', 'Resolved', 'Pending', 'Under Review'],
        'Priority': ['High', 'Critical', 'Medium', 'Low', 'High'],
        'Filed Date': ['2024-03-27', '2024-03-27', '2024-03-26', '2024-03-26', '2024-03-25']
    })
    
    st.dataframe(
        cases_data,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Case ID": st.column_config.TextColumn("Case ID", width="small"),
            "Platform": st.column_config.TextColumn("Platform", width="small"),
            "Infringement Type": st.column_config.TextColumn("Type", width="medium"),
            "Status": st.column_config.TextColumn("Status", width="small"),
            "Priority": st.column_config.TextColumn("Priority", width="small"),
            "Filed Date": st.column_config.TextColumn("Filed", width="small")
        }
    )
    
    # Action buttons
    col1, col2, col3 = st.columns(3, gap="medium")
    with col1:
        if st.button("NEW CASE", type="primary", use_container_width=True):
            st.info("Opening new case form...")
    with col2:
        if st.button("EXPORT_REPORT", type="secondary", use_container_width=True):
            st.success("Legal report exported")
    with col3:
        if st.button("BULK_ACTION", type="secondary", use_container_width=True):
            st.info("Bulk action options")

with sidebar_col:
    # Legal Statistics
    st.markdown("<div style='font-size: 1.1em; font-weight: 800; color: #FFF; margin-bottom: 15px;'>Legal Statistics</div>", unsafe_allow_html=True)
    
    st.markdown("""
    <div class="metric-container">
        <div class="metric-title">ACTIVE_CASES</div>
        <div class="metric-value">47</div>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("""
    <div class="metric-container">
        <div class="metric-title">RESOLVED_THIS_MONTH</div>
        <div class="metric-value">128</div>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("""
    <div class="metric-container">
        <div class="metric-title">SUCCESS_RATE</div>
        <div class="metric-value">96.2%</div>
    </div>
    """, unsafe_allow_html=True)
    
    # Quick Actions
    st.markdown("<div style='font-size: 1.1em; font-weight: 800; color: #FFF; margin-bottom: 15px; margin-top: 30px;'>Quick Actions</div>", unsafe_allow_html=True)
    
    if st.button("📄 Generate DMCA Template", type="secondary", use_container_width=True):
        st.success("DMCA template generated")
    
    if st.button("⚖️ Legal Review Queue", type="secondary", use_container_width=True):
        st.info("Opening review queue...")
    
    if st.button("📊 Compliance Report", type="secondary", use_container_width=True):
        st.success("Report generated")
    
    # Recent Activity
    st.markdown("<div style='font-size: 1.1em; font-weight: 800; color: #FFF; margin-bottom: 15px; margin-top: 30px;'>Recent Activity</div>", unsafe_allow_html=True)
    
    activities = [
        "CASE_004: Notice sent to Twitter",
        "CASE_003: Resolved - Content removed",
        "CASE_002: Critical priority assigned",
        "CASE_001: Under legal review"
    ]
    
    for activity in activities:
        st.markdown(f"""
        <div style="background-color: #1a1c1e; border-left: 2px solid #CCFF00; padding: 8px 12px; margin-bottom: 8px; font-size: 0.7em; color: #aaa;">
            {activity}
        </div>
        """, unsafe_allow_html=True)

# Footer
st.markdown("<br><br>", unsafe_allow_html=True)
st.markdown("""
<div style="position:fixed; bottom:0; left:0; width:100%; height:40px; background-color:#121415; border-top:1px solid #222; display:flex; justify-content:space-between; align-items:center; padding: 0 30px; z-index:99999;">
    <div style="font-size:0.75em; color:#666; font-weight:bold; letter-spacing:1px; display:flex; align-items:center;">
        <span style="display:inline-block; width:20px; height:20px; background-color:#2a2c2e; border: 1px solid #3a3c3e; margin-right: 15px;"></span>
        SENTINEL_NODE // LEGAL_CORE
    </div>
    <div style="display:flex; gap:30px; font-size:0.7em; font-weight:bold; letter-spacing:1px;">
        <span style="color:#CCFF00;">WS_CONNECTED</span>
        <span style="color:#555;">LOAD: 14%</span>
        <span style="color:#555;">NODE_ID: 8829-X</span>
    </div>
</div>
""", unsafe_allow_html=True)
