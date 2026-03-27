import streamlit as st
import pandas as pd
import numpy as np
import time

st.set_page_config(page_title="Evidence - SENTINEL", layout="wide", initial_sidebar_state="expanded")

with open("frontend/assets/style.css") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

st.markdown("""
<div class="navbar">
    <div style="font-size: 1.6em; color: #CCFF00; margin-right: 40px; font-weight: 800; letter-spacing: 2px;">SENTINEL_NODE</div>
    <div class="tab"><a href="?page=1_Dashboard" style="color: #8c8c8c; text-decoration: none;">DASHBOARD</a></div>
    <div class="tab"><a href="?page=2_Ingest" style="color: #8c8c8c; text-decoration: none;">INGEST</a></div>
    <div class="tab"><a href="?page=3_Detection" style="color: #8c8c8c; text-decoration: none;">DETECTION</a></div>
    <div class="tab active-tab">EVIDENCE</div>
    <div class="tab"><a href="?page=5_Legal" style="color: #8c8c8c; text-decoration: none;">LEGAL</a></div>
    <div style="flex-grow: 1;"></div>
    <div style="color: #666; font-size: 0.8em; border: 1px solid #222; padding: 10px 20px; border-radius: 4px; background-color: #1C1D1F;">((•)) NODE_8829-X_ACTIVE</div>
</div>
""", unsafe_allow_html=True)

# Main content
st.markdown("<div style='font-size: 2.5em; font-weight: 800; color: #FFF; margin-bottom: 10px;'>DMCA MANAGEMENT</div>", unsafe_allow_html=True)
st.markdown("<div style='font-size: 0.9em; color: #888; margin-bottom: 30px;'>Automated takedown notice generation and evidence collection</div>", unsafe_allow_html=True)

main_col, sidebar_col = st.columns([3, 1], gap="large")

with main_col:
    # Generated Notices Section
    st.markdown("<div style='font-size: 1.4em; font-weight: 800; color: #FFF; margin-bottom: 20px;'>Generated Notices</div>", unsafe_allow_html=True)
    
    # Filter and Sort controls
    col1, col2, col3 = st.columns([1, 1, 1], gap="medium")
    with col1:
        platform_filter = st.selectbox("Platform", ["All Platforms", "YouTube", "Twitch", "Facebook", "Twitter"], label_visibility="collapsed")
    with col2:
        status_filter = st.selectbox("Status", ["All Status", "Pending", "Sent", "Resolved"], label_visibility="collapsed")
    with col3:
        sort_by = st.selectbox("Sort by", ["Date Created", "Platform", "Status"], label_visibility="collapsed")
    
    # Notices table
    notices_data = pd.DataFrame({
        'ID': ['NOTICE_001', 'NOTICE_002', 'NOTICE_003', 'NOTICE_004', 'NOTICE_005'],
        'Platform': ['YouTube', 'Twitch', 'Facebook', 'YouTube', 'Twitter'],
        'Content': ['Video_ABC123', 'Stream_XYZ789', 'Post_DEF456', 'Video_GHI789', 'Tweet_JKL012'],
        'Status': ['Sent', 'Pending', 'Resolved', 'Sent', 'Pending'],
        'Date': ['2024-03-27', '2024-03-27', '2024-03-26', '2024-03-26', '2024-03-25']
    })
    
    st.dataframe(
        notices_data,
        use_container_width=True,
        hide_index=True,
        column_config={
            "ID": st.column_config.TextColumn("Notice ID", width="small"),
            "Platform": st.column_config.TextColumn("Platform", width="small"),
            "Content": st.column_config.TextColumn("Content ID", width="medium"),
            "Status": st.column_config.TextColumn("Status", width="small"),
            "Date": st.column_config.TextColumn("Date Created", width="small")
        }
    )
    
    # Pagination
    col1, col2, col3 = st.columns([1, 2, 1], gap="medium")
    with col1:
        if st.button("← Previous", type="secondary", use_container_width=True):
            st.info("Previous page")
    with col3:
        if st.button("Next →", type="secondary", use_container_width=True):
            st.info("Next page")
    with col2:
        st.markdown("<div style='text-align: center; color: #666; font-size: 0.8em; margin-top: 10px;'>Page 1 of 10</div>", unsafe_allow_html=True)

with sidebar_col:
    # Compliance Score
    st.markdown("""
    <div class="compliance-score">
        <div class="score">94.7%</div>
        <div class="label">COMPLIANCE SCORE</div>
    </div>
    """, unsafe_allow_html=True)
    
    # Legal Document Preview
    st.markdown("<div style='font-size: 1.1em; font-weight: 800; color: #FFF; margin-bottom: 15px; margin-top: 30px;'>Legal Document Preview</div>", unsafe_allow_html=True)
    
    st.markdown("""
    <div class="legal-preview">
        <h4 style="color: #CCFF00; margin-bottom: 10px;">DMCA TAKEDOWN NOTICE</h4>
        <p><strong>Date:</strong> March 27, 2024</p>
        <p><strong>To:</strong> Platform Legal Department</p>
        <p><strong>Re:</strong> Unauthorized Distribution of Copyrighted Content</p>
        <br>
        <p>Dear Sir/Madam,</p>
        <p>This letter serves as formal notification under the Digital Millennium Copyright Act (DMCA) that content hosted on your platform infringes upon our exclusive rights.</p>
        <p><strong>Infringing Content Details:</strong></p>
        <ul style="color: #aaa;">
            <li>Content ID: VIDEO_ABC123</li>
            <li>Original Work: EURO_PREMIER_CHAMPIONSHIP Match UUID_88392_B</li>
            <li>Broadcast Date: 2023-10-24</li>
            <li>Fingerprint Hash: 0x7F3A9B2C1D8E4F5A6B7C8D9E0F1A2B3C</li>
        </ul>
        <p>We request immediate removal of this content to prevent further infringement.</p>
        <br>
        <p>Sincerely,<br>SENTINEL Legal Department</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Sign and Dispatch Button
    if st.button("SIGN AND DISPATCH", type="primary", use_container_width=True):
        with st.spinner("Dispatching notice..."):
            time.sleep(2)
        st.success("DMCA notice successfully dispatched to platform")

# Footer
st.markdown("<br><br>", unsafe_allow_html=True)
st.markdown("""
<div style="position:fixed; bottom:0; left:0; width:100%; height:40px; background-color:#121415; border-top:1px solid #222; display:flex; justify-content:space-between; align-items:center; padding: 0 30px; z-index:99999;">
    <div style="font-size:0.75em; color:#666; font-weight:bold; letter-spacing:1px; display:flex; align-items:center;">
        <span style="display:inline-block; width:20px; height:20px; background-color:#2a2c2e; border: 1px solid #3a3c3e; margin-right: 15px;"></span>
        SENTINEL_NODE // EVIDENCE_CORE
    </div>
    <div style="display:flex; gap:30px; font-size:0.7em; font-weight:bold; letter-spacing:1px;">
        <span style="color:#CCFF00;">WS_CONNECTED</span>
        <span style="color:#555;">LOAD: 14%</span>
        <span style="color:#555;">NODE_ID: 8829-X</span>
    </div>
</div>
""", unsafe_allow_html=True)
