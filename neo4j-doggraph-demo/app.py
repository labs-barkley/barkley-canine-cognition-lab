"""
Barkley DogGraph — Streamlit app (v4 · chat + artifact pane)
============================================================
The behavioral memory layer, presented the way a VC already knows:
a chat-style exchange (question with a user icon, answer typing itself out
under the Barkley halo) and an artifact pane on the right (the generated
Cypher in a jSite window, raw results beneath). One exchange at a time —
a new question replaces the previous one. No free-text field: the questions
are curated, audited, and always work.

Page architecture:
  1. Header: halo · wordmark · CTA → getbarkley.com · the claim + chain
  2. H2 The difference, in ten seconds — card | card | paragraph (thirds)
  3. H2 Pick a question to run the graph — the signature question + three
     pillars of chips, grouped the way Barkley reasons (Individual /
     Relationships / Context), + single chat exchange + artifact pane
     (Cypher jSite window, raw results)
  4. Glossary — three canonical definitions, one per column
  5. H2 Under the hood — v9 figures + pipeline + safety

Secrets via st.secrets or env. Synthetic data · not a diagnostic tool ·
patent applications filed.
"""
from __future__ import annotations

import html
import os
import re
import time

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
    # Kept for the synthesis layer (grounded answers); no free-form input is
    # exposed in the UI — curated, audited questions only.
    return bool(_get_secret("ANTHROPIC_API_KEY"))


# --------------------------------------------------------------------------- #
# Curated questions — audited Cypher, plain-language framing.
# --------------------------------------------------------------------------- #
CURATED = [
    # ── INDIVIDUAL · understand the dog ────────────────────────────────
    {
        "cat": "individual",
        "q": "Kikoo looks normal compared to other Jack Russells, but he seems different lately. Why?",
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
    # ── RELATIONSHIPS · understand interactions ────────────────────────
    {
        "cat": "relationships",
        "q": "Should Kikoo meet Marlow tomorrow?",
        "cypher": (
            "MATCH (k:Dog {name:'Kikoo'})-[c:COMPATIBLE_WITH]->(m:Dog {name:'Marlow'})\n"
            "MATCH (m)-[:HAS_DRIFT]->(x:DriftEvent)-[:MODULATED_BY]->(ctx:ContextEvent)\n"
            "OPTIONAL MATCH (m)-[rr:RECOMMENDED_ROUTE]->(r:Route)\n"
            "RETURN m.name AS dog, c.previous_score AS score_before, c.score AS score_now,\n"
            "       c.reason AS compatibility_reason, x.rate AS drift_rate, x.severity AS severity,\n"
            "       collect(ctx.description) AS explained_by,\n"
            "       r.name AS alternative_route, rr.reason AS route_reason"
        ),
        "note": ("Four hops, one answer: yesterday's route crossed a high-noise area → "
                 "recovery remained incomplete → the compatibility score dropped → an "
                 "alternative route is recommended. That causal chain is native to a "
                 "graph — and invisible to a table of snapshots."),
    },
    {
        "cat": "individual",
        "q": "Which of my dogs have been quietly changing lately?",
        "cypher": (
            "MATCH (d:Dog)-[:HAS_DRIFT]->(x:DriftEvent)-[:DRIFTED_FROM]->(:Baseline)\n"
            "RETURN d.name AS dog, d.breed AS breed, x.rate AS drift_rate,\n"
            "       x.severity AS severity, x.detected_on AS detected_on\n"
            "ORDER BY x.rate DESC"
        ),
        "note": ("'Quietly' is the point — each of these drifts is invisible to a "
                 "population average. The graph measures every dog against its own "
                 "baseline: the individual reference frame."),
    },
    {
        "cat": "individual",
        "q": "Which dog should I check first today?",
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
    # ── CONTEXT · understand why ───────────────────────────────────────
    {
        "cat": "context",
        "q": "Is Kikoo changing because of context, or is something else going on?",
        "cypher": (
            "MATCH (d:Dog {name:'Kikoo'})-[:HAS_DRIFT]->(x:DriftEvent)\n"
            "OPTIONAL MATCH (x)-[:MODULATED_BY]->(c:ContextEvent)\n"
            "RETURN x.rate AS drift_rate, x.severity AS severity,\n"
            "       CASE WHEN c IS NULL THEN 'unexplained' ELSE 'context-explained' END AS status,\n"
            "       c.type AS context, c.description AS context_detail"
        ),
        "note": ("Context is the difference between an alarm and an explanation. "
                 "The MODULATED_BY edge is doing the interpretive work here."),
    },
    {
        "cat": "context",
        "q": "What changed before Kikoo's new walk recommendation?",
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
        "cat": "relationships",
        "q": "Which walk is safest for Kikoo today, and why?",
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
        "cat": "individual",
        "q": "Which dogs still look like themselves over time?",
        "cypher": (
            "MATCH (d:Dog)\n"
            "WHERE NOT (d)-[:HAS_DRIFT]->(:DriftEvent)\n"
            "RETURN d.name AS dog, d.breed AS breed\n"
            "ORDER BY d.name"
        ),
        "note": ("Stability is a finding too. These dogs remain closest to their own "
                 "baseline — the absence of a drift edge is itself information."),
    },
    {
        "cat": "individual",
        "q": "What does 'normal for Kikoo' actually look like?",
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
    {
        "cat": "relationships",
        "q": "Which dog has the best energy for a play walk today?",
        "cypher": (
            "MATCH (a:Dog)-[c:COMPATIBLE_WITH]->(b:Dog)\n"
            "WHERE c.score >= 0.7\n"
            "RETURN a.name AS dog, b.name AS partner, c.score AS compatibility,\n"
            "       c.reason AS why\n"
            "ORDER BY c.score DESC"
        ),
        "note": ("Play energy is not a property of one dog — it lives on the "
                 "relationship. The best match is the highest-scored edge whose "
                 "reason describes a matched tempo."),
    },
    {
        "cat": "relationships",
        "q": "Which dogs should avoid each other today?",
        "cypher": (
            "MATCH (a:Dog)-[c:COMPATIBLE_WITH]->(b:Dog)\n"
            "WHERE c.score < 0.5\n"
            "RETURN a.name AS dog, b.name AS other, c.score AS compatibility,\n"
            "       c.previous_score AS score_before, c.reason AS why\n"
            "ORDER BY c.score ASC"
        ),
        "note": ("'Avoid' is not a label — it is a low score with a reason attached. "
                 "One of these dropped only yesterday, and can recover as the "
                 "context clears."),
    },
    {
        "cat": "context",
        "q": "Where should each dog walk today, and why?",
        "cypher": (
            "MATCH (d:Dog)-[rr:RECOMMENDED_ROUTE]->(r:Route)-[:LOCATED_NEAR]->(l:Location)\n"
            "RETURN d.name AS dog, r.name AS route, r.terrain AS terrain,\n"
            "       r.intensity AS intensity, l.name AS near, rr.reason AS why\n"
            "ORDER BY d.name"
        ),
        "note": ("State-aware recommendation: the same three routes, matched "
                 "differently per dog — and every match ships with its why, "
                 "stored on the edge."),
    },
    # ── the question every owner asks ──────────────────────────────────
    {
        "cat": "signature",
        "q": "What changed — and should I worry?",
        "cypher": (
            "MATCH (d:Dog)-[:HAS_DRIFT]->(x:DriftEvent)\n"
            "OPTIONAL MATCH (x)-[:MODULATED_BY]->(c:ContextEvent)\n"
            "WITH d, x, collect(c.type) AS contexts\n"
            "RETURN d.name AS dog, x.rate AS drift_rate, x.severity AS severity,\n"
            "       CASE WHEN size(contexts) = 0 THEN 'worth a look — no explanation on file'\n"
            "            ELSE 'calm — explained by context' END AS should_i_worry,\n"
            "       contexts AS explained_by\n"
            "ORDER BY size(contexts) ASC, x.rate DESC"
        ),
        "note": ("The Barkley answer, one row per dog: change is measured against "
                 "the dog's own baseline, then checked for an explanation. Explained "
                 "change is calm. Unexplained change earns the first look."),
    },
]
CURATED_BY_Q = {c["q"]: c for c in CURATED}
FLAGSHIP_Q = CURATED[0]["q"]
SIGNATURE_Q = next(c["q"] for c in CURATED if c["cat"] == "signature")
PILLARS = [
    # key,            tag,                accent
    ("individual",    "// INDIVIDUAL",    "#7b9fff"),
    ("relationships", "// RELATIONSHIPS", "#a884ff"),
    ("context",       "// CONTEXT",       "#3fd6bc"),
]


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




# --------------------------------------------------------------------------- #
# v9 CSS
# --------------------------------------------------------------------------- #
V9_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter+Tight:wght@400;500;600;700&family=Inter:wght@400;500;600&family=Instrument+Serif:ital@0;1&family=JetBrains+Mono:wght@400;500;600&display=swap');

html, body, [class*="css"], .stMarkdown, p, li { font-family:'Inter','Helvetica Neue',sans-serif; }

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
h2.bk-h2{font-family:'Inter Tight',sans-serif !important;font-weight:500 !important;
  font-size:clamp(1.5rem,2.6vw,2.1rem) !important;letter-spacing:-.035em !important;
  color:#edebe4 !important;margin:2.6rem 0 1.2rem !important;padding-top:1.6rem !important;
  border-top:1px solid rgba(237,235,228,.07)}
h2.bk-h2 .bk-acc{font-size:1.04em}
.bk-acc{font-family:'Instrument Serif',serif;font-style:italic;font-weight:400;
  background:linear-gradient(120deg,#7b9fff,#c97bff);
  -webkit-background-clip:text;background-clip:text;-webkit-text-fill-color:transparent}
.bk-lead{font-size:1.02rem;line-height:1.65;color:rgba(237,235,228,.64);max-width:56rem;margin:0 0 .6rem}
.bk-pillar{display:flex;align-items:baseline;gap:.6rem;margin:0 0 .1rem}
.bk-ptag{font-family:'JetBrains Mono',monospace;font-size:.66rem;letter-spacing:.1em}

/* Question cards — one bordered container per category */
div[data-testid="stVerticalBlockBorderWrapper"]{
  border:1px solid rgba(237,235,228,.12) !important;border-radius:14px;
  background:rgba(237,235,228,.02)}

/* Question chips: gray until selected or hovered — fast human scanning */
div[data-testid="stButtonGroup"] button p{
  color:rgba(237,235,228,.5) !important;font-size:.85rem;transition:color .15s}
div[data-testid="stButtonGroup"] button:hover p{color:#edebe4 !important}
div[data-testid="stButtonGroup"] button[data-testid="stBaseButton-pillsActive"] p{
  color:#edebe4 !important}

/* Raw results — quiet mono table */
.bk-rows-wrap{overflow-x:auto;margin:.2rem 0 .6rem}
.bk-rows{width:100%;border-collapse:collapse;font-family:'JetBrains Mono',monospace;
  font-size:.72rem;line-height:1.5}
.bk-rows th{color:rgba(237,235,228,.42);text-align:left;font-weight:500;
  padding:.35rem .6rem;border-bottom:1px solid rgba(237,235,228,.14);white-space:nowrap}
.bk-rows td{color:rgba(237,235,228,.55);padding:.35rem .6rem;
  border-bottom:1px solid rgba(237,235,228,.06);vertical-align:top}
.bk-lead b{color:#edebe4;font-weight:600}

.bk-chain{display:flex;align-items:center;flex-wrap:wrap;gap:.4rem .3rem;margin:1rem 0 .4rem}
.bk-node{font-family:'JetBrains Mono',monospace;font-size:.7rem;color:rgba(237,235,228,.88);
  padding:.42rem .8rem;border-radius:999px;background:rgba(255,255,255,.04);
  border:1px solid rgba(237,235,228,.1);white-space:nowrap}
.bk-edge{width:22px;height:1px;background:linear-gradient(90deg,rgba(123,159,255,.5),rgba(201,123,255,.5))}

.bk-thirds{display:grid;grid-template-columns:1fr 1fr 1fr;gap:1rem;margin:.4rem 0 1rem}
@media(max-width:900px){.bk-thirds{grid-template-columns:1fr}}
.bk-card{border:1px solid rgba(237,235,228,.09);border-radius:16px;padding:1.3rem 1.4rem;
  background:rgba(255,255,255,.014);height:100%;box-sizing:border-box}
.bk-card .tag{font-family:'JetBrains Mono',monospace;font-size:.62rem;letter-spacing:.1em;
  text-transform:uppercase;margin-bottom:.6rem}
.bk-card h4{font-family:'Inter Tight',sans-serif;font-weight:600;font-size:1.12rem;
  letter-spacing:-.02em;color:#edebe4;margin:0 0 .45rem}
.bk-card p{font-size:.93rem;line-height:1.6;color:rgba(237,235,228,.64);margin:0}
.bk-verdict{font-family:'Instrument Serif',serif;font-style:italic;font-size:1.05rem}
.bk-same{display:flex;flex-direction:column;justify-content:center;height:100%;box-sizing:border-box;
  font-size:.98rem;color:rgba(237,235,228,.64);line-height:1.65;padding:.4rem .2rem}
.bk-same b{color:#edebe4}

/* jSite window — values from getbarkley v3 (the reference implementation) */
.win{border:1px solid rgba(237,235,228,.09);border-radius:14px;overflow:hidden;
  background:#0c0e13;margin:.4rem 0 .9rem;box-shadow:0 30px 80px -45px rgba(0,0,0,.95)}
.win *{margin:0;box-sizing:border-box}
.win-bar{display:flex;align-items:center;gap:.8rem;padding:.7rem 1rem;background:#0e1116;
  border-bottom:1px solid rgba(237,235,228,.05)}
.win-dots{display:flex;gap:6px}
.win-dots i{width:11px;height:11px;border-radius:50%;display:block}
.win-title{font-family:'JetBrains Mono',monospace;font-size:.72rem;color:rgba(237,235,228,.42);
  margin:0 auto;transform:translateX(-24px)}
.win-code{font-family:'JetBrains Mono',monospace !important;font-size:.78rem !important;
  line-height:1.7 !important;color:#c6ccd6 !important;background:#0c0e13 !important;
  padding:.9rem 1.2rem !important;white-space:pre-wrap;word-break:break-word;
  border:none !important;display:block}
.win-code .k{color:#7b9fff}.win-code .s{color:#3fd6bc}.win-code .t{color:#c97bff}
.win-status{display:flex;gap:1.1rem;padding:.45rem 1rem;background:#0e1116;
  border-top:1px solid rgba(237,235,228,.05);flex-wrap:wrap}
.win-status span{font-family:'JetBrains Mono',monospace;font-size:.64rem;color:rgba(237,235,228,.42)}
.win-status .ok{color:#3fd6bc}.win-status .br{color:#7b9fff}

.bk-gloss-grid{display:grid;grid-template-columns:1fr 1fr 1fr;gap:1rem;margin:.4rem 0 .6rem}
@media(max-width:900px){.bk-gloss-grid{grid-template-columns:1fr}}
.bk-gloss{border-top:1px solid rgba(237,235,228,.12);padding-top:.9rem;
  font-size:.88rem;line-height:1.6;color:rgba(237,235,228,.56)}
.bk-gloss b{display:block;color:#edebe4;font-weight:600;font-family:'Inter Tight',sans-serif;
  font-size:1rem;margin-bottom:.35rem}
.bk-gloss-link{font-family:'JetBrains Mono',monospace;font-size:.62rem;color:rgba(237,235,228,.42);margin:.2rem 0 0}
.bk-gloss-link a{color:rgba(123,159,255,.8);text-decoration:none}

.bk-honest{font-size:.88rem;line-height:1.6;color:rgba(237,235,228,.56)}
.bk-honest b{color:#edebe4;font-weight:600}
.bk-honest a{color:rgba(123,159,255,.8);text-decoration:none}
.bk-honest .bk-honest-links{margin-top:.8rem}

div.stButton>button{border-radius:999px;font-family:'Inter Tight',sans-serif}
div.stButton>button[kind="primary"]{background:linear-gradient(120deg,#7b9fff,#c97bff);border:none;font-weight:600}
div[data-testid="stChatMessage"]{background:transparent}

.bk-foot{text-align:center;font-family:'JetBrains Mono',monospace;font-size:.66rem;
  letter-spacing:.06em;color:rgba(237,235,228,.3);margin-top:2.4rem}
.bk-foot a{color:rgba(123,159,255,.7);text-decoration:none}
</style>
"""
st.markdown(V9_CSS, unsafe_allow_html=True)


def cypher_html(code: str) -> str:
    c = html.escape(code, quote=False)
    c = re.sub(r"('[^']*')", r'<span class="s">\1</span>', c)
    c = re.sub(r"(:`?[A-Za-z_]+`?)(?=[\s){\]])", r'<span class="t">\1</span>', c)
    c = re.sub(
        r"\b(MATCH|OPTIONAL|WHERE|WITH|RETURN|ORDER|BY|LIMIT|DISTINCT|AS|CASE|WHEN|THEN|ELSE|END|NOT|AND|OR|IS|NULL|DESC|ASC)\b",
        r'<span class="k">\1</span>', c)
    return c


def rows_table_html(rows: list[dict]) -> str:
    """Raw results as a quiet, stylable HTML table (st.dataframe is canvas —
    its text can't be muted with CSS)."""
    if not rows:
        return ""
    cols = list(rows[0].keys())

    def fmt(v) -> str:
        if v is None:
            return ""
        if isinstance(v, (list, tuple)):
            return ", ".join(str(x) for x in v)
        return str(v)

    head = "".join(f"<th>{html.escape(c)}</th>" for c in cols)
    body = "".join(
        "<tr>" + "".join(f"<td>{html.escape(fmt(r.get(c)))}</td>" for c in cols) + "</tr>"
        for r in rows
    )
    return (f'<div class="bk-rows-wrap"><table class="bk-rows">'
            f"<thead><tr>{head}</tr></thead><tbody>{body}</tbody></table></div>")


def jsite_window(title: str, body_html: str, status_html: str) -> str:
    return (
        '<div class="win">'
        '<div class="win-bar"><span class="win-dots">'
        '<i style="background:#ff5f57"></i><i style="background:#febc2e"></i><i style="background:#28c840"></i>'
        f'</span><span class="win-title">{html.escape(title)}</span></div>'
        f'<div class="win-code">{body_html}</div>'
        f'<div class="win-status">{status_html}</div>'
        '</div>'
    )


def _stream_words(text: str):
    for w in re.split(r"(\s+)", text):
        yield w
        if w.strip():
            time.sleep(0.012)


# --------------------------------------------------------------------------- #
# 1 · Header + claim
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
    <p class="bk-lead"><b>Every new day makes every previous day more valuable.
    Behavior accumulates. So does the moat.</b></p>
    <p class="bk-lead">DogGraph is Barkley's behavioral memory layer. It does not detect drift;
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
# 2 · The difference, in ten seconds — card | card | paragraph (thirds)
# --------------------------------------------------------------------------- #
st.markdown(
    '''
    <h2 class="bk-h2">The difference, <span class="bk-acc">in ten seconds.</span></h2>
    <div class="bk-thirds">
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
      <div class="bk-same"><span>Same dog. Same data. <b>Different reference — different
      conclusion.</b> This graph is the memory that makes the second answer possible:
      each dog's baseline, its drift, and the context that explains it, stored as
      relationships you can question.</span></div>
    </div>
    ''',
    unsafe_allow_html=True,
)

# --------------------------------------------------------------------------- #
# 3 · Run the graph — chat + artifact pane
# --------------------------------------------------------------------------- #
st.markdown(
    '<h2 class="bk-h2">Pick a question <span class="bk-acc">to run the graph.</span></h2>',
    unsafe_allow_html=True,
)

db_ok = _have_db()
pending: str | None = None

PILL_KEYS = ["qp_signature"] + [f"qp_{key}" for key, _, _ in PILLARS]


def _on_pick(changed_key: str) -> None:
    # Callbacks run before any widget is instantiated, so clearing the other
    # groups' selections here is legal — one highlighted chip across all groups.
    val = st.session_state.get(changed_key)
    if val:
        st.session_state["pending_q"] = val
        for k in PILL_KEYS:
            if k != changed_key:
                st.session_state[k] = None


# First visit: the flagship question asks itself.
if "booted" not in st.session_state:
    st.session_state["booted"] = True
    if db_ok:
        st.session_state["pending_q"] = FLAGSHIP_Q
        st.session_state["qp_individual"] = FLAGSHIP_Q

col_q, col_ans = st.columns([1, 1.4], gap="large")

with col_q:
    # Human questions, grouped the way Barkley reasons — Individual,
    # Relationships, Context — plus the one every owner actually asks.
    # One card per category, answer alongside: no scrolling to read it.
    if hasattr(st, "pills"):
        with st.container(border=True):
            st.markdown(
                '<div class="bk-pillar"><span class="bk-ptag" style="color:#c97bff">'
                '// THE QUESTION EVERY OWNER ASKS</span></div>',
                unsafe_allow_html=True,
            )
            st.pills("signature", options=[SIGNATURE_Q], selection_mode="single",
                     key="qp_signature", on_change=_on_pick, args=("qp_signature",),
                     label_visibility="collapsed")
        for key, tag, color in PILLARS:
            with st.container(border=True):
                st.markdown(
                    f'<div class="bk-pillar"><span class="bk-ptag" style="color:{color}">{tag}</span></div>',
                    unsafe_allow_html=True,
                )
                st.pills(key, options=[c["q"] for c in CURATED if c["cat"] == key],
                         selection_mode="single", key=f"qp_{key}",
                         on_change=_on_pick, args=(f"qp_{key}",),
                         label_visibility="collapsed")
    else:
        sel = st.selectbox("questions", ["—"] + [c["q"] for c in CURATED],
                           label_visibility="collapsed")
        if sel != "—" and st.button("Run", type="primary"):
            pending = sel

    picked_pending = st.session_state.pop("pending_q", None)
    if picked_pending:
        pending = picked_pending

with col_ans:
    # ---- handle the pending question: ONE exchange, replaced each time ----
    if pending:
        if not db_ok:
            st.error("Neo4j credentials missing — see deploy/DEPLOY.md.")
        else:
            res = _cached_curated(pending)
            st.session_state["current"] = {
                "q": pending, "res": res,
                "note": CURATED_BY_Q[pending]["note"], "streamed": False,
            }

    # ---- the single current exchange (answer types itself out once) ----
    current = st.session_state.get("current")
    if current:
        with st.chat_message("user"):
            st.markdown(current["q"])
        with st.chat_message("assistant", avatar=HALO_URL):
            answer = current["res"]["answer"] or f"_{current['res'].get('note') or 'No answer.'}_"
            if not current.get("streamed"):
                st.write_stream(_stream_words(answer))
                current["streamed"] = True
            else:
                st.markdown(answer)
            if current.get("note"):
                st.caption(current["note"])

        # ---- the artifact, right below the answer ----
        last = current["res"]
        if last.get("cypher"):
            status = (
                '<span class="br">⎇ read-only</span>'
                '<span class="ok">✓ validator</span>'
                '<span class="ok">✓ read transaction</span>'
                f'<span>mode: {html.escape(str(last.get("mode", "")))}</span>'
            )
            st.markdown(
                jsite_window("query.cypher — generated & validated",
                             cypher_html(last["cypher"]), status),
                unsafe_allow_html=True,
            )
        if last.get("rows"):
            st.markdown(
                f'<div class="bk-kicker" style="margin:.6rem 0 .1rem">Raw results · {len(last["rows"])} row(s)</div>'
                + rows_table_html(last["rows"]),
                unsafe_allow_html=True,
            )
        st.caption(
            "Every number came out of the graph — the model is only allowed to phrase "
            "what was retrieved."
        )

# --------------------------------------------------------------------------- #
# 4 · Glossary — one definition per column
# --------------------------------------------------------------------------- #
st.markdown(
    '''
    <div class="bk-gloss-grid">
      <div class="bk-gloss"><b>Individual Baseline</b>
        A per-individual longitudinal norm learned from that individual's own history,
        used as the reference frame for detecting change instead of a population average.</div>
      <div class="bk-gloss"><b>Behavioral Drift</b>
        A slow, cumulative divergence of an individual's behavior away from its own
        baseline — typically invisible to population statistics.</div>
      <div class="bk-gloss"><b>Reference Frame</b>
        The comparison standard a model uses to decide whether a behavior is normal;
        the same data can yield opposite conclusions under different reference frames.</div>
    </div>
    <p class="bk-gloss-link">Full canonical glossary →
      <a href="https://getbarkley.com/llms.txt" target="_blank">getbarkley.com/llms.txt</a></p>
    ''',
    unsafe_allow_html=True,
)

# --------------------------------------------------------------------------- #
# 5 · Under the hood — figures + pipeline + safety, at the end
# --------------------------------------------------------------------------- #
st.markdown('<h2 class="bk-h2">Under <span class="bk-acc">the hood.</span></h2>', unsafe_allow_html=True)
st.markdown('<p class="bk-lead"><b>Inference is disposable. Behavioral memory compounds.</b></p>',
            unsafe_allow_html=True)
here = os.path.dirname(os.path.abspath(__file__))
c1, c2 = st.columns(2, gap="large")
with c1:
    p = os.path.join(here, "screenshots", "doggraph_schema.png")
    if os.path.exists(p):
        st.image(p, caption="The DogGraph schema — the relationships are the product",
                 use_container_width=True)
with c2:
    p = os.path.join(here, "screenshots", "graph_render.png")
    if os.path.exists(p):
        st.image(p, caption="Kikoo's neighborhood — the memory being queried",
                 use_container_width=True)

c3, c4 = st.columns([2, 3], gap="large")
with c3:
    st.markdown(
        jsite_window(
            "pipeline — graphrag, strict sense",
            html.escape(
                "question\n"
                "  → LLM (schema-constrained, read-only rule)\n"
                "  → Cypher\n"
                "  → validator (writes + CALL refused)\n"
                "  → LIMIT enforced\n"
                "  → Neo4j, read transaction\n"
                "  → rows\n"
                "  → LLM ('ground strictly in these rows')\n"
                "  → answer",
                quote=False),
            '<span class="br">⎇ read-only</span><span class="ok">✓ three safety layers</span>',
        ),
        unsafe_allow_html=True,
    )
with c4:
    st.markdown(
        '<div class="bk-honest">'
        '<p><b>Honest by construction.</b> The LLM is an interface, not a reasoning engine: '
        'retrieval is the graph traversal, generation is grounded in the retrieved rows, '
        'and no write can ever reach the database — prompt rule, keyword validator, and a '
        'server-enforced read transaction, in depth. Drift <b>detection</b> happens in the '
        '<a href="https://github.com/labs-barkley/barkley-reference-architecture" target="_blank">'
        'Barkley Reference Architecture</a>; DogGraph is the behavioral memory it writes to.</p>'
        '<p class="bk-honest-links">'
        'Repo: <a href="https://github.com/labs-barkley/barkley-canine-cognition-lab/tree/main/neo4j-doggraph-demo" target="_blank">neo4j-doggraph-demo</a><br>'
        'Drift demo: <a href="https://drift-explorer.getbarkley.com" target="_blank">drift-explorer.getbarkley.com</a><br>'
        'Dataset: <a href="https://huggingface.co/datasets/labs-barkley/synthetic-doggraph-sample" target="_blank">synthetic-doggraph-sample</a><br>'
        'ORCID: <a href="https://orcid.org/0009-0004-6031-659X" target="_blank">0009-0004-6031-659X</a></p>'
        '</div>',
        unsafe_allow_html=True,
    )

st.markdown(
    '<div class="bk-foot">DogGraph stores conclusions, not methods.<br>'
    '© 2026 Barkley AI · synthetic data · patent applications filed · '
    'not a diagnostic tool · <a href="https://getbarkley.com" target="_blank">getbarkley.com</a></div>',
    unsafe_allow_html=True,
)
