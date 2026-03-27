import streamlit as st

def render_metric_card(title, value, delta=None):
    st.metric(label=title, value=value, delta=delta)
