import streamlit as st
from components.sidebar import render_sidebar

st.set_page_config(
    page_title="Sentinel Engine",
    page_icon="🛡️",
    layout="wide"
)

render_sidebar()

st.title("🛡️ Sentinel Real-Time Engine")
st.markdown("""
Welcome to the **Sentinel Real-Time Media Fingerprinting Engine**.

Select a page from the sidebar to view metrics or configure settings.
""")
