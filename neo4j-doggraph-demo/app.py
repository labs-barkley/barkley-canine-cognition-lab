"""
Barkley DogGraph — Streamlit app
================================
A self-contained Streamlit UI for the DogGraph. Connects to a Neo4j AuraDB
instance the operator owns, and uses the LLM/GraphRAG layer in
`graph_query_llm.py` to translate natural-language questions to validated,
read-only Cypher, execute them on the graph, and synthesize grounded answers.

Run locally
-----------
    pip install -r requirements.txt
    export NEO4J_URI="neo4j+s://<id>.databases.neo4j.io"
    export NEO4J_USER="neo4j"
    export NEO4J_PASSWORD="<your-aura-password>"
    export ANTHROPIC_API_KEY="<your-anthropic-key>"        # optional but recommended
    streamlit run app.py

Deploy to Streamlit Community Cloud
-----------------------------------
1. Push this folder to a GitHub repo (or use the existing
   `labs-barkley/barkley-canine-cognition-lab`, file path
   `neo4j-doggraph-demo/app.py`).
2. In https://share.streamlit.io, "Create app", select the repo, set the
   main file path to `neo4j-doggraph-demo/app.py`.
3. In "Advanced settings → Secrets", paste:

       NEO4J_URI = "neo4j+s://<id>.databases.neo4j.io"
       NEO4J_USER = "neo4j"
       NEO4J_PASSWORD = "<your-aura-password>"
       ANTHROPIC_API_KEY = "<your-anthropic-key>"
       ANTHROPIC_MODEL = "claude-haiku-4-5-20251001"

4. Deploy. The free Community tier has 2.7 GB per app — plenty for this demo.

This is a research demonstrator on fully synthetic data, not a diagnostic tool.
Certain Barkley methods are the subject of filed patent applications.
"""
from __future__ import annotations

import os
from pathlib import Path

import streamlit as st


# --------------------------------------------------------------------------- #
# Page config — must be the very first Streamlit call
# --------------------------------------------------------------------------- #
st.set_page_config(
    page_title="Barkley DogGraph",
    page_icon="🐕",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Soft per-session cap on questions (public demo wired to a real API key).
MAX_QUESTIONS_PER_SESSION = 25


# --------------------------------------------------------------------------- #
# Secrets / env: read from Streamlit Cloud secrets first, fall back to env vars
# Then push into os.environ so the existing modules pick them up unchanged.
# --------------------------------------------------------------------------- #
def _get_secret(key: str, default=None):
    """Streamlit secrets (cloud) → environment variable (local) → default."""
    try:
        if key in st.secrets:
            return st.secrets[key]
    except Exception:
        # st.secrets may raise if no secrets.toml is present locally; that's fine.
        pass
    return os.environ.get(key, default)


for _k in ("NEO4J_URI", "NEO4J_USER", "NEO4J_PASSWORD",
           "ANTHROPIC_API_KEY", "ANTHROPIC_MODEL"):
    _v = _get_secret(_k)
    if _v:
        os.environ[_k] = str(_v)


def _have_db() -> bool:
    return bool(_get_secret("NEO4J_URI") and _get_secret("NEO4J_PASSWORD"))


def _have_llm() -> bool:
    return bool(_get_secret("ANTHROPIC_API_KEY"))


# --------------------------------------------------------------------------- #
# Lazy backend import — so the app can render even if creds are missing.
# --------------------------------------------------------------------------- #
@st.cache_resource(show_spinner=False)
def _backend():
    from graph_query_llm import answer_llm  # imports anthropic + neo4j lazily
    return answer_llm


# --------------------------------------------------------------------------- #
# Header
# --------------------------------------------------------------------------- #
st.title("🐕 Barkley DogGraph")
st.caption(
    "Behavioral intelligence as a Neo4j property graph. Ask in natural language — "
    "an LLM emits schema-constrained, read-only Cypher; the graph answers; the LLM "
    "synthesizes a grounded reply. Synthetic data · research demonstrator · "
    "not a diagnostic tool."
)


# --------------------------------------------------------------------------- #
# Sidebar: schema diagram, presets, links
# --------------------------------------------------------------------------- #
with st.sidebar:
    st.subheader("DogGraph schema")
    here = Path(__file__).parent
    schema_img = here / "screenshots" / "doggraph_schema.png"
    graph_img  = here / "screenshots" / "graph_render.png"
    if schema_img.exists():
        st.image(str(schema_img), use_container_width=True,
                 caption="Schema (node labels and relationships)")
    if graph_img.exists():
        st.image(str(graph_img), use_container_width=True,
                 caption="Seeded graph (six synthetic dogs · Kikoo highlighted)")

    st.divider()
    st.subheader("Try a preset")
    presets = [
        "Which dogs are drifting from their baseline?",
        "Is Kikoo's drift explained by context, or unexplained?",
        "Which route is recommended for Kikoo and why?",
        "Who is the most socially compatible dog with Kikoo?",
    ]
    for p in presets:
        if st.button(p, use_container_width=True, key=f"preset_{abs(hash(p))}"):
            st.session_state["question"] = p

    st.divider()
    st.subheader("About")
    st.markdown(
        "- Repo: [`labs-barkley/barkley-canine-cognition-lab`](https://github.com/labs-barkley/barkley-canine-cognition-lab/tree/main/neo4j-doggraph-demo)  \n"
        "- Drift demo: [drift-explorer.getbarkley.com](https://drift-explorer.getbarkley.com)  \n"
        "- Dataset: [🤗 synthetic-doggraph-sample](https://huggingface.co/datasets/labs-barkley/synthetic-doggraph-sample)  \n"
        "- ORCID: [0009-0004-6031-659X](https://orcid.org/0009-0004-6031-659X)  \n"
        "- Synthetic data · patent applications filed"
    )


# --------------------------------------------------------------------------- #
# Input area + mode toggle + status
# --------------------------------------------------------------------------- #
question = st.text_input(
    "Ask the DogGraph in natural language:",
    value=st.session_state.get("question", ""),
    placeholder="e.g. Which dog has the highest unexplained drift?",
)

col_a, col_b = st.columns([3, 1])
with col_a:
    mode = st.radio(
        "Translator",
        options=["LLM (schema-constrained)", "Deterministic router"],
        horizontal=True,
        help=(
            "LLM mode uses the Anthropic API to translate natural language to Cypher, "
            "constrained by the DogGraph schema and validated as read-only before "
            "execution. Deterministic mode uses the four pattern-matching intents from "
            "the v1 demo."
        ),
    )
with col_b:
    submit = st.button("Ask the graph", type="primary", use_container_width=True)

# Status bar
db_ok  = _have_db()
llm_ok = _have_llm()
status_bits = [
    f"DB {'🟢' if db_ok else '🔴 missing'}",
    f"LLM {'🟢' if llm_ok else '🟡 deterministic only'}",
]
st.caption(" · ".join(status_bits))


# --------------------------------------------------------------------------- #
# Run the question
# --------------------------------------------------------------------------- #
if submit and question.strip():
    if not db_ok:
        st.error(
            "Neo4j credentials missing. Set `NEO4J_URI`, `NEO4J_USER`, "
            "`NEO4J_PASSWORD` in Streamlit secrets (cloud) or env vars (local). "
            "See README for the AuraDB setup steps."
        )
    elif st.session_state.get("q_count", 0) >= MAX_QUESTIONS_PER_SESSION:
        # Soft, per-session rate limit — mitigates casual abuse of a public
        # demo wired to a real API key. A determined user can refresh; pair
        # this with a spend alert on the Anthropic console.
        st.warning(
            f"You've reached {MAX_QUESTIONS_PER_SESSION} questions for this session — "
            "thanks for exploring the DogGraph! Refresh the page to start a new "
            "session, or reach out at labs@getbarkley.com to go deeper."
        )
    else:
        st.session_state["q_count"] = st.session_state.get("q_count", 0) + 1
        prefer_llm = (mode == "LLM (schema-constrained)")
        if prefer_llm and not llm_ok:
            st.info("ANTHROPIC_API_KEY missing — falling back to the deterministic router.")
            prefer_llm = False

        with st.spinner("Querying the graph…"):
            try:
                answer_llm = _backend()
                result = answer_llm(question, prefer_llm=prefer_llm)
            except Exception as exc:
                st.error(f"Error: {exc}")
                st.stop()

        st.markdown("---")

        # GraphRAG synthesized answer — surfaced first
        st.subheader("🐕 Answer")
        if result.answer:
            st.markdown(result.answer)
        else:
            st.info(result.note or "(No answer synthesized.)")

        # Generated Cypher + raw rows side-by-side
        c1, c2 = st.columns([1, 1])
        with c1:
            st.subheader("Generated Cypher")
            if result.cypher:
                st.code(result.cypher, language="cypher")
            else:
                st.caption("_No Cypher was emitted (out of scope or refused)._")
            st.caption(f"Mode: `{result.mode}`")
            if result.note and result.answer:
                # Already showed the note above when no answer; show alongside otherwise
                st.caption(result.note)
        with c2:
            st.subheader("Raw results")
            if result.rows:
                st.dataframe(result.rows, use_container_width=True, hide_index=True)
                st.caption(f"{len(result.rows)} row(s)")
            else:
                st.caption("_No rows returned._")

elif submit and not question.strip():
    st.warning("Please enter a question.")

else:
    # Idle / first-load explainer
    st.markdown("---")
    st.subheader("What you can ask")
    st.markdown(
        "- Which dogs are drifting, and from which baselines?\n"
        "- For a given dog, is the drift **explained by context** (vet visit, "
        "  schedule change) or unexplained?\n"
        "- Which route is recommended for a dog, and why?\n"
        "- Compatibility scores between dogs.\n"
        "- Cross-resolution counts (events per temporal bin or channel)."
    )
    st.caption(
        "The LLM is constrained to the DogGraph schema and emits **only read-only "
        "Cypher**, validated by a forbidden-keyword scanner before execution. "
        "Questions outside the schema return a graceful refusal."
    )


# --------------------------------------------------------------------------- #
# Footer
# --------------------------------------------------------------------------- #
st.markdown(
    """
    <div style="text-align:center; opacity:0.55; font-size:0.85em; margin-top:2em;">
    © 2026 Barkley AI · Synthetic data · Patent applications filed · Not a diagnostic tool
    </div>
    """,
    unsafe_allow_html=True,
)
