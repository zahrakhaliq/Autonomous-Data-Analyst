import os
from pathlib import Path
import streamlit as st

APP_TITLE = "Autonomous Data Analyst"
APP_VERSION = "1.0.0"
MAX_FILE_MB = 100
MAX_ROWS = 1_000_000

def get_groq_api_key():
    try:
        key = st.secrets.get("GROQ_API_KEY")
        if key:
            return key
    except Exception:
        pass
    return os.getenv("GROQ_API_KEY")

def get_model():
    try:
        model = st.secrets.get("GROQ_MODEL")
        if model:
            return model
    except Exception:
        pass
    return os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")

BASE_DIR = Path(__file__).resolve().parent
