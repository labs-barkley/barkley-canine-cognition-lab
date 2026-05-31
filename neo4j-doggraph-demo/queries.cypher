// ===========================================================================
// Barkley DogGraph — showcase queries
// Run AFTER schema.cypher + seed_synthetic.cypher.
// Each query answers a *relational* question a flat tracker cannot.
// Synthetic data only. Not a diagnostic tool.
// ===========================================================================


// ---------------------------------------------------------------------------
// Q1. Which dogs are drifting from their OWN baseline (not a breed average)?
//     Returns each dog with a detected drift, ranked by rate. This is the core
//     Barkley idea: change is measured against the individual, longitudinally.
// ---------------------------------------------------------------------------
MATCH (d:Dog)-[:HAS_DRIFT]->(x:DriftEvent)-[:DRIFTED_FROM]->(:Baseline)
RETURN d.name AS dog, d.breed AS breed,
       x.rate AS drift_rate, x.severity AS severity, x.detected_on AS detected_on
ORDER BY x.rate DESC;


// ---------------------------------------------------------------------------
// Q2. Which drift events are EXPLAINED BY CONTEXT (vs. unexplained)?
//     The "Sovereignty of Silence" idea: not every change is alarming — some
//     are context-explained (recovery, a known low-activity period). Unexplained
//     drift is what deserves a closer look.
// ---------------------------------------------------------------------------
MATCH (d:Dog)-[:HAS_DRIFT]->(x:DriftEvent)
OPTIONAL MATCH (x)-[:MODULATED_BY]->(c:ContextEvent)
RETURN d.name AS dog,
       x.rate AS drift_rate,
       CASE WHEN c IS NULL THEN 'UNEXPLAINED — review'
            ELSE 'explained by context' END AS status,
       c.type AS context, c.description AS context_detail
ORDER BY (c IS NULL) DESC, x.rate DESC;


// ---------------------------------------------------------------------------
// Q3. Which route fits Kikoo's CURRENT state, and why?
//     Route recommendation is a function of the dog's present behavioral state
//     (here, elevated drift → a calmer, lower-intensity route).
// ---------------------------------------------------------------------------
MATCH (d:Dog {name: 'Kikoo'})-[rr:RECOMMENDED_ROUTE]->(r:Route)-[:LOCATED_NEAR]->(l:Location)
OPTIONAL MATCH (d)-[:HAS_DRIFT]->(x:DriftEvent)
RETURN d.name AS dog,
       r.name AS route, r.terrain AS terrain, r.intensity AS intensity,
       l.name AS near, rr.reason AS why,
       x.severity AS current_drift;


// ---------------------------------------------------------------------------
// Q4. Which dog is socially compatible with Kikoo, and WHY?
//     Compatibility is a scored, explained relationship (PPA-02). The graph
//     surfaces both the best match and the reasoning behind it.
// ---------------------------------------------------------------------------
MATCH (k:Dog {name: 'Kikoo'})-[c:COMPATIBLE_WITH]->(other:Dog)
RETURN other.name AS candidate, other.breed AS breed,
       c.score AS compatibility, c.reason AS why
ORDER BY c.score DESC;


// ---------------------------------------------------------------------------
// BONUS. Kikoo's full neighbourhood — one query, the whole behavioral memory.
//        Great for a Neo4j Bloom / graph-viz screenshot.
// ---------------------------------------------------------------------------
MATCH p = (d:Dog {name: 'Kikoo'})-[*1..2]-(n)
RETURN p;
