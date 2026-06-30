---
title: Workflow Families
audience: mixed
type: index
status: canonical
owner: bijux-proteomics-docs
last_reviewed: 2026-05-09
---

# Workflow Families

This page compares the six workflow families as product families, not as a
diffuse set of package artifacts. It is the fastest route from a family name to
its current trust status, run mode, benchmark coverage, and remaining blocker
story.

## Family Comparison

| workflow family | trust status | primary run mode | benchmark coverage | current blockers | start here |
| --- | --- | --- | --- | --- | --- |
| `dda` | outsider-auditable, bounded | `import_only` | flagship package plus companion generalization package | still not raw-executable and still lacks in-repo live-engine parity | [Why Trust DDA](https://bijux.io/bijux-proteomics/01-bijux-proteomics/foundation/why-trust-dda/) |
| `dia` | outsider-auditable, bounded | `raw_executable` | flagship package plus companion generalization package | broader biological confidence still stops at library incompleteness and absent-peptide consequences | [Why Trust DIA](https://bijux.io/bijux-proteomics/01-bijux-proteomics/foundation/why-trust-dia/) |
| `lfq` | review-grade, bounded | `raw_executable` | flagship package plus companion generalization package | external review kit readiness and acceptance pressure still block the stronger outsider-facing sentence | [Why Trust LFQ](https://bijux.io/bijux-proteomics/01-bijux-proteomics/foundation/why-trust-lfq/) |
| `multiplex` | internal-support-only | `raw_executable` | flagship package plus companion generalization package | companion rerun path still collapses outsider-facing trust | [Why Multiplex Stops At Internal Support](https://bijux.io/bijux-proteomics/01-bijux-proteomics/foundation/why-multiplex-stops-at-internal-support/) |
| `ptm` | outsider-auditable, bounded | `raw_executable` | flagship package plus companion generalization package | downstream consequence confidence remains narrower than localization evidence | [Why Trust PTM](https://bijux.io/bijux-proteomics/01-bijux-proteomics/foundation/why-trust-ptm/) |
| `targeted` | outsider-auditable, bounded | `raw_executable` | flagship package plus companion generalization package | vendor-parity and calibration-clean certainty are still outside the supported lane | [Why Trust Targeted](https://bijux.io/bijux-proteomics/01-bijux-proteomics/foundation/why-trust-targeted/) |

## Best Next Routes

- Open [DDA Cross-Package Handbook](https://bijux.io/bijux-proteomics/01-bijux-proteomics/foundation/dda-cross-package-handbook/)
  when the question is how one real flagship family crosses foundation, core,
  runtime, knowledge, intelligence, and lab without package-handbook hopping.
- Open [Scientist Journey](https://bijux.io/bijux-proteomics/01-bijux-proteomics/foundation/scientist-journey/)
  when the question is how one family connects benchmark assets, runtime
  evidence, curated knowledge, recommendation posture, and lab consequence.
- Open [Benchmark Assets](https://bijux.io/bijux-proteomics/04-bijux-proteomics-core/foundation/benchmark-assets/)
  when the question is whether the public package roots are complete and
  current enough.
- Open [Execution](https://bijux.io/bijux-proteomics/09-bijux-proteomics-runtime/execution-overview/)
  when the question is whether the current run mode and rerun lane deserve the
  published language.
- Open [Decision Support](https://bijux.io/bijux-proteomics/01-bijux-proteomics/foundation/decision-support/)
  when the question is whether grounding, contradiction, recommendation, or
  public artifact roles change the family call.

## Boundary

This page compares families. It should not be the only explanation for any one
family once the reader knows which route they need next.
