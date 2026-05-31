"""
graph_query.py
==============
A small natural-language -> Cypher layer over the Barkley DogGraph.

WHAT THIS IS (honestly)
-----------------------
A **deterministic intent router**: it matches a question to one of a handful of
known graph questions and runs a *parameterised, reviewed* Cypher query. It is
NOT a large-language-model text-to-Cypher system, and it does not invent queries.

Why deterministic? Because for a health-adjacent demo, a fixed set of audited
graph queries is safer and more honest than free-form generation. The seam for a
true LLM translator is marked clearly below (`translate`): drop an LLM call there
that emits Cypher constrained to this schema, and you have graph-grounded
retrieval ("GraphRAG"). Until then, call it what it is.

USAGE
-----
    export NEO4J_URI="neo4j+s://<your-aura-id>.databases.neo4j.io"
    export NEO4J_USER="neo4j"
    export NEO4J_PASSWORD="<your-password>"
    python ask.py "Why is River Path recommended for Kikoo today?"

Synthetic data only. Not a diagnostic tool.
"""
from __future__ import annotations

import os
import re
from dataclasses import dataclass


@dataclass
class Intent:
    name: str
    # keywords (lowercased) that, if present, select this intent
    triggers: list
    cypher: str
    explain: str  # how to read the result


# A dog name is pulled from the question if present; defaults to Kikoo.
_KNOWN_DOGS = ["kikoo", "juno", "pixel", "marlow", "sable", "ollie"]


INTENTS = [
    Intent(
        name="drifting_dogs",
        triggers=["drifting", "drift from", "drifting from", "changing", "which dogs are drift"],
        cypher="""
            MATCH (d:Dog)-[:HAS_DRIFT]->(x:DriftEvent)-[:DRIFTED_FROM]->(:Baseline)
            RETURN d.name AS dog, x.rate AS drift_rate, x.severity AS severity
            ORDER BY x.rate DESC
        """,
        explain="Dogs moving away from their own baseline, ranked by drift rate.",
    ),
    Intent(
        name="explained_by_context",
        triggers=["explained", "context", "why is the drift", "unexplained", "should i worry"],
        cypher="""
            MATCH (d:Dog)-[:HAS_DRIFT]->(x:DriftEvent)
            OPTIONAL MATCH (x)-[:MODULATED_BY]->(c:ContextEvent)
            RETURN d.name AS dog, x.rate AS drift_rate,
                   CASE WHEN c IS NULL THEN 'UNEXPLAINED - review' ELSE 'explained by context' END AS status,
                   c.type AS context
            ORDER BY (c IS NULL) DESC, x.rate DESC
        """,
        explain="Which drifts are context-explained vs. worth a closer look.",
    ),
    Intent(
        name="route_for_dog",
        triggers=["route", "walk", "recommended", "path", "where should", "take "],
        cypher="""
            MATCH (d:Dog {name: $dog})-[rr:RECOMMENDED_ROUTE]->(r:Route)-[:LOCATED_NEAR]->(l:Location)
            OPTIONAL MATCH (d)-[:HAS_DRIFT]->(x:DriftEvent)
            RETURN d.name AS dog, r.name AS route, r.terrain AS terrain,
                   r.intensity AS intensity, l.name AS near, rr.reason AS why,
                   x.severity AS current_drift
        """,
        explain="The route matched to the dog's current behavioral state, with reasoning.",
    ),
    Intent(
        name="compatibility",
        triggers=["compatible", "compatibility", "match", "play with", "friend", "social"],
        cypher="""
            MATCH (k:Dog {name: $dog})-[c:COMPATIBLE_WITH]->(other:Dog)
            RETURN other.name AS candidate, c.score AS compatibility, c.reason AS why
            ORDER BY c.score DESC
        """,
        explain="Scored, explained social matches for the dog.",
    ),
]


def extract_dog(question: str) -> str:
    q = question.lower()
    for name in _KNOWN_DOGS:
        if name in q:
            return name.capitalize()
    return "Kikoo"  # default focus dog


def translate(question: str):
    """
    Map a natural-language question to (cypher, params, intent, explain).

    >>> This is the seam for a real LLM translator. <<<
    To upgrade to LLM-backed text-to-Cypher (GraphRAG), replace the keyword
    matching below with an LLM call that is given this graph's schema and is
    constrained to return read-only Cypher. Keep the parameterisation.
    """
    q = question.lower().strip()
    best = None
    for intent in INTENTS:
        if any(t in q for t in intent.triggers):
            best = intent
            break
    if best is None:
        return None
    params = {}
    if "$dog" in best.cypher:
        params["dog"] = extract_dog(question)
    return best.cypher.strip(), params, best.name, best.explain


# --------------------------------------------------------------------------- #
# Execution (needs a live Neo4j + the `neo4j` driver). Lazy-imported so that
# `translate` can be used / tested without a database or the driver installed.
# --------------------------------------------------------------------------- #
def _driver():
    try:
        from neo4j import GraphDatabase
    except ImportError as e:
        raise SystemExit("Install the driver:  pip install neo4j") from e
    uri = os.environ.get("NEO4J_URI")
    user = os.environ.get("NEO4J_USER", "neo4j")
    pwd = os.environ.get("NEO4J_PASSWORD")
    if not uri or not pwd:
        raise SystemExit("Set NEO4J_URI and NEO4J_PASSWORD (see .env.example).")
    return GraphDatabase.driver(uri, auth=(user, pwd))


def answer(question: str) -> str:
    t = translate(question)
    if t is None:
        return ("I can answer questions about: drifting dogs, whether a drift is "
                "explained by context, route recommendations, and social compatibility.\n"
                "Try: \"Which dogs are drifting from their baseline?\"")
    cypher, params, intent, explain = t
    rows = []
    drv = _driver()
    with drv.session() as s:
        for rec in s.run(cypher, **params):
            rows.append(dict(rec))
    drv.close()

    out = [f"Q: {question}",
           f"   [intent: {intent}] {explain}",
           f"   [cypher] {' '.join(cypher.split())}",
           ""]
    if not rows:
        out.append("   (no matching results in the graph)")
    for r in rows:
        out.append("   - " + ", ".join(f"{k}={v}" for k, v in r.items() if v is not None))
    return "\n".join(out)


if __name__ == "__main__":
    # Offline self-test of the translator (no database needed).
    samples = [
        "Which dogs are drifting from their baseline?",
        "Is Kikoo's drift explained by context, or should I worry?",
        "Why is a route recommended for Kikoo today?",
        "Which dog is socially compatible with Kikoo?",
        "What's the capital of France?",  # should fall through
    ]
    for s in samples:
        t = translate(s)
        tag = t[2] if t else "NO MATCH (graceful fallback)"
        print(f"[{tag}]  {s}")
