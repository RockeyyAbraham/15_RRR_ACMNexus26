import streamlit as st
import pandas as pd
import numpy as np
import time

st.set_page_config(
    page_title="SENTINEL_NODE",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Hide Streamlit Sidebar via CSS
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

# Fake mini sidebar using raw markdown
with st.sidebar:
    st.markdown("<div style='text-align: center; color: #555; border-bottom:1px solid #333; padding-bottom:10px; font-weight: bold;'>~</div>", unsafe_allow_html=True)
    st.markdown("<br><br><br><br><br><br><br><br><br><br>", unsafe_allow_html=True)

# Top Navbar
st.markdown("""
<div class="navbar">
    <div style="font-size: 1.6em; color: #CCFF00; margin-right: 40px; font-weight: 800; letter-spacing: 2px;">SENTINEL_NODE</div>
    <div class="tab">INGEST</div>
    <div class="tab">DETECTION</div>
    <div class="tab active-tab">EVIDENCE</div>
    <div class="tab">LEGAL</div>
    <div style="flex-grow: 1;"></div>
    <div style="color: #CCFF00; font-size: 1.2em; font-weight:bold;">((•))</div>
</div>
""", unsafe_allow_html=True)

# Subheader
st.markdown("""
<div style="display: flex; justify-content: space-between; margin-bottom: 25px;">
    <div>
        <div style='font-size: 0.8em; color: #888; letter-spacing: 1.5px; font-weight:bold; margin-bottom:5px;'>
            <span class="status-indicator"></span>MODULE: EVIDENCE_VIEWER_v4.0.1
        </div>
        <div style='font-size: 2.2em; font-weight: 800; color: #FFF; line-height: 1;'>FORENSIC ANALYSIS</div>
    </div>
    <div style="text-align: right; display: flex; flex-direction: column; justify-content: flex-end;">
        <div style="font-size: 0.7em; color: #888; letter-spacing: 1.5px; font-weight:bold;">TARGET_ID: 0X8829-X-DELTA</div>
        <div style="font-size: 1.1em; color: #CCFF00; font-weight: 800; letter-spacing: 1px;">MATCH_PROBABILITY: 99.8%</div>
    </div>
</div>
""", unsafe_allow_html=True)

# Main Two Columns
col1, col2 = st.columns(2, gap="medium")

with col1:
    st.markdown("""
    <div class="container-box">
        <div class="badge-yellow">ORIGINAL_FRAME_REFERENCE</div>
        
        <div style="height: 350px; background: linear-gradient(135deg, #121415 0%, #1a1c1e 100%); border: 1px solid #222; position:relative; overflow:hidden; display:flex; flex-direction:column; justify-content:space-between; padding:20px;">
            <div style="color:#FFF; font-size:1.5em; letter-spacing:15px; opacity:0.8; text-align:center;">REFEREENENCE FRCE</div>
            
            <!-- Abstract generic shapes simulation -->
            <div style="position:absolute; top:50%; left:50%; transform:translate(-50%, -50%); width: 250px; height: 180px; border:1px solid #333; opacity:0.2; box-shadow: inset 0 0 50px #CCFF00; transform: translate(-50%, -50%) rotate(45deg);"></div>
            <div style="position:absolute; top:50%; left:50%; transform:translate(-50%, -50%); width: 200px; height: 150px; border:1px solid #333; opacity:0.2; box-shadow: inset 0 0 50px #2b70c9; transform: translate(-50%, -50%) rotate(-20deg);"></div>
            
            <div style="color:#FFF; font-size:0.8em; letter-spacing:5px; opacity:0.5;">SAFE SWORE</div>
        </div>
        
        <div style="display:flex; gap: 10px; margin-top: 15px;">
            <div class="info-metric">
                <div class="title">HASH</div>
                <div class="val" style="font-size: 0.7em;">f3e2...9a11</div>
            </div>
            <div class="info-metric">
                <div class="title">RESOLUTION</div>
                <div class="val" style="font-size: 0.7em;">3840x2160</div>
            </div>
            <div class="info-metric">
                <div class="title">PROTOCOL</div>
                <div class="val" style="font-size: 0.7em;">HEVC_S_01</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown("""
    <div class="container-box">
        <div style="text-align:right; margin-bottom:10px;">
            <span class="badge-red">THREAT_LOCATED</span>
        </div>
        
        <div style="height: 350px; background-color:#141516; border: 1px solid #222; position:relative; overflow:hidden; display:flex; flex-direction:column; align-items:center; justify-content:center;">
            <div style="font-size:0.55em; color:#ff6b6b; position:absolute; top:60px; text-align:center; width:100%;">SIGNATURE_MATCH_001</div>
            
            <div style="width: 220px; height: 120px; border: 1px solid #ff4d4d; border-top: 1px solid #ff4d4d; opacity:0.4; position:relative;">
                <div style="border-bottom: 1px solid #ff4d4d; position:absolute; top:50%; width:100%;"></div>
            </div>
            
            <div style="color:#888; font-size:1.5em; letter-spacing:3px; margin-top:40px;">CAPTURE FRAME</div>
            
            <!-- Arrow markers -->
            <div style="color:#333; position:absolute; right:15px; top:15px; font-size:1.2em;">&larr;</div>
            <div style="color:#333; position:absolute; right:15px; bottom:15px; font-size:1.2em;">&larr;</div>
        </div>
        
        <div style="display:flex; gap: 10px; margin-top: 15px;">
            <div class="info-metric">
                <div class="title">SOURCE_IP</div>
                <div class="val red">185.158.113.44</div>
            </div>
            <div class="info-metric">
                <div class="title">LOCATION</div>
                <div class="val red">MOSCOW_REGION [RU]</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

# Wide Signature Module
st.markdown("<div class='container-box' style='padding:15px 20px;'>", unsafe_allow_html=True)
sig_col1, sig_col2 = st.columns([2.5, 1])
with sig_col1:
    st.markdown("""
    <div style="display:flex; justify-content:space-between; margin-bottom: -5px;">
        <div style="font-size:0.8em; color:#888; letter-spacing:1px; font-weight:bold;">DIGITAL_KINETIC_SIGNATURE</div>
        <div style="font-size:0.7em; color:#CCFF00; font-weight:bold; letter-spacing:1px;">VARIANCE_DELTA: +12.4ms</div>
    </div>
    """, unsafe_allow_html=True)
    
    # Mock specific structured bar chart
    bar_data = pd.DataFrame(
        np.array([1, 1, 6, 8, 4, 1, 1, 0, 1, 5, 8, 3, 1, 1, 1, 0]),
        columns=["Amplitude"]
    )
    st.bar_chart(bar_data, color="#CCFF00", height=150)

with sig_col2:
    st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
    btn1 = st.button("[APPROVE_FOR_DMCA]", type="primary", use_container_width=True)
    btn2 = st.button("REJECT_AS_FALSE_POSITIVE", type="secondary", use_container_width=True)
    
    if btn1:
        st.success("DMCA Approval verified sequence initiated.")
    elif btn2:
        st.warning("Flagged as false positive. Learning weights adjusted.")
st.markdown("</div>", unsafe_allow_html=True)


# Bottom Metrics grid
b1, b2, b3, b4 = st.columns(4, gap="medium")
with b1:
    st.markdown("""
    <div class="bottom-metric">
        <div class="title">ACTIVE_NODES</div>
        <div class="val yellow">1,204</div>
    </div>
    """, unsafe_allow_html=True)
with b2:
    st.markdown("""
    <div class="bottom-metric">
        <div class="title">LATENCY_AVG</div>
        <div class="val blue">14ms</div>
    </div>
    """, unsafe_allow_html=True)
with b3:
    st.markdown("""
    <div class="bottom-metric">
        <div class="title">DMCA_BATCH_QUEUE</div>
        <div class="val white">492</div>
    </div>
    """, unsafe_allow_html=True)
with b4:
    st.markdown("""
    <div class="bottom-metric optimal">
        <div class="title">NETWORK_INTEGRITY</div>
        <div class="val white">OPTIMAL</div>
    </div>
    """, unsafe_allow_html=True)


st.markdown("<br><br><br>", unsafe_allow_html=True)

# Footer bar to mimic the absolute bottom text
st.markdown("""
<div style="position:fixed; bottom:0; left:0; width:100%; height:40px; background-color:#121415; border-top:1px solid #222; display:flex; justify-content:space-between; align-items:center; padding: 0 30px; z-index:99999;">
    <div style="font-size:0.7em; color:#666; font-weight:bold; letter-spacing:1px; display:flex; align-items:center;">
        <span style="display:inline-block; width:18px; height:18px; background-color:#2a2c2e; border: 1px solid #3a3c3e; margin-right: 15px; border-radius: 2px;"></span>
        SENTINEL_NODE // GLOBAL_INTELLIGENCE_FRAMEWORK
    </div>
    <div style="display:flex; gap:30px; font-size:0.7em; font-weight:bold; letter-spacing:1px;">
        <span style="color:#CCFF00;">WS_CONNECTED</span>
        <span style="color:#555;">LOAD: 14%</span>
        <span style="color:#555;">NODE_ID: 8829-X</span>
    </div>
</div>
""", unsafe_allow_html=True)
