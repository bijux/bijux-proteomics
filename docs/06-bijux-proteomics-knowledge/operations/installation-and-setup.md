---
title: Installation and Setup
audience: mixed
type: how-to
status: canonical
owner: bijux-proteomics-knowledge-docs
last_reviewed: 2026-07-21
---

# Installation and Setup

Install `bijux-proteomics-knowledge` to model scientific evidence and claims, normalize evidence into reviewable memory, preserve contradictions, resolve biological identities and associations, measure annotation coverage, and assemble decision briefs.

## Requirements

- Python 3.11 or newer
- an isolated Python environment
- compatible Foundation and Core packages, installed automatically
- explicit source material for any knowledge being curated

The package does not download reference databases, literature, ontologies, or credentials during installation. Bundled fixtures support reproducible tests; they are not substitutes for current external scientific sources.

## Install from PyPI

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install bijux-proteomics-knowledge
```

Confirm schema compatibility through the public surface:

```python
from bijux_proteomics_foundation import DocumentSchema
from bijux_proteomics_knowledge import evaluate_schema_compatibility

schema = DocumentSchema(
    created_by="knowledge-setup-check",
    document_kind="annotation_pack",
    package_name="bijux-proteomics-knowledge",
)
report = evaluate_schema_compatibility(schema)

assert report.compatible
```

That check establishes document compatibility only. It does not establish that annotations are current, identifiers are resolvable, citations support a claim, or a bundle is free from contradiction.

## Prepare a reviewable evidence fixture

Include enough variation to exercise the package contract:

- unique evidence and claim identifiers;
- source type, origin, extraction method, dates, and citations;
- organism and scientific context where identity depends on them;
- quantitative support with units and uncertainty when applicable;
- duplicate, malformed, stale, ambiguous, and contradictory cases;
- expected ingestion counts and rejection reasons;
- expected graph-integrity and reconciliation outcomes.

Separate external references from checked-in fixture records in manifests and descriptions. A reproducible fixture proves behavior against a known case; it does not prove external completeness or freshness.

## Source checkout

From the repository root:

```bash
python -m pip install -e "packages/bijux-proteomics-knowledge[test]"
python -m pytest packages/bijux-proteomics-knowledge/tests
```

During development, run the matching families under `tests/contracts`, `tests/memory`, `tests/references`, `tests/reviews`, and the biological resolver tests. A curation path is ready only when normalization, provenance, ambiguity, contradiction, coverage, and deterministic rendering are all verified.
