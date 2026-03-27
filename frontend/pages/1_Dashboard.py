import streamlit as st
import time

st.set_page_config(page_title="Dashboard - SENTINEL", layout="wide", initial_sidebar_state="expanded")

with open("frontend/assets/style.css") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# Main splash screen content
st.markdown("""
<div style="height: 70vh; display: flex; flex-direction: column; justify-content: center; align-items: center; text-align: center;">
    <div style="font-size: 6em; color: #CCFF00; font-weight: 800; letter-spacing: 12px; line-height: 1; margin-bottom: 15px; text-shadow: 0 0 40px rgba(204, 255, 0, 0.4);">SENTINEL</div>
    <div style="font-size: 1.2em; color: #888; letter-spacing: 6px; font-weight: bold;">V 4.2.8 STABLE</div>
    <div style="font-size: 0.9em; color: #666; letter-spacing: 3px; margin-top: 10px;">INITIATING_REAL_TIME_PIRACY_SCAN...</div>
    
    <div style="margin-top: 60px; border: 1px solid #333; padding: 20px 40px; background-color: #1a1c1e; border-radius: 4px; box-shadow: inset 0 0 20px rgba(0,0,0,0.5);">
        <span class="status-indicator"></span> 
        <span style="color: #FFF; font-weight: bold; letter-spacing: 2px;">CONTENT FINGERPRINTING ENGINE ACTIVE</span>
    </div>
    
    <div style="margin-top: 30px; display: flex; gap: 40px; font-size: 0.8em;">
        <div style="display: flex; align-items: center;">
            <span style="display: inline-block; width: 8px; height: 8px; background-color: #FFA500; border-radius: 50%; margin-right: 8px;"></span>
            <span style="color: #888; letter-spacing: 1px;">ENCRYPTED</span>
        </div>
        <div style="display: flex; align-items: center;">
            <span style="display: inline-block; width: 8px; height: 8px; background-color: #8daeff; border-radius: 50%; margin-right: 8px;"></span>
            <span style="color: #888; letter-spacing: 1px;">DEEP SCAN</span>
        </div>
    </div>
</div>

<div style="position: fixed; top: 20px; left: 20px; font-size: 0.7em; color: #666; letter-spacing: 1px;">
    <div>SYSLOG: ETHERIUM.ONE</div>
    <div>SEC_LOG: [HIDDEN]</div>
</div>

<div style="position: fixed; bottom: 20px; right: 20px; font-size: 0.7em; color: #666; letter-spacing: 1px; text-align: right;">
    <div>LOGGING_ENABLED: TRUE</div>
    <div>BUFFERING_ASSETS...</div>
</div>
""", unsafe_allow_html=True)

# Auto-redirect simulation
if 'redirect_time' not in st.session_state:
    st.session_state.redirect_time = time.time()

time_elapsed = time.time() - st.session_state.redirect_time
if time_elapsed > 5:  # After 5 seconds, show navigation hint
    st.markdown("""
    <div style="text-align:center; color: #555; font-size: 0.8em; letter-spacing: 2px; margin-top: 40px;">
        Use the navigation sidebar to access modules.
    </div>
    """, unsafe_allow_html=True)