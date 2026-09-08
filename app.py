import streamlit as st
import pandas as pd
from pathlib import Path

from config import APP_TITLE
from data_profiler import load_datasets, build_profiles
from agent import AnalystAgent
from session_store import init_state, add_history
from ui import inject_css, render_sidebar, render_header, render_profile, render_history

st.set_page_config(
    page_title=APP_TITLE,
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

inject_css()
init_state()

render_header()

uploaded = st.file_uploader(
    "Upload one or more datasets",
    type=["csv", "xlsx"],
    accept_multiple_files=True,
    help="CSV and Excel files are supported. Your original files are never modified.",
)

if uploaded:
    try:
        datasets = load_datasets(uploaded)
        st.session_state["datasets"] = datasets
        st.session_state["profiles"] = build_profiles(datasets)
    except Exception as e:
        st.error(f"Could not read the uploaded file(s): {e}")
        st.stop()

render_sidebar()

if not st.session_state.get("datasets"):
    st.info("👆 Upload a CSV or Excel file to begin.")
    st.markdown("""
    <div class="landing-grid">
      <div class="feature-card"><div class="feature-icon">🔎</div><b>Understand</b><span>Automatically profile your data.</span></div>
      <div class="feature-card"><div class="feature-icon">🧠</div><b>Plan</b><span>Groq creates an analytical plan.</span></div>
      <div class="feature-card"><div class="feature-icon">🐍</div><b>Analyze</b><span>Python performs the calculations.</span></div>
      <div class="feature-card"><div class="feature-icon">✅</div><b>Verify</b><span>A separate verification layer checks results.</span></div>
    </div>
    """, unsafe_allow_html=True)
    st.stop()

profiles = st.session_state["profiles"]
render_profile(profiles)

st.divider()
st.subheader("Ask your data")

question = st.text_area(
    "Natural-language question",
    placeholder="Example: Why did revenue decrease in Q3?",
    height=110,
    label_visibility="collapsed",
)

col1, col2 = st.columns([1, 5])
with col1:
    analyze = st.button("🚀 Analyze", type="primary", use_container_width=True)
with col2:
    st.caption("The agent will inspect → plan → analyze → verify → report.")

if analyze:
    if not question.strip():
        st.warning("Please enter a question.")
        st.stop()

    agent = AnalystAgent(
        datasets=st.session_state["datasets"],
        profiles=profiles,
        history=st.session_state["history"],
    )

    progress = st.status("Running the autonomous analysis...", expanded=True)
    try:
        progress.write("🔎 Inspecting dataset structure...")
        progress.write("🧠 Building an analytical plan with Groq...")
        progress.write("🐍 Running deterministic Python/Pandas analysis...")
        result = agent.run(question, progress)
        progress.write("✅ Independently verifying calculations...")
        progress.update(label="Analysis complete", state="complete", expanded=False)

        st.session_state["last_result"] = result
        add_history(question, result)

    except Exception as e:
        progress.update(label="Analysis failed", state="error", expanded=True)
        st.exception(e)
        st.stop()

result = st.session_state.get("last_result")
if result:
    st.divider()
    st.subheader("📋 Executive Summary")
    st.markdown(result["report"]["executive_summary"])

    if result["report"]["key_findings"]:
        st.subheader("Key Findings")
        for finding in result["report"]["key_findings"]:
            st.markdown(f"- {finding}")

    if result.get("figures"):
        st.subheader("Visual Analysis")
        for fig in result["figures"]:
            st.plotly_chart(fig, use_container_width=True)

    with st.expander("🔬 Evidence & Methodology"):
        st.markdown(result["report"]["evidence"])
        st.markdown("**Methodology**")
        st.markdown(result["report"]["methodology"])

    with st.expander("🛡️ Verification & Limitations"):
        st.markdown(result["report"]["verification"])
        st.markdown(result["report"]["limitations"])

    with st.expander("🧭 Agent Plan"):
        st.json(result["plan"])

render_history()
