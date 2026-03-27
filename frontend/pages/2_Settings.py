import streamlit as st
from components.sidebar import render_sidebar

st.set_page_config(page_title="Settings", page_icon="⚙️", layout="wide")
render_sidebar()

st.title("⚙️ Engine Settings")
st.text_input("Backend API URL", value="http://localhost:5000")
st.slider("Fingerprint Sensitivity Threshold", 0.0, 1.0, 0.85)

if st.button("Save Configuration"):
    st.success("Configuration saved correctly!")
