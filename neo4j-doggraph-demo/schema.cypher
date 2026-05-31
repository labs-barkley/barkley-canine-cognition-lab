// ===========================================================================
// Barkley DogGraph — schema (constraints + indexes)
// Run this FIRST, before seed_synthetic.cypher.
// Neo4j 5.x / AuraDB. Synthetic data only. Not a diagnostic tool.
// ===========================================================================
//
// MODEL (the behavioral-intelligence layer, expressed as a graph)
// ---------------------------------------------------------------------------
//   (:Dog)          a single animal — the unit of reference
//   (:Baseline)     the dog's Individual Cognitive Fingerprint (ICF), per channel
//   (:TemporalBin)  a resolution: circadian (24h) / weekly (7d) / quarterly (91d)
//   (:BehaviorEvent)an observed, individual-referenced behavioral reading
//   (:ContextEvent) a situational cause (the missingness / "Sovereignty of Silence" taxonomy)
//   (:DriftEvent)   a detected change in the *rate* a dog moves away from its own baseline
//   (:Route)        a walk/route option, with terrain + intensity
//   (:Location)     a place, carrying a privacy-preserving location_entropy scalar
//
// RELATIONSHIPS
//   (:Dog)-[:HAS_BASELINE]->(:Baseline)
//   (:Dog)-[:GENERATED]->(:BehaviorEvent)-[:FALLS_IN]->(:TemporalBin)
//   (:Dog)-[:HAS_DRIFT]->(:DriftEvent)-[:DRIFTED_FROM]->(:Baseline)
//   (:DriftEvent)-[:MODULATED_BY]->(:ContextEvent)      // context explains the drift
//   (:Dog)-[:RECOMMENDED_ROUTE {reason}]->(:Route)-[:LOCATED_NEAR]->(:Location)
//   (:Dog)-[:COMPATIBLE_WITH {score, reason}]->(:Dog)   // social compatibility
//
// The point: "drifting from itself", "explained by context", "compatible with",
// and "right route for current state" are all *relationship* questions — which is
// exactly what a graph answers natively, and a flat tracker cannot.
// ===========================================================================

// --- Uniqueness constraints (also create backing indexes on :id) ---
CREATE CONSTRAINT dog_id            IF NOT EXISTS FOR (d:Dog)           REQUIRE d.id IS UNIQUE;
CREATE CONSTRAINT baseline_id       IF NOT EXISTS FOR (b:Baseline)      REQUIRE b.id IS UNIQUE;
CREATE CONSTRAINT tbin_id           IF NOT EXISTS FOR (t:TemporalBin)   REQUIRE t.id IS UNIQUE;
CREATE CONSTRAINT bevent_id         IF NOT EXISTS FOR (e:BehaviorEvent) REQUIRE e.id IS UNIQUE;
CREATE CONSTRAINT ctxevent_id       IF NOT EXISTS FOR (c:ContextEvent)  REQUIRE c.id IS UNIQUE;
CREATE CONSTRAINT driftevent_id     IF NOT EXISTS FOR (x:DriftEvent)    REQUIRE x.id IS UNIQUE;
CREATE CONSTRAINT route_id          IF NOT EXISTS FOR (r:Route)         REQUIRE r.id IS UNIQUE;
CREATE CONSTRAINT location_id       IF NOT EXISTS FOR (l:Location)      REQUIRE l.id IS UNIQUE;

// --- Secondary indexes for common lookups ---
CREATE INDEX dog_name    IF NOT EXISTS FOR (d:Dog)        ON (d.name);
CREATE INDEX drift_rate  IF NOT EXISTS FOR (x:DriftEvent) ON (x.rate);
CREATE INDEX bin_res     IF NOT EXISTS FOR (t:TemporalBin) ON (t.resolution);

// Schema ready. Now run seed_synthetic.cypher.
