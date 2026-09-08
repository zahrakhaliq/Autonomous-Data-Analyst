import streamlit as st

def init_state():
    st.session_state.setdefault("datasets", {})
    st.session_state.setdefault("profiles", {})
    st.session_state.setdefault("history", [])
    st.session_state.setdefault("last_result", None)

def add_history(question, result):
    st.session_state["history"].append({
        "question": question,
        "summary": result["report"].get("executive_summary", ""),
    })
    st.session_state["history"] = st.session_state["history"][-10:]
