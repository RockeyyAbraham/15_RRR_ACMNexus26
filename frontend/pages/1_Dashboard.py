import streamlit as st
from components.metric_cards import render_metric_card
from components.sidebar import render_sidebar

st.set_page_config(page_title="Dashboard", page_icon="📊", layout="wide")
render_sidebar()

st.title("📊 Real-Time Dashboard")

col1, col2, col3 = st.columns(3)
with col1:
    render_metric_card("Active Streams", 12, 2)
with col2:
    render_metric_card("Fingeprints Processed", "45.2K", "1.2K")
with col3:
    render_metric_card("Matches Found", 8, -1)

st.divider()
st.subheader("Live Feed")
st.info("Waiting for data from backend...")
