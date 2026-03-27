import streamlit as st

st.set_page_config(page_title="SENTINEL - Global Intelligence Framework", layout="wide", initial_sidebar_state="expanded")

with open("frontend/assets/style.css") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# Main landing page content
st.markdown("""
<div style="height: 70vh; display: flex; flex-direction: column; justify-content: center; align-items: center; text-align: center;">
    <div style="font-size: 6em; color: #CCFF00; font-weight: 800; letter-spacing: 12px; line-height: 1; margin-bottom: 15px; text-shadow: 0 0 40px rgba(204, 255, 0, 0.4);">SENTINEL</div>
    <div style="font-size: 1.2em; color: #888; letter-spacing: 6px; font-weight: bold;">GLOBAL INTELLIGENCE FRAMEWORK</div>
    
    <div style="margin-top: 60px; border: 1px solid #333; padding: 20px 40px; background-color: #1a1c1e; border-radius: 4px; box-shadow: inset 0 0 20px rgba(0,0,0,0.5);">
        <span class="status-indicator"></span> 
        <span style="color: #FFF; font-weight: bold; letter-spacing: 2px;">SYSTEM ONLINE.</span> AWAITING IDENTIFICATION.
    </div>
</div>

<div style="text-align:center; color: #555; font-size: 0.8em; letter-spacing: 2px;">
    Use the navigation sidebar to access modules.
</div>
""", unsafe_allow_html=True)
