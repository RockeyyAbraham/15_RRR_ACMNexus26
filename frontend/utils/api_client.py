import requests
import streamlit as st

BASE_URL = "http://localhost:5000/api"

def get_system_status():
    try:
        response = requests.get(f"{BASE_URL}/status", timeout=2)
        return response.json()
    except requests.exceptions.RequestException:
        return {"status": "error", "message": "Backend unreachable"}
