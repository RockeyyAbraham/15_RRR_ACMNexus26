import streamlit as st

def render_sidebar():
    with st.sidebar:
        st.header("Sentinel Controls")
        st.markdown("---")
        st.info("System Status: **ONLINE**")
        st.markdown("---")
        st.caption("v1.0.0 - Hackathon Build")
