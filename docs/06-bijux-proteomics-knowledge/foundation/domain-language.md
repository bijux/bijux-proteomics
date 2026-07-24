---
title: Domain Language
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-knowledge-docs
last_reviewed: 2026-07-21
---

# Domain Language

Knowledge terminology separates what was observed, what is asserted, and how strongly an assertion is currently supported.

| Term | Meaning |
| --- | --- |
| **evidence record** | A sourced observation, import, inference, model output, or curated statement with identity and provenance |
| **claim** | A testable assertion linked to supporting and contradicting evidence and explicit assumptions |
| **evidence kind** | The scientific family of support, such as literature, structure, assay, phenotype, pathway, safety, or proteomics |
| **origin** | Whether evidence is observed, inferred, imported, or synthetic |
| **extraction method** | How a record entered memory: curation, import, model inference, or lab capture |
| **strength** | Exploratory, supporting, or decisive contribution under a declared context |
| **confidence** | A bounded assessment of support; not a probability of universal truth unless a model explicitly establishes that interpretation |
| **polarity** | Whether a claim or record supports, contradicts, or remains neutral toward a decision context |
| **evidence state** | Supported, contradicted, conflicted, or unresolved state of a claim |
| **stale** | Evidence or a claim whose freshness no longer satisfies the active policy |
| **contradiction** | Credible evidence that conflicts with another record or claim under comparable context |
| **conflict cluster** | Related contradictions grouped by decision area and conflict type |
| **reconciliation** | A policy-governed account of how conflicting evidence is held, split, curated, or provisionally preferred |
| **trust** | A composite assessment derived from source, provenance, quality, freshness, and consistency—not source prestige alone |
| **grounding** | Mapping an identifier or assertion to a reference context while retaining ambiguity and release information |
| **coverage** | The measured extent to which a declared entity set is represented under a named reference and policy |
| **decision lineage** | Trace from a decision area to its claims, disputed claims, and evidence records |

Persistence is not validation, resolution is not erasure, grounding is not universal identity, and confidence is not recommendation authority. These distinctions are the package’s central trust contract.
