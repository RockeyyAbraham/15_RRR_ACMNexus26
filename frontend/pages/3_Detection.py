import streamlit as st
import pandas as pd
import numpy as np
import time
from datetime import datetime, timedelta

st.set_page_config(page_title="Detection - SENTINEL", layout="wide", initial_sidebar_state="expanded")

with open("frontend/assets/style.css") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

st.markdown("""
<div class="navbar">
    <div style="font-size: 1.6em; color: #CCFF00; margin-right: 40px; font-weight: 800; letter-spacing: 2px;">SENTINEL_NODE</div>
    <div class="tab"><a href="?page=1_Dashboard" style="color: #8c8c8c; text-decoration: none;">DASHBOARD</a></div>
    <div class="tab"><a href="?page=2_Ingest" style="color: #8c8c8c; text-decoration: none;">INGEST</a></div>
    <div class="tab active-tab">DETECTION</div>
    <div class="tab"><a href="?page=4_Evidence" style="color: #8c8c8c; text-decoration: none;">EVIDENCE</a></div>
    <div class="tab"><a href="?page=5_Legal" style="color: #8c8c8c; text-decoration: none;">LEGAL</a></div>
    <div style="flex-grow: 1;"></div>
    <div style="color: #666; font-size: 0.8em; border: 1px solid #222; padding: 10px 20px; border-radius: 4px; background-color: #1C1D1F;">((•)) NODE_8829-X_ACTIVE</div>
</div>
""", unsafe_allow_html=True)

# Top metrics row
top_left, top_right = st.columns([2, 1], gap="large")

with top_left:
    col1, col2 = st.columns(2, gap="medium")
    with col1:
        st.markdown("""
        <div class="info-metric">
            <div class="title">ACTIVE_SESSIONS</div>
            <div class="val">03 /NODE_CLUSTER</div>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown("""
        <div class="info-metric">
            <div class="title">ENCRYPTION_STATUS</div>
            <div class="val">AES-256</div>
        </div>
        """, unsafe_allow_html=True)

with top_right:
    st.markdown("""
    <div class="threat-level">
        <div class="label">PEAK_THREAT_LEVEL</div>
        <div class="value">CRITICAL ||| !</div>
    </div>
    """, unsafe_allow_html=True)

# Main content area
main_left, main_right = st.columns([2, 1], gap="large")

with main_left:
    st.markdown("<div style='font-size: 1.8em; font-weight: 800; color: #FFF; margin-bottom: 20px;'>DETECTION_FEED</div>", unsafe_allow_html=True)
    
    # Detection feed items
    st.markdown("""
    <div class="detection-feed">
        <div class="detection-item">
            <div class="platform">TWITCH.TV/LIVE_STREAM_8829</div>
            <div class="timestamp">2024-03-27 18:42:15 UTC</div>
            <div class="confidence">CONFIDENCE: 98.7%</div>
            <div class="hash">HASH: 0x7F3A9B2C1D8E4F5A6B7C8D9E0F1A2B3C</div>
        </div>
        <div class="detection-item">
            <div class="platform">YOUTUBE.COM/VIDEO_ABC123</div>
            <div class="timestamp">2024-03-27 18:41:32 UTC</div>
            <div class="confidence">CONFIDENCE: 95.2%</div>
            <div class="hash">HASH: 0x9C8D7E6F5A4B3C2D1E0F9A8B7C6D5E4F</div>
        </div>
        <div class="detection-item">
            <div class="platform">FACEBOOK.COM/STREAM_XYZ789</div>
            <div class="timestamp">2024-03-27 18:40:18 UTC</div>
            <div class="confidence">CONFIDENCE: 91.8%</div>
            <div class="hash">HASH: 0x2B3C4D5E6F7A8B9C0D1E2F3A4B5C6D7E</div>
        </div>
        <div class="detection-item">
            <div class="platform">TWITCH.TV/LIVE_STREAM_4456</div>
            <div class="timestamp">2024-03-27 18:39:45 UTC</div>
            <div class="confidence">CONFIDENCE: 89.3%</div>
            <div class="hash">HASH: 0x7E8F9A0B1C2D3E4F5A6B7C8D9E0F1A2B</div>
        </div>
        <div class="detection-item">
            <div class="platform">DISCORD.GG/CHANNEL_PRIVATE</div>
            <div class="timestamp">2024-03-27 18:38:22 UTC</div>
            <div class="confidence">CONFIDENCE: 87.6%</div>
            <div class="hash">HASH: 0x3C4D5E6F7A8B9C0D1E2F3A4B5C6D7E8F</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Action buttons
    col1, col2 = st.columns(2, gap="medium")
    with col1:
        if st.button("EXPORT_CSV", type="secondary", use_container_width=True):
            st.success("Detection feed exported to CSV")
    with col2:
        if st.button("CLEAR_LOG", type="secondary", use_container_width=True):
            st.success("Detection log cleared")

with main_right:
    st.markdown("<div style='font-size: 1.2em; font-weight: 800; color: #FFF; margin-bottom: 20px;'>THREAT_CONFIDENCE_HISTORY</div>", unsafe_allow_html=True)
    
    # Generate time series data for the chart
    hours = [f"{i:02d}:00" for i in range(8, 15)]
    confidence_data = pd.DataFrame({
        'Time': hours,
        'Confidence': np.random.randint(75, 99, len(hours))
    })
    
    st.bar_chart(confidence_data.set_index('Time'), color="#CCFF00", height=200)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Global traffic monitor
    st.markdown("""
    <div style='font-size: 0.9em; color: #8c8c8c; margin-bottom: 15px; font-weight:bold; letter-spacing:1px;'>GLOBAL_TRAFFIC_MONITOR</div>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns(2, gap="small")
    with col1:
        st.markdown("""
        <div class="info-metric">
            <div class="title">LATENCY</div>
            <div class="val">12ms</div>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown("""
        <div class="info-metric">
            <div class="title">UPTIME</div>
            <div class="val">99.98%</div>
        </div>
        """, unsafe_allow_html=True)

# Footer
st.markdown("<br><br>", unsafe_allow_html=True)
st.markdown("""
<div style="position:fixed; bottom:0; left:0; width:100%; height:40px; background-color:#121415; border-top:1px solid #222; display:flex; justify-content:space-between; align-items:center; padding: 0 30px; z-index:99999;">
    <div style="font-size:0.75em; color:#666; font-weight:bold; letter-spacing:1px; display:flex; align-items:center;">
        <span style="display:inline-block; width:20px; height:20px; background-color:#2a2c2e; border: 1px solid #3a3c3e; margin-right: 15px;"></span>
        SENTINEL_NODE // GLOBAL_INTELLIGENCE_FRAMEWORK
    </div>
    <div style="display:flex; gap:30px; font-size:0.7em; font-weight:bold; letter-spacing:1px;">
        <span style="color:#CCFF00;">WS_CONNECTED</span>
        <span style="color:#555;">LOAD: 14%</span>
        <span style="color:#555;">NODE_ID: 8829-X</span>
    </div>
</div>
""", unsafe_allow_html=True)
