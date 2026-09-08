import streamlit as st

CSS = """
<style>
:root { --radius: 18px; }
.block-container { padding-top: 2rem; max-width: 1400px; }
.hero {
  padding: 2.2rem 2.4rem; border-radius: 26px;
  background: linear-gradient(135deg, rgba(99,102,241,.16), rgba(14,165,233,.10));
  border: 1px solid rgba(120,120,160,.20); margin-bottom: 1.5rem;
}
.hero h1 { font-size: 2.5rem; margin: 0; letter-spacing: -.04em; }
.hero p { color: #667085; font-size: 1.05rem; margin: .5rem 0 0; }
.feature-card {
  border: 1px solid rgba(120,120,160,.18); border-radius: 18px;
  padding: 1.25rem; min-height: 150px; background: rgba(255,255,255,.55);
}
.feature-card b, .feature-card span { display:block; }
.feature-card span { color:#667085; margin-top:.5rem; }
.feature-icon { font-size: 2rem; margin-bottom:.5rem; }
.landing-grid { display:grid; grid-template-columns:repeat(4,1fr); gap:1rem; margin-top:2rem; }
.metric-card {
  border:1px solid rgba(120,120,160,.18); border-radius:16px;
  padding:1rem; background:rgba(255,255,255,.45);
}
.small-label { color:#667085; font-size:.82rem; }
.big-number { font-size:1.45rem; font-weight:700; }
@media (max-width: 900px) {
  .landing-grid { grid-template-columns:repeat(2,1fr); }
}
</style>
"""

def inject_css():
    st.markdown(CSS, unsafe_allow_html=True)

def render_header():
    st.markdown("""
    <div class="hero">
      <h1>📊 Autonomous Data Analyst</h1>
      <p>Upload your data. Ask a question. Let an agent plan, analyze, visualize and verify the evidence.</p>
    </div>
    """, unsafe_allow_html=True)

def render_sidebar():
    with st.sidebar:
        st.markdown("## ⚙️ Workspace")
        st.caption("Groq powers planning and reporting. Pandas performs the actual data analysis.")
        if st.session_state.get("datasets"):
            st.success(f"{len(st.session_state['datasets'])} dataset(s) loaded")
        st.divider()
        st.markdown("### Workflow")
        for text in [
            "🔎 Dataset inspection",
            "🧠 Planning",
            "🛠️ Tool selection",
            "🐍 Python analysis",
            "📈 Visualization",
            "✅ Independent verification",
            "📝 Final report",
        ]:
            st.write(text)

def render_profile(profiles):
    st.subheader("🔎 Dataset Profile")
    for name, p in profiles.items():
        a, b, c, d = st.columns(4)
        a.markdown(f'<div class="metric-card"><div class="small-label">Dataset</div><div class="big-number">{name}</div></div>', unsafe_allow_html=True)
        b.markdown(f'<div class="metric-card"><div class="small-label">Rows</div><div class="big-number">{p["rows"]:,}</div></div>', unsafe_allow_html=True)
        c.markdown(f'<div class="metric-card"><div class="small-label">Columns</div><div class="big-number">{p["columns_count"]}</div></div>', unsafe_allow_html=True)
        d.markdown(f'<div class="metric-card"><div class="small-label">Duplicates</div><div class="big-number">{p["duplicates"]:,}</div></div>', unsafe_allow_html=True)
        with st.expander(f"View {name}"):
            st.write("**Columns:**", ", ".join(p["columns"]))
            st.dataframe(p["sample"], use_container_width=True)

def render_history():
    history = st.session_state.get("history", [])
    if history:
        with st.expander("🕘 Analysis History"):
            for i, item in enumerate(reversed(history), 1):
                st.markdown(f"**{i}. {item['question']}**")
                st.caption(item["summary"])
