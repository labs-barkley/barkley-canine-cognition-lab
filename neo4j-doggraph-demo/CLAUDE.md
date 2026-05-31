# CLAUDE.md

This folder is a public-safe Neo4j / DogGraph demonstrator for Barkley (v2).

Rules:

- Use synthetic data only.
- Do not add real dog, owner, veterinary, location, investor, or partner data.
- Do not claim clinical validation, diagnosis, medical use, or veterinary
  decision-making.
- Do not use "patented"; use "patent applications filed" only where needed.
- Do not add exact patent filing references or confidential data-room materials.
- Keep the module framed as: synthetic data, research demonstrator, not a
  diagnostic tool.
- Keep Neo4j usage honest: property graph schema, Cypher queries, synthetic seed
  data, and a reproducible demo.

About the natural-language layers (v2):

- `graph_query.py` is the deterministic intent router. Predictable, no LLM.
- `graph_query_llm.py` is a **schema-constrained GraphRAG layer**: LLM
  text-to-Cypher (Anthropic API) → read-only validated → executed → grounded
  LLM synthesis from rows.
- The read-only validator in `graph_query_llm.py` is load-bearing safety. Any
  edit that loosens or removes it (e.g. allowing `SET`, `CREATE`, `MERGE`,
  `DELETE`, `REMOVE`, `DROP`, `DETACH`, `FOREACH`, `LOAD CSV`, `USING PERIODIC`)
  is a regression and must be refused.
- The LLM layer must always fall back gracefully to the deterministic router
  when `ANTHROPIC_API_KEY` is absent. Do not introduce a hard dependency on the
  API key.
- The Streamlit app (`app.py`) must read credentials from `st.secrets` (cloud)
  or `os.environ` (local). Never hardcode keys, never echo them.

About the rendered figure (`screenshots/graph_render.png`):

- It is generated from the same canonical structure in `seed_synthetic.cypher`
  by `make_seed_render.py`. If the seed changes, regenerate the figure so the
  visual remains honest.
