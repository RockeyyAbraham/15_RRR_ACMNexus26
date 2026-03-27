import streamlit as st
import pandas as pd
import numpy as np
import time

st.set_page_config(
    page_title="SENTINEL_NODE",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Hide Streamlit Sidebar effectively via CSS
hide_sidebar_style = """
    <style>
        [data-testid="stSidebar"] {
            background-color: #121415;
            border-right: 1px solid #222;
            width: 80px !important;
        }
    </style>
"""
with open("frontend/assets/style.css") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
st.markdown(hide_sidebar_style, unsafe_allow_html=True)

# Fake mini sidebar using raw markdown in st.sidebar
with st.sidebar:
    st.markdown("<div style='text-align: center; color: #555; font-size: 20px; font-weight: bold;'>=</div>", unsafe_allow_html=True)
    st.markdown("<br><br><br><br><br><br><br><br><br><br>", unsafe_allow_html=True)

# Top Navbar
st.markdown("""
<div class="navbar">
    <div style="font-size: 1.6em; color: #CCFF00; margin-right: 40px; font-weight: 800; letter-spacing: 2px;">SENTINEL_NODE</div>
    <div class="tab active-tab">INGEST</div>
    <div class="tab">DETECTION</div>
    <div class="tab">EVIDENCE</div>
    <div class="tab">LEGAL</div>
    <div style="flex-grow: 1;"></div>
    <div style="color: #666; font-size: 0.8em; border: 1px solid #222; padding: 10px 20px; border-radius: 4px; background-color: #1C1D1F;">((•)) NODE_8829-X_ACTIVE</div>
</div>
""", unsafe_allow_html=True)

# Main Content Layout
left_col, right_col = st.columns([3, 1], gap="large")

with left_col:
    # "SYSTEM: OPERATIONAL" tag
    st.markdown("""
        <div style='font-size: 0.8em; color: #CCFF00; font-weight: 800; letter-spacing: 1.5px; margin-bottom: 5px;'>
            <span style='display:inline-block; width:10px; height:10px; border-radius:50%; background-color:#CCFF00; margin-right:8px;'></span>SYSTEM: OPERATIONAL
        </div>
    """, unsafe_allow_html=True)
    
    st.markdown("<div style='font-size: 3em; font-weight: 800; color: #FFF; margin-bottom: 40px; line-height: 1;'>Ingest Portal</div>", unsafe_allow_html=True)
    
    inner_left, inner_right = st.columns([1.6, 1], gap="medium")
    
    with inner_left:
        st.markdown("<div style='font-size: 0.7em; color:#8c8c8c; margin-bottom: 15px; letter-spacing: 1.5px;'>REFERENCE VIDEO SOURCE</div>", unsafe_allow_html=True)
        uploaded_file = st.file_uploader("DRAG_DROP_VIDEO_SOURCE", type=["mp4", "mkv", "mov"], label_visibility="collapsed")
        
    with inner_right:
        st.markdown("<div style='font-size: 0.7em; color:#8c8c8c; margin-bottom: -15px; letter-spacing: 1.5px;'>LEAGUE NAME</div>", unsafe_allow_html=True)
        league = st.text_input("League", value="EURO_PREMIER_CHAMPIONSHIP", label_visibility="collapsed")
        
        st.markdown("<div style='font-size: 0.7em; color:#8c8c8c; margin-top: 10px; margin-bottom: -15px; letter-spacing: 1.5px;'>MATCH ID</div>", unsafe_allow_html=True)
        match_id = st.text_input("Match", value="UUID_88392_B", label_visibility="collapsed")
        
        st.markdown("<div style='font-size: 0.7em; color:#8c8c8c; margin-top: 10px; margin-bottom: -15px; letter-spacing: 1.5px;'>BROADCAST DATE</div>", unsafe_allow_html=True)
        b_date = st.text_input("Date", value="2023-10-24", label_visibility="collapsed")
        
        st.markdown("<br>", unsafe_allow_html=True)
        generate_clicked = st.button("🧬 GENERATE_FINGERPRINT", use_container_width=True)
        
        if generate_clicked:
            if uploaded_file is None:
                st.error("Please upload a video source first.")
            else:
                with st.spinner("Analyzing media stream..."):
                    time.sleep(2)
                st.success("Fingerprint generated and dispatched to Global Sync.")
    
    st.markdown("<br><br>", unsafe_allow_html=True)
    
    # Progress Indicators
    p_col1, p_col2 = st.columns(2, gap="medium")
    with p_col1:
        st.markdown("""
        <div class="progress-container">
            <div class="progress-label"><span>VIDEO_PHASH</span><span class="ready">READY</span></div>
            <div class="progress-bar-bg"><div class="progress-bar-fill yellow"></div></div>
        </div>
        """, unsafe_allow_html=True)
    with p_col2:
        st.markdown("""
        <div class="progress-container">
            <div class="progress-label"><span>AUDIO_SPECTROGRAM</span><span class="pending">ANALYSIS PENDING</span></div>
            <div class="progress-bar-bg"><div class="progress-bar-fill blue"></div></div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br><br><br>", unsafe_allow_html=True)
    
    # Log Cards - perfectly styled
    c1, c2, c3 = st.columns(3, gap="medium")
    with c1:
        st.markdown("""
        <div class="log-card blue-bar">
            <div style="font-size: 0.8em; color:#888; margin-bottom:8px; font-weight:bold; letter-spacing:1px;">EVENT_LOG_ID_092</div>
            Encrypted manifest verified at T-0ms. Local node handshake successful.
        </div>
        """, unsafe_allow_html=True)
    with c2:
        st.markdown("""
        <div class="log-card yellow-bar">
            <div style="font-size: 0.8em; color:#CCFF00; margin-bottom:8px; font-weight:bold; letter-spacing:1px;">NODE_LATENCY</div>
            Global sync offset: 0.002ms.<br>High-fidelity extraction active.
        </div>
        """, unsafe_allow_html=True)
    with c3:
        st.markdown("""
        <div class="log-card grey-bar">
            <div style="font-size: 0.8em; color:#888; margin-bottom:8px; font-weight:bold; letter-spacing:1px;">GEO_REDUNDANCY</div>
            Paris-IX and US-East data mirroring locked. Backup secure.
        </div>
        """, unsafe_allow_html=True)


with right_col:
    st.markdown("<div style='font-size: 0.7em; color:#8c8c8c; margin-bottom: 5px; font-weight:bold; letter-spacing: 1.5px;'>GLOBAL INTEGRITY MONITOR</div>", unsafe_allow_html=True)
    st.markdown("<div style='font-size: 1.4em; font-weight:800; margin-bottom: 25px; color:#FFF; letter-spacing:1px;'>INTELLIGENCE FEED</div>", unsafe_allow_html=True)
    
    st.markdown("""
    <div class="metric-container">
        <div class="metric-title">TOTAL_PROTECTED_HASHES</div>
        <div class="metric-value">14,209 <span style="font-size: 0.35em; color: #888; font-weight: normal; vertical-align: middle;">+24h: 182</span></div>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("""
    <div class="metric-container" style="display:flex; justify-content: space-between; align-items: center;">
        <div>
            <div class="metric-title">SYSTEM_SYNC</div>
            <div class="metric-value" style="font-size: 1.25em;">STABLE</div>
        </div>
        <div style="background-color: #CCFF00; border-radius: 50%; width: 28px; height: 28px; display:inline-flex; justify-content:center; align-items:center; color:#121415; font-weight:bold; font-size:1.2em;">✓</div>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("<br><div style='font-size: 0.7em; color:#8c8c8c; margin-bottom: 15px; font-weight:bold; letter-spacing: 1.5px;'>NODE_TRAFFIC_HEATMAP</div>", unsafe_allow_html=True)
    
    # Real looking traffic heatmap substitute via st.area_chart
    chart_data = pd.DataFrame(
        np.array([12, 13, 11, 15, 14, 20, 18, 14, 15, 16, 12, 14, 15, 22, 25, 21, 19, 15, 12, 11]),
        columns=["Traffic"]
    )
    # Applying a black/grey color via CSS isn't fully possible here via pure streamlit but green matches the vibe
    st.area_chart(chart_data, color="#CCFF00", height=200)
    
    st.markdown("<div style='flex-grow: 1; height: 180px;'></div>", unsafe_allow_html=True)
    
    st.markdown("""
    <div style="font-size: 0.7em; color:#888; margin-bottom:8px; font-weight:bold; letter-spacing:1px;">ACTIVE_CONTROLLERS</div>
    <div style="display:flex; gap: 8px; margin-bottom: 25px;">
        <div style="width: 25px; height: 25px; border-radius:50%; background-color:#333;"></div>
        <div style="width: 25px; height: 25px; border-radius:50%; background-color:#2b70c9;"></div>
        <div style="width: 25px; height: 25px; border-radius:50%; background-color:#CCFF00;"></div>
        <div style="font-size:0.8em; margin-left:8px; align-self:center; font-weight:bold; color:#888;">+4</div>
    </div>
    """, unsafe_allow_html=True)

# Footer bar to mimic the absolute bottom text
st.markdown("""
<div style="position:fixed; bottom:0; left:0; width:100%; height:40px; background-color:#121415; border-top:1px solid #222; display:flex; justify-content:space-between; align-items:center; padding: 0 30px; z-index:99999;">
    <div style="font-size:0.7em; color:#888; font-weight:bold; letter-spacing:1px;">
        <span style="color:#CCFF00; margin-right:15px;"">NODE_01</span>
        SENTINEL_NODE // GLOBAL_INTELLIGENCE_FRAMEWORK
    </div>
    <div style="display:flex; gap:30px; font-size:0.7em; font-weight:bold; letter-spacing:1px;">
        <span style="color:#CCFF00;">WS_CONNECTED</span>
        <span style="color:#555;">LOAD: 14%</span>
        <span style="color:#555;">NODE_ID: 8829-X</span>
    </div>
</div>
""", unsafe_allow_html=True)
