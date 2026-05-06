# Scientific Positioning

*Where Barkley Sits in the Research Landscape*

---

## The Existing Paradigm

Current companion animal behavioral monitoring — both in academic research and commercial wearable products — operates primarily within a **normative paradigm**: behavioral signals are interpreted by comparison to population-level reference distributions, typically stratified by breed.

This paradigm produces useful insights at the population level. It is architecturally limited at the individual level.

The limitations are structural, not incidental:

1. **Breed-level norms erase within-breed cognitive diversity.** Research from the Duke Canine Cognition Center (MacLean et al., 2014; Gnanadesikan et al., 2020) establishes that cognitive profiles vary substantially within breeds. Two dogs of the same breed may have fundamentally different baseline behavioral architectures.

2. **Population cross-sections cannot capture longitudinal trajectories.** Gradual behavioral change is characterized by *drift* — a directional change over time — not by deviation from a population mean at any single moment. Cross-sectional models are blind to trajectory.

3. **Static norms applied to a non-stationary process produce systematic misclassification.** Dog behavior changes across the lifespan. A behavioral signal normal for a 2-year-old Labrador is not the same as one normal for a 10-year-old Labrador. Applying a fixed breed standard to a changing individual introduces systematic bias.

---

## The Barkley Position

Barkley operates within the tradition of **health informatics** applied to companion animal behavioral data — drawing on methodologies developed for human EHR analysis (electronic phenotyping, temporal binning, individual baseline anomaly detection) and grounding them in canine cognition research.

The methodological shift is from:
- **Normative discrimination** (is this dog normal for its breed?)

To:
- **Individual trajectory analysis** (is this dog normal for itself, compared to its own longitudinal history?)

This is not a novel methodological contribution in isolation — individual baseline approaches are standard in human health monitoring. The novelty is in their **systematic application to continuous companion animal behavioral data** within a unified computational architecture.

---

## Relationship to Existing Research

| Research Domain | Relationship to Barkley |
|----------------|------------------------|
| Duke Canine Cognition Center | Foundation: individual cognitive fingerprint theory, cognitive dimensions |
| Stanford clinical data mining | Methodological source: temporal binning, electronic phenotyping |
| Canine behavioral health literature | Application context (Azkona 2009, Salvin 2010) |
| Commercial pet wearables | Current paradigm Barkley argues against — normative, non-longitudinal |
| Human EHR informatics | Methodological source domain (Banda 2018, Lasko 2013) |

Note: this repository draws on methodologies developed in human clinical informatics. We use the term **health informatics** (rather than clinical informatics) when describing Barkley's own application domain, since this repository is a research framework — not a clinical tool — and uses synthetic data only.

---

## The DogGraph in Context

The DogGraph concept draws on **biomedical knowledge graph** research (Rotmensch et al., 2017) and applies it to the challenge of structuring multi-source, temporally complex companion animal behavioral data into a computable representation.

Knowledge graphs have demonstrated utility in human health informatics for:
- Cross-patient pattern recognition
- Signal disambiguation (is this behavioral pattern meaningful given the individual's history and context?)
- Longitudinal cohort construction for research

Their systematic application to companion animal behavioral data is, to our knowledge, novel.

The specific implementation of the DogGraph — its data structures, schema, and inference mechanisms — is proprietary and not described in this repository. What is described here are the conceptual foundations: individual baselines, temporal drift detection, and structured absence encoding.

---

*Full references in [`references.md`](references.md).*
