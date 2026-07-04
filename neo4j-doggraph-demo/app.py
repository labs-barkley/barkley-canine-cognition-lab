"""
Barkley DogGraph — Streamlit app (v3 · v9 brand)
================================================
The behavioral memory layer, made legible in ten seconds.

Page architecture (deliberate — a VC must understand before scrolling):
  1. Header: halo · wordmark · CTA → getbarkley.com
  2. The claim: DogGraph stores, connects, explains — it does not detect
  3. The difference, in ten seconds (breed average vs own baseline)
  4. Ask: a dropdown of curated, audited questions (auto-runs — no empty box
     that pretends to answer anything you type)
  5. Result: grounded answer · Cypher in a jSite window · raw rows,
     with "what you're seeing" + glossary on the right
  6. Free-form GraphRAG for CTOs (expander, rate-limited)
  7. Under the hood: schema + pipeline + safety, at the end

Secrets: NEO4J_URI / NEO4J_USER / NEO4J_PASSWORD (+ ANTHROPIC_API_KEY) via
st.secrets or env. Synthetic data · not a diagnostic tool · patents filed.
"""
from __future__ import annotations

import html
import os
import re

import streamlit as st

HALO_URL = "https://getbarkley.com/images/Barkley_Halo_512x512.png"

st.set_page_config(
    page_title="Barkley DogGraph",
    page_icon=HALO_URL,
    layout="wide",
    initial_sidebar_state="collapsed",
)
if hasattr(st, "logo"):
    st.logo(HALO_URL, link="https://getbarkley.com")

# Free-form questions per session (public demo wired to a real API key).
MAX_FREEFORM_PER_SESSION = 15


# --------------------------------------------------------------------------- #
# Secrets / env
# --------------------------------------------------------------------------- #
def _get_secret(key: str, default=None):
    try:
        if key in st.secrets:
            return st.secrets[key]
    except Exception:
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
# Curated questions — audited Cypher, plain-language framing. The dropdown is
# the primary interface on purpose: every question always works.
# --------------------------------------------------------------------------- #
CURATED = [
    {
        "q": "Why does Kikoo look normal by breed average, but not by his own baseline?",
        "cypher": (
            "MATCH (d:Dog {name:'Kikoo'})-[:HAS_DRIFT]->(x:DriftEvent)-[:DRIFTED_FROM]->(b:Baseline)\n"
            "OPTIONAL MATCH (x)-[:MODULATED_BY]->(c:ContextEvent)\n"
            "RETURN d.name AS dog, d.breed AS breed, x.rate AS drift_rate,\n"
            "       x.severity AS severity, x.detected_on AS detected_on,\n"
            "       b.established_on AS baseline_established, c.type AS context"
        ),
        "note": ("A breed model has no memory of Kikoo — it can only compare him to "
                 "other dogs, and by that standard he is fine. This graph compares "
                 "him to himself: his own baseline, and a measured drift away from it."),
    },
    {
        "q": "Which dogs are drifting from their own baseline?",
        "cypher": (
            "MATCH (d:Dog)-[:HAS_DRIFT]->(x:DriftEvent)-[:DRIFTED_FROM]->(:Baseline)\n"
            "RETURN d.name AS dog, d.breed AS breed, x.rate AS drift_rate,\n"
            "       x.severity AS severity, x.detected_on AS detected_on\n"
            "ORDER BY x.rate DESC"
        ),
        "note": ("The core question a flat tracker cannot ask. Each drift is measured "
                 "against that dog's own history — no population average involved."),
    },
    {
        "q": "Which dog needs attention first, and why?",
        "cypher": (
            "MATCH (d:Dog)-[:HAS_DRIFT]->(x:DriftEvent)\n"
            "OPTIONAL MATCH (x)-[:MODULATED_BY]->(c:ContextEvent)\n"
            "RETURN d.name AS dog, x.rate AS drift_rate, x.severity AS severity,\n"
            "       CASE WHEN c IS NULL THEN 'UNEXPLAINED — review' ELSE 'explained by context' END AS status,\n"
            "       c.type AS context\n"
            "ORDER BY (c IS NULL) DESC, x.rate DESC"
        ),
        "note": ("Triage is not 'biggest drift first' — it is 'least explained first'. "
                 "A drift with a known cause is calm; a drift with no context attached "
                 "earns the first look."),
    },
    {
        "q": "Is Kikoo's drift explained by context, or unexplained?",
        "cypher": (
            "MATCH (d:Dog {name:'Kikoo'})-[:HAS_DRIFT]->(x:DriftEvent)\n"
            "OPTIONAL MATCH (x)-[:MODULATED_BY]->(c:ContextEvent)\n"
            "RETURN x.rate AS drift_rate, x.severity AS severity,\n"
            "       CASE WHEN c IS NULL THEN 'unexplained' ELSE 'context-explained' END AS status,\n"
            "       c.type AS context, c.description AS context_detail"
        ),
        "note": ("Context is the difference between an alarm and an explanation. "
                 "The edge MODULATED_BY is doing the interpretive work here."),
    },
    {
        "q": "What changed before the walk recommendation?",
        "cypher": (
            "MATCH (d:Dog {name:'Kikoo'})-[rr:RECOMMENDED_ROUTE]->(r:Route)-[:LOCATED_NEAR]->(l:Location)\n"
            "OPTIONAL MATCH (d)-[:HAS_DRIFT]->(x:DriftEvent)\n"
            "RETURN x.detected_on AS drift_detected_on, x.rate AS drift_rate,\n"
            "       x.severity AS severity, r.name AS recommended_route,\n"
            "       r.terrain AS terrain, r.intensity AS intensity,\n"
            "       l.name AS near, rr.reason AS reason"
        ),
        "note": ("The recommendation is a function of current state: elevated drift → "
                 "a calmer, flatter route. The reasoning is stored on the edge itself, "
                 "so the answer always ships with its why."),
    },
    {
        "q": "Which compatibility walk is safest, and why?",
        "cypher": (
            "MATCH (:Dog {name:'Kikoo'})-[c:COMPATIBLE_WITH]->(o:Dog)\n"
            "RETURN o.name AS candidate, o.breed AS breed,\n"
            "       c.score AS compatibility, c.reason AS why\n"
            "ORDER BY c.score DESC"
        ),
        "note": ("Compatibility is a scored, explained relationship — not a guess. "
                 "The safest walk is the highest score whose reason fits Kikoo's "
                 "current state."),
    },
    {
        "q": "Which dogs are stable — no drift at all?",
        "cypher": (
            "MATCH (d:Dog)\n"
            "WHERE NOT (d)-[:HAS_DRIFT]->(:DriftEvent)\n"
            "RETURN d.name AS dog, d.breed AS breed\n"
            "ORDER BY d.name"
        ),
        "note": ("Stability is a finding too. These dogs track their own baselines "
                 "closely — the absence of a drift edge is itself information."),
    },
    {
        "q": "Show Kikoo's baseline profile across all channels.",
        "cypher": (
            "MATCH (d:Dog {name:'Kikoo'})-[:HAS_BASELINE]->(b:Baseline)\n"
            "RETURN b.established_on AS established_on, b.window_days AS window_days,\n"
            "       b.activity_level_mean AS activity_mean, b.activity_level_scale AS activity_scale,\n"
            "       b.sleep_fragmentation_mean AS sleep_frag_mean, b.sleep_fragmentation_scale AS sleep_frag_scale,\n"
            "       b.restlessness_index_mean AS restlessness_mean, b.restlessness_index_scale AS restlessness_scale,\n"
            "       b.location_entropy_mean AS loc_entropy_mean, b.location_entropy_scale AS loc_entropy_scale,\n"
            "       b.social_response_latency_mean AS social_latency_mean, b.social_response_latency_scale AS social_latency_scale"
        ),
        "note": ("Five channels, each with a mean and a scale — the Individual "
                 "Cognitive Fingerprint every future reading is compared against."),
    },
]
CURATED_BY_Q = {c["q"]: c for c in CURATED}


# --------------------------------------------------------------------------- #
# Backends (lazy) + server-wide answer caches
# --------------------------------------------------------------------------- #
@st.cache_resource(show_spinner=False)
def _backend():
    import graph_query_llm
    return graph_query_llm


@st.cache_data(ttl=3600, show_spinner=False)
def _cached_curated(question: str) -> dict:
    c = CURATED_BY_Q[question]
    return _backend().answer_curated(question, c["cypher"], c["note"]).to_dict()


@st.cache_data(ttl=3600, show_spinner=False)
def _cached_freeform(question: str) -> dict:
    return _backend().answer_llm(question, prefer_llm=True).to_dict()


# --------------------------------------------------------------------------- #
# v9 CSS + HTML components
# --------------------------------------------------------------------------- #
V9_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter+Tight:wght@400;500;600;700&family=Inter:wght@400;500;600&family=Instrument+Serif:ital@0;1&family=JetBrains+Mono:wght@400;500;600&display=swap');

html, body, [class*="css"], .stMarkdown, p, li { font-family: 'Inter','Helvetica Neue',sans-serif; }
h1,h2,h3 { font-family:'Inter Tight','Helvetica Neue',sans-serif !important; letter-spacing:-.03em; }

.bk-head{display:flex;align-items:center;justify-content:space-between;gap:1rem;
  padding:.2rem 0 1.1rem;border-bottom:1px solid rgba(237,235,228,.08);margin-bottom:1.6rem}
.bk-brand{display:flex;align-items:center;gap:.6rem}
.bk-brand img{width:30px;height:30px}
.bk-word{font-family:'Inter Tight',sans-serif;font-weight:600;font-size:1.08rem;color:#edebe4;letter-spacing:-.02em}
.bk-dot{color:#c97bff}
.bk-chip{font-family:'JetBrains Mono',monospace;font-size:.62rem;letter-spacing:.12em;color:rgba(237,235,228,.42);
  border-left:1px solid rgba(237,235,228,.12);padding-left:.65rem;text-transform:uppercase}
.bk-cta{font-family:'Inter Tight',sans-serif;font-weight:600;font-size:.85rem;color:#fff !important;
  background:linear-gradient(120deg,#7b9fff,#c97bff);padding:.5rem 1.2rem;border-radius:999px;
  text-decoration:none !important;box-shadow:0 10px 26px -12px rgba(150,120,255,.85);white-space:nowrap}
.bk-cta:hover{filter:brightness(1.08)}

.bk-kicker{font-family:'JetBrains Mono',monospace;font-size:.64rem;letter-spacing:.22em;
  text-transform:uppercase;color:rgba(237,235,228,.42);margin:.2rem 0 1rem}
.bk-h1{font-family:'Inter Tight',sans-serif;font-weight:500;font-size:clamp(1.9rem,4.2vw,3rem);
  line-height:1.05;letter-spacing:-.045em;color:#edebe4;margin:0 0 1rem}
.bk-acc{font-family:'Instrument Serif',serif;font-style:italic;font-weight:400;font-size:1.05em;
  background:linear-gradient(115deg,#2ee0ff 0%,#7b9fff 45%,#c97bff 100%);
  -webkit-background-clip:text;background-clip:text;-webkit-text-fill-color:transparent}
.bk-lead{font-size:1.02rem;line-height:1.65;color:rgba(237,235,228,.64);max-width:56rem;margin:0 0 .6rem}
.bk-lead b{color:#edebe4;font-weight:600}

.bk-chain{display:flex;align-items:center;flex-wrap:wrap;gap:.4rem .3rem;margin:1rem 0 .4rem}
.bk-node{font-family:'JetBrains Mono',monospace;font-size:.7rem;color:rgba(237,235,228,.88);
  padding:.42rem .8rem;border-radius:999px;background:rgba(255,255,255,.04);
  border:1px solid rgba(237,235,228,.1);white-space:nowrap}
.bk-edge{width:22px;height:1px;background:linear-gradient(90deg,rgba(123,159,255,.5),rgba(201,123,255,.5))}

.bk-diff{display:grid;grid-template-columns:1fr 1fr;gap:1rem;margin:1.4rem 0 .9rem}
@media(max-width:800px){.bk-diff{grid-template-columns:1fr}}
.bk-card{border:1px solid rgba(237,235,228,.09);border-radius:16px;padding:1.3rem 1.4rem;
  background:rgba(255,255,255,.014)}
.bk-card .tag{font-family:'JetBrains Mono',monospace;font-size:.62rem;letter-spacing:.1em;
  text-transform:uppercase;margin-bottom:.6rem}
.bk-card h4{font-family:'Inter Tight',sans-serif;font-weight:600;font-size:1.12rem;
  letter-spacing:-.02em;color:#edebe4;margin:0 0 .45rem}
.bk-card p{font-size:.93rem;line-height:1.6;color:rgba(237,235,228,.64);margin:0}
.bk-verdict{font-family:'Instrument Serif',serif;font-style:italic;font-size:1.05rem}
.bk-same{font-size:1.02rem;color:rgba(237,235,228,.64);line-height:1.65;max-width:56rem}
.bk-same b{color:#edebe4}

.bk-sec{font-family:'JetBrains Mono',monospace;font-size:.64rem;letter-spacing:.2em;
  text-transform:uppercase;color:rgba(237,235,228,.42);border-top:1px solid rgba(237,235,228,.07);
  padding-top:1.3rem;margin:2rem 0 .8rem}

.win{border:1px solid rgba(237,235,228,.1);border-radius:14px;overflow:hidden;
  background:#0b0d12;margin:.4rem 0 .8rem;box-shadow:0 30px 70px -40px rgba(0,0,0,.9)}
.win-bar{display:flex;align-items:center;gap:.7rem;padding:.5rem .9rem;background:#090b0f;
  border-bottom:1px solid rgba(237,235,228,.05)}
.win-dots{display:flex;gap:5px}
.win-dots i{width:10px;height:10px;border-radius:50%;display:block}
.win-title{font-family:'JetBrains Mono',monospace;font-size:.66rem;color:rgba(237,235,228,.42);margin:0 auto;transform:translateX(-20px)}
.win-code{font-family:'JetBrains Mono',monospace;font-size:.78rem;line-height:1.75;color:#c6ccd6;
  padding:.9rem 1.1rem;margin:0;white-space:pre-wrap;word-break:break-word}
.win-code .k{color:#7b9fff}.win-code .s{color:#3fd6bc}.win-code .t{color:#c97bff}.win-code .p{color:#2ee0ff}
.win-status{display:flex;gap:1rem;padding:.4rem .9rem;background:#090b0f;border-top:1px solid rgba(237,235,228,.05)}
.win-status span{font-family:'JetBrains Mono',monospace;font-size:.62rem;color:rgba(237,235,228,.42)}
.win-status .ok{color:#3fd6bc}.win-status .br{color:#7b9fff}

.bk-note{border-left:2px solid rgba(201,123,255,.5);padding:.15rem 0 .15rem .9rem;margin:.2rem 0 1rem}
.bk-note p{font-family:'Instrument Serif',serif;font-style:italic;font-size:1.02rem;
  line-height:1.55;color:rgba(237,235,228,.78);margin:0}
.bk-gloss{font-size:.86rem;line-height:1.6;color:rgba(237,235,228,.56)}
.bk-gloss b{color:#edebe4;font-weight:600}

div.stButton>button[kind="primary"]{background:linear-gradient(120deg,#7b9fff,#c97bff);
  border:none;border-radius:999px;font-family:'Inter Tight',sans-serif;font-weight:600}
div.stButton>button{border-radius:999px;font-family:'Inter Tight',sans-serif}
.bk-foot{text-align:center;font-family:'JetBrains Mono',monospace;font-size:.66rem;
  letter-spacing:.06em;color:rgba(237,235,228,.3);margin-top:2.4rem}
.bk-foot a{color:rgba(123,159,255,.7);text-decoration:none}
</style>
"""
st.markdown(V9_CSS, unsafe_allow_html=True)


def cypher_html(code: str) -> str:
    """Escape + minimally highlight Cypher for the jSite window."""
    c = html.escape(code, quote=False)
    c = re.sub(r"('[^']*')", r'<span class="s">\1</span>', c)
    c = re.sub(r"(:`?[A-Za-z_]+`?)(?=[\s){\]])", r'<span class="t">\1</span>', c)
    c = re.sub(
        r"\b(MATCH|OPTIONAL|WHERE|WITH|RETURN|ORDER|BY|LIMIT|DISTINCT|AS|CASE|WHEN|THEN|ELSE|END|NOT|AND|OR|IS|NULL|DESC|ASC)\b",
        r'<span class="k">\1</span>', c)
    return c


def jsite_cypher(code: str, mode: str) -> str:
    return (
        '<div class="win">'
        '<div class="win-bar"><span class="win-dots">'
        '<i style="background:#ff5f57"></i><i style="background:#febc2e"></i><i style="background:#28c840"></i>'
        '</span><span class="win-title">query.cypher — generated & validated</span></div>'
        f'<pre class="win-code">{cypher_html(code)}</pre>'
        '<div class="win-status"><span class="br">⎇ read-only</span>'
        '<span class="ok">✓ validator passed</span>'
        '<span class="ok">✓ read transaction</span>'
        f'<span>mode: {html.escape(mode)}</span></div>'
        '</div>'
    )


# --------------------------------------------------------------------------- #
# 1 · Header
# --------------------------------------------------------------------------- #
st.markdown(
    f'''
    <div class="bk-head">
      <div class="bk-brand">
        <img src="{HALO_URL}" alt="Barkley halo"/>
        <span class="bk-word">Barkley<span class="bk-dot">.</span></span>
        <span class="bk-chip">DogGraph</span>
      </div>
      <a class="bk-cta" href="https://getbarkley.com" target="_blank" rel="noopener">getbarkley.com →</a>
    </div>
    <div class="bk-kicker">Behavioral memory layer · Live GraphRAG demo · Synthetic data</div>
    <h1 class="bk-h1">The memory that makes a dog <span class="bk-acc">more than an average.</span></h1>
    <p class="bk-lead"><b>DogGraph is Barkley's behavioral memory layer.</b> It does not detect drift;
    it stores, connects, and explains validated behavioral conclusions. Most pet AI counts events —
    Barkley connects change over time:</p>
    <div class="bk-chain">
      <span class="bk-node">dog</span><span class="bk-edge"></span>
      <span class="bk-node">baseline</span><span class="bk-edge"></span>
      <span class="bk-node">context</span><span class="bk-edge"></span>
      <span class="bk-node">drift</span><span class="bk-edge"></span>
      <span class="bk-node">route</span><span class="bk-edge"></span>
      <span class="bk-node">compatibility</span>
    </div>
    ''',
    unsafe_allow_html=True,
)

# --------------------------------------------------------------------------- #
# 2 · The difference, in ten seconds — FIRST, or nothing else makes sense
# --------------------------------------------------------------------------- #
st.markdown(
    '''
    <div class="bk-sec">01 · The difference, in ten seconds</div>
    <div class="bk-diff">
      <div class="bk-card">
        <div class="tag" style="color:rgba(237,235,228,.42)">// breed average</div>
        <h4>The breed average says: fine.</h4>
        <p>Kikoo's activity sits inside the normal range for a Jack Russell Terrier.
        A population model sees nothing. <span class="bk-verdict">No alert.</span></p>
      </div>
      <div class="bk-card" style="border-color:rgba(201,123,255,.35)">
        <div class="tag" style="color:#c97bff">// his own baseline</div>
        <h4>Kikoo's own baseline says: look.</h4>
        <p>Compared to <i>his own</i> history, Kikoo moves less, recovers slower, and
        goes quiet more often. <span class="bk-verdict" style="color:#c97bff">Drift detected — weeks earlier.</span></p>
      </div>
    </div>
    <p class="bk-same">Same dog. Same data. <b>Different reference — different conclusion.</b>
    This graph is the memory that makes the second answer possible: each dog's baseline,
    its drift, and the context that explains it, stored as relationships you can question.</p>
    ''',
    unsafe_allow_html=True,
)

# --------------------------------------------------------------------------- #
# 3 · Ask — dropdown of curated questions, auto-runs
# --------------------------------------------------------------------------- #
st.markdown('<div class="bk-sec">02 · Ask the graph</div>', unsafe_allow_html=True)

db_ok, llm_ok = _have_db(), _have_llm()

question = st.selectbox(
    "Pick a question — it runs instantly:",
    options=[c["q"] for c in CURATED],
    index=0,
    help="Every question here is a curated, audited graph query — it always works. "
         "CTO mode: ask your own free-form question further down.",
)

if not db_ok:
    st.error("Neo4j credentials missing — see README / deploy/DEPLOY.md.")
else:
    with st.spinner("Querying the graph…"):
        try:
            result = _cached_curated(question)
        except Exception as exc:
            st.error(f"Error: {exc}")
            st.stop()

    col_main, col_side = st.columns([1.9, 1], gap="large")

    with col_main:
        st.markdown("#### Answer")
        st.markdown(result["answer"] or "_(no answer synthesized)_")
        st.markdown(jsite_cypher(result["cypher"], result["mode"]), unsafe_allow_html=True)
        if result["rows"]:
            with st.expander(f"Raw results · {len(result['rows'])} row(s)"):
                st.dataframe(result["rows"], use_container_width=True, hide_index=True)
        st.caption(
            "Every number above came out of the graph — the model is only allowed to "
            "phrase what was retrieved."
        )

    with col_side:
        st.markdown(
            f'<div class="bk-note"><p>{html.escape(CURATED_BY_Q[question]["note"])}</p></div>',
            unsafe_allow_html=True,
        )
        here = os.path.dirname(os.path.abspath(__file__))
        render = os.path.join(here, "screenshots", "graph_render.png")
        if os.path.exists(render):
            st.image(render, caption="Kikoo's neighborhood — the memory being queried",
                     use_container_width=True)
        st.markdown(
            '''
            <div class="bk-gloss">
            <b>Individual Baseline</b> — a per-individual longitudinal norm learned from
            that individual's own history, used as the reference frame for detecting
            change instead of a population average.<br/><br/>
            <b>Behavioral Drift</b> — a slow, cumulative divergence of an individual's
            behavior away from its own baseline — typically invisible to population
            statistics.<br/><br/>
            <b>Reference Frame</b> — the comparison standard a model uses to decide
            whether a behavior is normal; the same data can yield opposite conclusions
            under different reference frames.<br/><br/>
            Full canonical glossary → <a href="https://getbarkley.com/llms.txt"
            style="color:rgba(123,159,255,.8)">getbarkley.com/llms.txt</a>
            </div>
            ''',
            unsafe_allow_html=True,
        )

# --------------------------------------------------------------------------- #
# 4 · Free-form GraphRAG — the CTO path (rate-limited)
# --------------------------------------------------------------------------- #
st.markdown('<div class="bk-sec">03 · CTO mode — free-form GraphRAG</div>', unsafe_allow_html=True)
with st.expander("Ask your own question (LLM → schema-constrained, read-only Cypher)"):
    st.caption(
        "Your question is translated by an LLM constrained to the DogGraph schema. "
        "The emitted Cypher is validated (writes and CALL refused), capped with a "
        "LIMIT, and executed in a server-enforced read transaction. Out-of-schema "
        "questions get a graceful refusal — by design, this box does not pretend "
        "to know things the graph doesn't."
    )
    ff_q = st.text_input("Free-form question:", placeholder="e.g. Which dog has the highest unexplained drift?")
    ff_go = st.button("Ask the graph", type="primary")
    if ff_go and ff_q.strip():
        if not db_ok:
            st.error("Neo4j credentials missing.")
        elif not llm_ok:
            st.info("ANTHROPIC_API_KEY missing — free-form mode needs the LLM translator.")
        elif st.session_state.get("ff_count", 0) >= MAX_FREEFORM_PER_SESSION:
            st.warning(
                f"You've reached {MAX_FREEFORM_PER_SESSION} free-form questions this "
                "session — thanks for stress-testing the GraphRAG layer! Refresh for a "
                "new session, or reach out at labs@getbarkley.com."
            )
        else:
            st.session_state["ff_count"] = st.session_state.get("ff_count", 0) + 1
            with st.spinner("Translating → validating → querying → grounding…"):
                try:
                    ff = _cached_freeform(ff_q.strip())
                except Exception as exc:
                    st.error(f"Error: {exc}")
                    st.stop()
            st.markdown("#### Answer")
            st.markdown(ff["answer"] or f"_{ff['note'] or 'No answer.'}_")
            if ff["cypher"]:
                st.markdown(jsite_cypher(ff["cypher"], ff["mode"]), unsafe_allow_html=True)
            if ff["rows"]:
                with st.expander(f"Raw results · {len(ff['rows'])} row(s)"):
                    st.dataframe(ff["rows"], use_container_width=True, hide_index=True)

# --------------------------------------------------------------------------- #
# 5 · Under the hood — schema, pipeline, safety (at the end, as it should be)
# --------------------------------------------------------------------------- #
st.markdown('<div class="bk-sec">04 · Under the hood</div>', unsafe_allow_html=True)
c1, c2 = st.columns([1.15, 1], gap="large")
with c1:
    here = os.path.dirname(os.path.abspath(__file__))
    schema_img = os.path.join(here, "screenshots", "doggraph_schema.png")
    if os.path.exists(schema_img):
        st.image(schema_img, caption="The DogGraph schema — the relationships are the product",
                 use_container_width=True)
with c2:
    st.markdown(
        jsite_cypher(
            "question\n"
            "  → LLM (schema-constrained, read-only rule, OUT_OF_SCOPE escape)\n"
            "  → Cypher\n"
            "  → validator (writes + CALL refused) · LIMIT enforced\n"
            "  → Neo4j, read transaction   ← retrieval = graph traversal\n"
            "  → rows\n"
            "  → LLM ('ground the answer strictly in these rows')\n"
            "  → answer",
            "graphrag · strict sense",
        ),
        unsafe_allow_html=True,
    )
    st.markdown(
        "**Honest by construction.** The LLM is an interface, not a reasoning engine: "
        "retrieval is the graph traversal, generation is grounded in the retrieved rows, "
        "and no write can ever reach the database — prompt rule, keyword validator, and "
        "a server-enforced read transaction, in depth. Drift **detection** happens in the "
        "[Barkley Reference Architecture](https://github.com/labs-barkley/barkley-reference-architecture); "
        "DogGraph is the behavioral memory it writes to."
    )
    st.markdown(
        "- Repo: [`neo4j-doggraph-demo`](https://github.com/labs-barkley/barkley-canine-cognition-lab/tree/main/neo4j-doggraph-demo)\n"
        "- Drift demo: [drift-explorer.getbarkley.com](https://drift-explorer.getbarkley.com)\n"
        "- Dataset: [synthetic-doggraph-sample](https://huggingface.co/datasets/labs-barkley/synthetic-doggraph-sample)\n"
        "- ORCID: [0009-0004-6031-659X](https://orcid.org/0009-0004-6031-659X)"
    )

# --------------------------------------------------------------------------- #
# Footer
# --------------------------------------------------------------------------- #
st.markdown(
    '<div class="bk-foot">© 2026 Barkley AI · synthetic data · patent applications filed · '
    'not a diagnostic tool · <a href="https://getbarkley.com" target="_blank">getbarkley.com</a></div>',
    unsafe_allow_html=True,
)
