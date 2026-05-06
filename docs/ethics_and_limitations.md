# Ethics and Limitations

*Barkley Canine Cognition Lab — v1.0, May 2026*

---

## What This Repository Is

This repository is a **research framework and technical demonstrator**. It uses **synthetic data only** and is intended to illustrate a methodological approach — individual-centric longitudinal behavioral modeling for companion animals.

It is **not** a clinical system, a diagnostic tool, a validated detection system, or a medical product of any kind.

---

## Explicit Limitations

### On the Data

- All data in this repository is synthetically generated. It was not collected from real animals or real owners.
- Breed behavioral parameters used in generation are **illustrative estimates**, not clinically validated population norms.
- The synthetic generation model makes simplifying assumptions about behavioral patterns that may not reflect real-world complexity.

### On the Methodology

- The individual baseline framework has **not been prospectively validated** against any behavioral or health endpoint.
- Drift detection thresholds are **exploratory**, not calibrated. They should not be interpreted as behavioral detection standards.
- The Missing Data Paradox taxonomy is a conceptual framework. Its operationalization requires domain expert validation.
- The DogGraph is an architectural concept. No production system has been constructed or validated.

### On Generalizability

- Individual baseline modeling requires sufficient longitudinal data to establish a stable individual profile. The minimum observation period is not established by this research.
- Breed-stratified calibration of all parameters is likely necessary in any real-world extension.

---

## What This Repository Does Not Claim

- That it can detect, predict, or diagnose any health condition in any animal
- That its behavioral drift detection methodology has demonstrated sensitivity or specificity
- That synthetic drift patterns match any real behavioral progression
- That individual baseline thresholds used here are appropriate for real-world use
- That any specific biomarker, hormonal, or physiological signal is captured or modeled here

---

## Privacy

**This repository contains no personal data.** The synthetic dataset was generated programmatically. It does not represent real animals, real owners, or real behavioral records of any kind.

Any future extension to real behavioral data would require:

- **Informed consent** from dog owners, with explicit disclosure of what behavioral data is collected, how it is stored, and how long it is retained
- **Data minimization** — collecting only the signals necessary for the stated research purpose
- **Purpose limitation** — behavioral data collected for one purpose not repurposed without renewed consent
- **Right to erasure** — owners must be able to request deletion of their data and their dog's behavioral record
- **Transparency** — clear, plain-language explanation of what "behavioral monitoring" means in practice and what inferences may be drawn
- **Security by design** — behavioral time-series data constitutes sensitive personal data and must be protected accordingly
- **Veterinary ethical oversight** of any system producing health-adjacent outputs

In the context of companion animal behavioral monitoring, the owner's behavioral data (routines, location patterns, owner-absence events) is often as sensitive as the dog's. Privacy frameworks must protect both.

---

## Data Ethics

**No real animal data is used.** If this framework is extended to real behavioral data:

- Animal welfare protocols and relevant regulatory frameworks must be respected
- Veterinary oversight of any system producing health-adjacent behavioral outputs is mandatory
- **Algorithmic equity** is a first-class concern. Breed-based normative systems can reinforce disparities in care access by disadvantaging mixed-breed dogs or breeds underrepresented in any training data. Individual baseline modeling partially mitigates this — but does not eliminate it.
- Socioeconomic proxies embedded in behavioral data (e.g., absence patterns that correlate with owner work schedules, housing conditions) must be identified and audited

---

## Responsible Use

This repository is shared for academic and research purposes. It should not be used to:

- Make veterinary decisions about real animals
- Market or advertise any clinical capability
- Train production systems without substantial independent validation

---

## Feedback

Methodological feedback from the veterinary, data science, and animal cognition research communities is welcome. Open an issue or contact [invest@getbarkley.com](mailto:invest@getbarkley.com).

---

*Barkley AI, 2026. Research framework and technical demonstrator using synthetic data only.*
