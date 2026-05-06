# Barkley Thesis

*Version 1.0 — May 2026*

---

## The Central Argument

**Current canine behavioral monitoring is limited by breed-level aggregation.**  
**Barkley explores individual longitudinal behavioral modeling as an alternative.**

This is a methodological position — not a clinical claim. It has clear precedent in human health informatics and has not yet been systematically applied to companion animal behavioral data.

---

## 1. The Structural Limitation of Breed-Level Norms

The dominant paradigm in canine behavioral monitoring compares an individual dog to a population average, typically stratified by breed. A dog is flagged as behaviorally anomalous when its measurements deviate significantly from this external reference point.

This paradigm has a structural limitation: **it erases individual behavioral identity.**

Dogs, like humans, have stable individual cognitive and behavioral profiles — what Duke Canine Cognition Center researchers call a "cognitive fingerprint." These profiles vary substantially within any breed. A Labrador that has always been low-energy is not the same as a Labrador that has become low-energy. Breed-level models treat them identically.

The consequence: **early behavioral change may remain invisible to population-normative models.** A dog drifting from its own established behavioral baseline can remain statistically normal for its breed for months — exactly the window where behavioral observation may be most valuable.

---

## 2. The Individual Longitudinal Alternative

Individual longitudinal modeling inverts the reference frame.

Instead of asking: *"Is this dog normal for its breed?"*  
Barkley explores: *"Is this dog normal for itself — relative to its own behavioral history?"*

This requires:

1. **A stable individual baseline** — established from the dog's own behavioral history over sufficient observation time
2. **Multi-resolution temporal monitoring** — tracking behavioral signals across day-level, week-level, and quarter-level windows simultaneously
3. **Rate-of-change features** — measuring not where behavior is, but how fast and in what direction it is moving
4. **Individual behavioral phenotyping** — characterizing each dog's stable profile across dimensions drawn from canine cognition research (inhibitory control, communication, memory, physical reasoning)

The methodological precedent is well-established in human health informatics. Electronic phenotyping, temporal binning, and individual baseline anomaly detection are standard tools in human EHR analysis (Banda et al., 2018; Shah, 2019). Their application to continuous companion animal behavioral data is novel — and, we believe, overdue.

---

## 3. The Missing Data Paradox

Real-world canine behavioral data is inherently messy. Dogs travel. Sensors fail. Owners forget to log.

Standard approaches treat these gaps as noise to be eliminated — imputed or excluded.

Barkley proposes a three-category taxonomy. Behavioral data gaps carry distinct interpretive implications depending on their cause:

- **Artefactual absence** — structurally absent because a behavior category does not apply to this individual
- **Systemic absence** — missing due to non-behavioral factors (device failure, travel, boarding)
- **Informative absence** — extended absence of anomalous signals that may itself be a meaningful behavioral observation in longitudinal monitoring

The third category is the counterintuitive one. A prolonged absence of nocturnal restlessness signals can be a meaningful behavioral observation — it encodes stability. Eliminating it through imputation may destroy longitudinal signal.

This reframing — **data absence as a structured behavioral feature rather than noise** — is one of Barkley's core conceptual contributions. It requires empirical validation.

---

## 4. The DogGraph: From Individual to Collective Intelligence

Individual longitudinal behavioral profiles, generated at scale, create the raw material for a population-level behavioral knowledge graph: the **DogGraph**.

The DogGraph maps relationships between behavioral signals, environmental contexts, temporal patterns, and individual outcomes across the companion animal population. It transforms isolated individual trajectories into computable collective intelligence.

The specific implementation of this architecture — its data structures, graph schema, and inference mechanisms — is proprietary and not described in this repository. What this repository demonstrates are the conceptual foundations that make such a graph meaningful: individual baselines, temporal drift detection, and structured absence encoding.

---

## Scope and Limitations

This thesis represents a research agenda, not a validated behavioral system.

- The individual baseline methodology has not been prospectively validated
- Temporal drift thresholds used in demonstrations are exploratory, not calibrated
- The DogGraph is an architectural concept; its construction is a future research program
- All demonstrations in this repository use synthetic data

The framework draws on well-validated methods from adjacent fields. Its application to companion animal health monitoring requires empirical validation before any real-world use.

---

## One Sentence

> *A dog can remain normal for its breed while becoming behaviorally different from itself.*  
> Barkley is the research framework built to explore that difference.

---

*Elodie P. Remoissenet — Founder, Barkley AI*  
*Research correspondence: invest@getbarkley.com*
