# Evaluation Guide — Barkley DogGraph (Neo4j demo · v2)

This is a 5-minute, 30-minute, and 60-minute reading path for a CTO or technical
co-founder evaluating the Barkley DogGraph pack. It is deliberately short: the
pack is small (~12 files), and the goal of this guide is to point you at the
right things in the right order, not to re-narrate what you can already read.

> Synthetic data only. Not a diagnostic tool. Patent applications filed.

---

## Three orientation questions

Before opening any file, hold these three questions in mind. The pack is built
to give honest answers to all three:

1. **Is the choice of a graph database actually motivated, or is it neo4j-as-
   sponsor-badge?**
2. **Where is the LLM, and is it allowed to write to the database?** (No.)
3. **What is real here, and what is still synthetic / not validated?**

If by the end of this guide any of those three is unclear, the pack has failed
its own bar.

---

## 5-minute scan

| Step | File | What you should see |
|------|------|---------------------|
| 1 | [`README.md`](./README.md) | The "Why a graph" section ties each Barkley primitive (individual baseline, drift, context, route, compatibility) to a literal edge type. If those four bullets don't read as relationships rather than columns, the modelling premise is wrong. |
| 2 | [`screenshots/graph_render.png`](./screenshots/graph_render.png) | The seeded subgraph. Six synthetic dogs, three drifts, two context modulations, four recommended routes, five compatibility edges. Kikoo is highlighted. This is the topology the rest of the pack reasons over. |
| 3 | [`schema.cypher`](./schema.cypher) | Eight node labels, the relationship vocabulary, eight uniqueness constraints, three lookup indexes. No magic. |
| 4 | [`queries.cypher`](./queries.cypher) | The four showcase questions, each as a single MATCH with a clear traversal. Read these to see whether the schema actually answers the questions cleanly — i.e. whether the modelling has earned its keep. |

If those four pass the smell test, the modelling story holds and you can stop
here for the 5-minute version.

---

## 30-minute deep look

Add to the scan above:

### 1. Reproduce locally on AuraDB free tier (~5 min)

```bash
# Spin up a free instance at https://neo4j.com/product/auradb/
# In Neo4j Browser, run in order:
:source schema.cypher
:source seed_synthetic.cypher
:source queries.cypher
```

Each of the four showcase queries should return rows that match what
`screenshots/graph_render.png` shows. The bonus query at the bottom of
`queries.cypher` returns a visualizable subgraph for Bloom/Browser — that screenshot
is the authentic equivalent of the programmatic render shipped here.

### 2. Read the LLM / GraphRAG layer

[`graph_query_llm.py`](./graph_query_llm.py) is the most load-bearing file in the
pack. Spend most of your time here.

What to verify:

- **`_TRANSLATE_SYSTEM_PROMPT`** — the system prompt states the schema, the
  read-only rule, the OUT_OF_SCOPE escape hatch. The few-shot examples come
  straight from `queries.cypher`.
- **`validate_readonly()`** — the post-hoc safety scanner. It strips Cypher
  comments first (so `// CREATE` doesn't false-trigger) and then refuses any
  query containing `CREATE`, `MERGE`, `DELETE`, `SET`, `REMOVE`, `DROP`,
  `DETACH`, `FOREACH`, `LOAD CSV`, or `USING PERIODIC`.
- **Defense in depth** — `run_cypher()` re-validates at execution time even if
  the caller already validated. Belt and braces.
- **`answer_llm()`** — the public entry point. The pipeline is:

  ```
  question → (LLM, constrained) → Cypher → validate → execute → rows
           → (LLM, "ground in rows") → grounded NL answer
  ```

  This is GraphRAG in the strict sense (retrieval is the graph traversal,
  generation is grounded on retrieved rows), not free-form LLM-with-a-database.

- **Graceful fallback** — if `ANTHROPIC_API_KEY` is absent or the LLM emits
  `OUT_OF_SCOPE` / unsafe Cypher, `answer_llm()` returns a `GraphAnswer` with a
  meaningful `note` and (where applicable) falls back to the deterministic
  router from [`graph_query.py`](./graph_query.py).

Quick offline check (no API key, no DB):

```bash
python graph_query_llm.py
# Runs the validator self-test on 4 read-only queries (must pass)
# and 6+ write attempts (must be refused).
```

### 3. Read the Streamlit app

[`app.py`](./app.py) is intentionally thin: a UI over `answer_llm`. What to
verify:

- Credentials are read from `st.secrets` (Streamlit Cloud) **then** environment
  variables (local) **then** nothing — no hardcoded keys, ever.
- The "Translator" toggle is honest: it surfaces the choice between
  schema-constrained LLM and the deterministic router, and tells the operator
  when it has fallen back.
- Generated Cypher is shown **before** the synthesized answer. The system never
  presents an answer the user can't audit against the query that produced it.

---

## 60-minute pull-the-thread

If you want to push further:

- **`generate_seed.py`** — deterministic synthetic data generator (seeded at 42).
  Read this to confirm there is no real-animal data anywhere; the entire graph
  is procedurally generated.
- **`make_seed_render.py`** — the figure above is built from the same canonical
  structure. Re-run it after changes to the seed to keep the figure honest.
- **Drift vs context: pick a dog and follow the path.**
  - *Kikoo's* drift (rate 0.62) is modulated by `ctx_low_activity_period` —
    "informative silence" confirmed by a second channel.
  - *Marlow's* drift (0.55) is modulated by `ctx_post_surgery_recovery` — a
    known clinical context.
  - *Juno's* drift (0.41) is **not** modulated by any `ContextEvent` — this is
    the unexplained case the framework flags. Run query #2 in `queries.cypher`
    to see this directly.
- **Compatibility colors in the render.** Edge color encodes the score band
  (green ≥ 0.70, amber 0.50–0.69, red < 0.50). Kikoo→Sable at 0.34 (red) and
  Kikoo→Ollie at 0.86 (green) are the two clearest pairs.

---

## What this pack is, and what it isn't

It **is**:

- A faithful translation of Barkley's core behavioral primitives into a graph
  schema, with a synthetic seed that exercises every relationship in the model.
- A working, deployable Streamlit app and CLI over a real Neo4j AuraDB
  connection.
- A schema-constrained GraphRAG layer with two-layer read-only safety, honest
  about its fallback behavior.
- ~12 files. Small on purpose.

It **isn't**:

- A diagnostic or clinical tool.
- Validated on real animals.
- A production data platform — this is a research demonstrator on synthetic data.
- A claim that the IP described in the framework paper is "patented" — patent
  applications are *filed*, not granted.

---

## Where to push back if you're skeptical

A reviewer's job is to push. Reasonable lines of pushback we expect:

- **"The graph is too small."** — Correct. The seed exists to exercise every
  edge type with a clear semantic, not to benchmark scale. `generate_seed.py`
  scales out trivially.
- **"GraphRAG is fashionable; do you actually need it?"** — For the showcase
  queries, the deterministic router is enough. The LLM layer earns its keep
  the moment questions stop fitting four canned intents — i.e. in any real
  product UI. It is opt-in for exactly that reason.
- **"Read-only validation by regex is brittle."** — Defense in depth, not the
  only line. Production should additionally use a Neo4j role with no write
  permissions; the validator catches accidental writes before they reach the
  driver, but a least-privilege DB user is the load-bearing control.
- **"You're using synthetic data."** — Yes. The framework paper is explicit
  that all results are on synthetic data. Real-data work requires consented
  cohorts and IRB-equivalent process, which is separate from this demonstrator.

---

## Pointers outside this folder

- Lab repo (root): <https://github.com/labs-barkley/barkley-canine-cognition-lab>
- Drift demo (deployed): <https://drift-explorer.getbarkley.com>
- Reference architecture: <https://github.com/labs-barkley/barkley-reference-architecture>
- Public synthetic dataset: <https://huggingface.co/datasets/labs-barkley/synthetic-doggraph-sample>
- ORCID: <https://orcid.org/0009-0004-6031-659X>

Questions or critical pushback are welcome — that's the point of this guide.
