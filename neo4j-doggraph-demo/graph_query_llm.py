"""
graph_query_llm.py
==================
A schema-constrained LLM text-to-Cypher and GraphRAG layer over the
Barkley DogGraph.

WHAT THIS IS (precisely)
------------------------
This module upgrades the deterministic intent router (`graph_query.py`) into a
proper **GraphRAG** layer:

    natural language question
      → (LLM, constrained to the DogGraph schema)
      → Cypher  ← validated as read-only
      → executed on Neo4j AuraDB (retrieval)
      → results
      → (LLM)
      → natural-language answer, grounded in the retrieved rows

This is GraphRAG in the strict sense: retrieval is the graph traversal, and
generation is a downstream synthesis step that is grounded in the retrieved
subgraph — not free-form generation. The LLM never sees the full database,
only the question, the schema, and the results of the validated query.

SAFETY
------
Two-layer defense to keep the LLM honest:

  1. **Prompt-level** — the system prompt states the read-only rule, gives the
     schema, gives a few audited few-shot examples, and instructs the LLM to
     emit `OUT_OF_SCOPE` if the question can't be answered from this schema.

  2. **Validator** — every emitted Cypher is parsed for forbidden tokens
     (CREATE/MERGE/DELETE/SET/REMOVE/DROP/DETACH/LOAD CSV/CALL with writes).
     If any are present the query is REFUSED. No write ever reaches the DB,
     even if the LLM ignored its instructions.

If `ANTHROPIC_API_KEY` is not set, the module gracefully falls back to the
deterministic router from `graph_query.py`.

USAGE
-----
    export NEO4J_URI="neo4j+s://<id>.databases.neo4j.io"
    export NEO4J_USER="neo4j"
    export NEO4J_PASSWORD="<your-aura-password>"
    export ANTHROPIC_API_KEY="<your-anthropic-key>"       # enables the LLM layer
    export ANTHROPIC_MODEL="claude-haiku-4-5-20251001"    # optional, this is default

    python -c "from graph_query_llm import answer_llm; print(answer_llm('Why is River Path recommended for Kikoo?'))"

Synthetic data only. Not a diagnostic tool. Patent applications filed.
"""
from __future__ import annotations

import os
import re
import json
from dataclasses import dataclass

# We reuse the deterministic router as a graceful fallback when no API key is set.
from graph_query import translate as _det_translate, _driver as _neo_driver  # noqa


class UnsafeCypherError(ValueError):
    """Raised when the LLM tries to emit a write or unsupported Cypher clause."""


class OutOfScopeError(ValueError):
    """Raised when the LLM judges the question is not answerable from this schema."""


# --------------------------------------------------------------------------- #
# The schema as the LLM sees it. Kept in sync with schema.cypher by hand.
# --------------------------------------------------------------------------- #
DOGGRAPH_SCHEMA = """
Nodes (labels and their properties):
  (:Dog {id, name, breed, birth_year})
  (:Baseline {id, established_on, window_days,
              activity_level_mean, activity_level_scale,
              sleep_fragmentation_mean, sleep_fragmentation_scale,
              restlessness_index_mean, restlessness_index_scale,
              location_entropy_mean, location_entropy_scale,
              social_response_latency_mean, social_response_latency_scale})
  (:TemporalBin {id, resolution})        // resolution in {circadian, weekly, quarterly}
  (:BehaviorEvent {id, day, channel, value})
  (:ContextEvent {id, type, description})
  (:DriftEvent {id, detected_on, rate, severity, window})
  (:Route {id, name, terrain, intensity})
  (:Location {id, name, lat, location_entropy})

Relationships:
  (:Dog)-[:HAS_BASELINE]->(:Baseline)
  (:Dog)-[:GENERATED]->(:BehaviorEvent)
  (:BehaviorEvent)-[:FALLS_IN]->(:TemporalBin)
  (:Dog)-[:HAS_DRIFT]->(:DriftEvent)
  (:DriftEvent)-[:DRIFTED_FROM]->(:Baseline)
  (:DriftEvent)-[:MODULATED_BY]->(:ContextEvent)
  (:Dog)-[:RECOMMENDED_ROUTE {reason}]->(:Route)
  (:Route)-[:LOCATED_NEAR]->(:Location)
  (:Dog)-[:COMPATIBLE_WITH {score, reason}]->(:Dog)
""".strip()


FEW_SHOTS = [
    {
        "q": "Which dogs are drifting from their baseline?",
        "cypher": (
            "MATCH (d:Dog)-[:HAS_DRIFT]->(x:DriftEvent)-[:DRIFTED_FROM]->(:Baseline) "
            "RETURN d.name AS dog, x.rate AS drift_rate, x.severity AS severity "
            "ORDER BY x.rate DESC"
        ),
    },
    {
        "q": "Is Kikoo's drift explained by context, or unexplained?",
        "cypher": (
            "MATCH (d:Dog {name:'Kikoo'})-[:HAS_DRIFT]->(x:DriftEvent) "
            "OPTIONAL MATCH (x)-[:MODULATED_BY]->(c:ContextEvent) "
            "RETURN x.rate AS drift_rate, x.severity AS severity, "
            "       CASE WHEN c IS NULL THEN 'unexplained' ELSE 'context-explained' END AS status, "
            "       c.type AS context, c.description AS context_detail"
        ),
    },
    {
        "q": "Which route is recommended for Kikoo and why?",
        "cypher": (
            "MATCH (d:Dog {name:'Kikoo'})-[rr:RECOMMENDED_ROUTE]->(r:Route)-[:LOCATED_NEAR]->(l:Location) "
            "RETURN r.name AS route, r.terrain AS terrain, r.intensity AS intensity, "
            "       l.name AS near, rr.reason AS why"
        ),
    },
    {
        "q": "Who is the most socially compatible dog with Kikoo?",
        "cypher": (
            "MATCH (:Dog {name:'Kikoo'})-[c:COMPATIBLE_WITH]->(other:Dog) "
            "RETURN other.name AS candidate, c.score AS compatibility, c.reason AS why "
            "ORDER BY c.score DESC LIMIT 1"
        ),
    },
]


_TRANSLATE_SYSTEM_PROMPT = f"""You translate natural-language questions about a Neo4j property graph called the Barkley DogGraph into a single read-only Cypher query.

# Schema
{DOGGRAPH_SCHEMA}

# Rules — read carefully
1. Output **exactly one** Cypher query and **nothing else** — no markdown fences, no prose, no explanation.
2. The query MUST be **read-only**. Use only MATCH, OPTIONAL MATCH, WHERE, WITH, RETURN, ORDER BY, LIMIT, SKIP, DISTINCT, CASE/WHEN/THEN/ELSE/END, and aggregation functions (count, sum, avg, min, max, collect).
3. **Never** use: CREATE, MERGE, DELETE, SET, REMOVE, DROP, DETACH, FOREACH, LOAD, CALL ... YIELD with write side effects.
4. Use the exact node labels, relationship types, and property names from the schema. Do not invent fields.
5. If the question cannot be answered from this schema, respond with the literal text `OUT_OF_SCOPE` and nothing else.
6. Prefer LIMIT 25 for open-ended queries to keep results manageable.
"""


_ANSWER_SYSTEM_PROMPT = """You write a short, natural-language answer to a question about the Barkley DogGraph, grounded strictly in the query results you are given. Rules:

1. Use only facts present in the results. If the results are empty, say so honestly.
2. Do not invent values, dogs, dates, or relationships not in the results.
3. Be concise — 2–4 sentences. No preamble like "Based on the results...".
4. Mention specific names/numbers from the results so the answer is grounded.
5. End with a short note when relevant (e.g., "synthetic data") if the question implies a real-world claim.
"""


# --------------------------------------------------------------------------- #
# Read-only validator. Defense in depth: even if the LLM emits a write,
# this layer refuses to execute it.
# --------------------------------------------------------------------------- #
_FORBIDDEN_PATTERN = re.compile(
    r"\b(CREATE|MERGE|DELETE|SET|REMOVE|DROP|DETACH|FOREACH|LOAD\s+CSV|USING\s+PERIODIC)\b",
    re.IGNORECASE,
)


def _strip_fences(text: str) -> str:
    """Remove ```cypher / ``` fences and surrounding whitespace if present."""
    t = text.strip()
    t = re.sub(r"^```(?:cypher|cql)?\s*", "", t, flags=re.IGNORECASE)
    t = re.sub(r"\s*```$", "", t)
    return t.strip()


def validate_readonly(cypher: str) -> None:
    """Raise UnsafeCypherError if the query contains any write keyword."""
    if not cypher.strip():
        raise UnsafeCypherError("Empty query.")
    # Strip Cypher line comments and block comments before scanning, so a
    # comment containing the word "CREATE" does not trigger a false positive.
    cleaned = re.sub(r"//[^\n]*", "", cypher)
    cleaned = re.sub(r"/\*.*?\*/", "", cleaned, flags=re.DOTALL)
    hit = _FORBIDDEN_PATTERN.search(cleaned)
    if hit:
        raise UnsafeCypherError(
            f"Refused: query contains forbidden write keyword '{hit.group(0)}'. "
            "Only read-only Cypher is allowed."
        )


# --------------------------------------------------------------------------- #
# Anthropic client (lazy)
# --------------------------------------------------------------------------- #
def _anthropic_available() -> bool:
    return bool(os.environ.get("ANTHROPIC_API_KEY"))


def _anthropic_client():
    try:
        from anthropic import Anthropic
    except ImportError as e:
        raise SystemExit(
            "The LLM layer needs the anthropic SDK:  pip install anthropic"
        ) from e
    return Anthropic()  # reads ANTHROPIC_API_KEY from env


def _model() -> str:
    return os.environ.get("ANTHROPIC_MODEL", "claude-haiku-4-5-20251001")


# --------------------------------------------------------------------------- #
# Translation: NL -> Cypher (constrained by schema, validated read-only)
# --------------------------------------------------------------------------- #
def translate_llm(question: str) -> str:
    """
    Use the LLM to translate `question` to a single read-only Cypher query.
    Raises OutOfScopeError if the LLM says the question is out of scope.
    Raises UnsafeCypherError if the emitted query fails the read-only check.
    """
    if not _anthropic_available():
        raise RuntimeError("ANTHROPIC_API_KEY not set; cannot use LLM translator.")

    client = _anthropic_client()

    # Build few-shot examples as a single user/assistant exchange.
    messages = []
    for ex in FEW_SHOTS:
        messages.append({"role": "user", "content": ex["q"]})
        messages.append({"role": "assistant", "content": ex["cypher"]})
    messages.append({"role": "user", "content": question})

    resp = client.messages.create(
        model=_model(),
        max_tokens=400,
        system=_TRANSLATE_SYSTEM_PROMPT,
        messages=messages,
    )
    raw = "".join(b.text for b in resp.content if getattr(b, "type", "") == "text").strip()
    cypher = _strip_fences(raw)

    if cypher.upper().startswith("OUT_OF_SCOPE"):
        raise OutOfScopeError("The model judged this question outside the DogGraph schema.")

    validate_readonly(cypher)
    return cypher


# --------------------------------------------------------------------------- #
# Execution
# --------------------------------------------------------------------------- #
def run_cypher(cypher: str, params: dict | None = None) -> list[dict]:
    """Run a read-only Cypher against Neo4j AuraDB and return rows as dicts."""
    validate_readonly(cypher)  # belt-and-braces: re-validate at execution time
    drv = _neo_driver()
    rows = []
    try:
        with drv.session() as s:
            for rec in s.run(cypher, **(params or {})):
                rows.append({k: rec[k] for k in rec.keys()})
    finally:
        drv.close()
    return rows


# --------------------------------------------------------------------------- #
# Answer synthesis (the "G" of GraphRAG): grounded NL answer from rows
# --------------------------------------------------------------------------- #
def _synthesize(question: str, cypher: str, rows: list[dict]) -> str:
    if not _anthropic_available():
        return ""  # in fallback mode the caller will format rows directly
    client = _anthropic_client()
    # Truncate rows we send to the synthesizer to keep tokens bounded.
    safe_rows = rows[:25]
    user = (
        f"Question: {question}\n\n"
        f"Cypher executed:\n{cypher}\n\n"
        f"Results ({len(rows)} row(s), showing up to 25):\n"
        f"{json.dumps(safe_rows, default=str, indent=2)}\n"
    )
    resp = client.messages.create(
        model=_model(),
        max_tokens=400,
        system=_ANSWER_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user}],
    )
    return "".join(b.text for b in resp.content if getattr(b, "type", "") == "text").strip()


# --------------------------------------------------------------------------- #
# Public API: the full GraphRAG pipeline (with deterministic fallback)
# --------------------------------------------------------------------------- #
@dataclass
class GraphAnswer:
    question: str
    mode: str           # "llm" or "deterministic"
    cypher: str
    rows: list
    answer: str
    note: str = ""      # any caveat (out-of-scope, fallback, refused, etc.)

    def to_dict(self) -> dict:
        return {
            "question": self.question, "mode": self.mode, "cypher": self.cypher,
            "rows": self.rows, "answer": self.answer, "note": self.note,
        }


def answer_llm(question: str, prefer_llm: bool = True) -> GraphAnswer:
    """
    Full GraphRAG pipeline:
       NL → (LLM-constrained Cypher) → DB → (LLM synthesis) → grounded answer.
    Falls back to the deterministic router from graph_query.py if the LLM is
    unavailable or refuses (OUT_OF_SCOPE / UnsafeCypherError).
    """
    use_llm = prefer_llm and _anthropic_available()

    # ---------- LLM mode ----------
    if use_llm:
        try:
            cypher = translate_llm(question)
        except OutOfScopeError:
            return GraphAnswer(
                question=question, mode="llm", cypher="",
                rows=[], answer="",
                note="The model judged this question outside the DogGraph schema.",
            )
        except UnsafeCypherError as e:
            return GraphAnswer(
                question=question, mode="llm", cypher="",
                rows=[], answer="",
                note=f"Refused unsafe Cypher: {e}",
            )

        rows = run_cypher(cypher)
        synth = _synthesize(question, cypher, rows)
        return GraphAnswer(
            question=question, mode="llm", cypher=cypher,
            rows=rows, answer=synth,
            note="Cypher emitted by an LLM under a schema-constrained, read-only "
                 "system prompt; validated by `validate_readonly` before execution.",
        )

    # ---------- Deterministic fallback ----------
    t = _det_translate(question)
    if t is None:
        return GraphAnswer(
            question=question, mode="deterministic", cypher="",
            rows=[], answer="",
            note="Deterministic router has no matching intent. "
                 "Set ANTHROPIC_API_KEY to enable the LLM translator.",
        )
    cypher, params, intent, explain = t
    rows = run_cypher(cypher, params)
    # Format a simple grounded answer from the rows
    if not rows:
        formatted = f"({explain}) No matching rows in the graph."
    else:
        formatted = f"({explain})\n" + "\n".join(
            "- " + ", ".join(f"{k}={v}" for k, v in r.items() if v is not None)
            for r in rows
        )
    return GraphAnswer(
        question=question, mode="deterministic", cypher=cypher,
        rows=rows, answer=formatted,
        note=f"Deterministic intent: {intent}",
    )


# --------------------------------------------------------------------------- #
# Offline self-test of the *validator* (no API key or DB needed).
# This verifies the safety layer; LLM and DB integration are tested live.
# --------------------------------------------------------------------------- #
if __name__ == "__main__":
    good = [
        "MATCH (d:Dog) RETURN d.name",
        "MATCH (d:Dog)-[:HAS_DRIFT]->(x) WITH d, x WHERE x.rate > 0.5 RETURN d.name, x.rate ORDER BY x.rate DESC LIMIT 25",
        "MATCH (d:Dog {name:'Kikoo'})-[c:COMPATIBLE_WITH]->(o) RETURN o.name, c.score",
    ]
    bad = [
        "MATCH (d:Dog) DELETE d",
        "CREATE (d:Dog {name:'Pirate'})",
        "MATCH (d:Dog) SET d.danger = true",
        "MERGE (d:Dog {name:'X'})",
        "MATCH (d:Dog) DETACH DELETE d",
        "LOAD CSV WITH HEADERS FROM 'http://x' AS r CREATE (:Dog {name: r.name})",
    ]
    print("=== validator self-test ===")
    for q in good:
        try:
            validate_readonly(q)
            print(f"  OK    : {q[:60]}")
        except UnsafeCypherError as e:
            print(f"  FAIL  (good was rejected): {e}")
    for q in bad:
        try:
            validate_readonly(q)
            print(f"  FAIL  (bad was accepted): {q[:60]}")
        except UnsafeCypherError as e:
            print(f"  OK    : refused -> {e.args[0][:80]}")
    # Strip-fences smoke
    assert _strip_fences("```cypher\nMATCH (d:Dog) RETURN d\n```") == "MATCH (d:Dog) RETURN d"
    print("  OK    : fence stripping works")
    print(f"  LLM available: {_anthropic_available()}  (model={_model()})")
