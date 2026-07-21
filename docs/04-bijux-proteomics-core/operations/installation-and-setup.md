---
title: Installation and Setup
audience: mixed
type: how-to
status: canonical
owner: bijux-proteomics-core-docs
last_reviewed: 2026-07-21
---

# Installation and Setup

Install `bijux-proteomics-core` for scientific data models, file readers, sequence and chemistry operations, identification, quantification, study validation, interpretation, and the scientific CLI. Install Runtime separately when the application needs governed run orchestration, persistence, replay, providers, or service interfaces.

## Requirements

- Python 3.11 or newer
- an isolated Python environment
- enough local memory for the chosen spectra, identification, or quantitative workload

Core installs NumPy, Biopython, Pydantic, Click, DefusedXML, Loguru, and the Foundation contract kernel. PyArrow is optional.

## Install the scientific package

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install bijux-proteomics-core
bijux-proteomics --help
```

Install Parquet support only when the workflow reads or writes that format:

```bash
python -m pip install "bijux-proteomics-core[parquet]"
```

A successful `--help` confirms command registration. It does not validate a scientific workflow, input format, reference database, or output contract.

## Select the narrowest proof route

| Intended use | Initial verification |
| --- | --- |
| FASTA and sequence handling | parse a small known FASTA and verify sequence count, identifiers, and checksum |
| spectra or search-result import | use a checked-in fixture for the exact format and inspect parser warnings |
| identification and FDR | run target–decoy and protein-inference cases with known acceptance outcomes |
| quantification | verify units, missingness, aggregation scope, and multiple-testing family |
| PTM analysis | retain modification identity, residue position, localization evidence, and ambiguity |
| study design | validate contrasts, batches, pairing, replicates, and timepoint structure |
| report or artifact generation | compare deterministic fields, provenance, warnings, and schema version |

## Source checkout

From the repository root:

```bash
python -m pip install -e "packages/bijux-proteomics-core[test,parquet]"
python -m pytest packages/bijux-proteomics-core/tests
```

Use a narrower test family while developing—such as `tests/io`, `tests/identification`, `tests/quantification`, or `tests/study`—then run the package suite before release. The full suite is large because it defends independent scientific domains and cross-domain workflows.

## Keep data and execution explicit

Do not rely on the current directory for scientific assets. Pass input and output paths explicitly, retain reference versions, and write generated results under a governed artifact location. Record command arguments, package versions, schema identities, warnings, and input fingerprints whenever results will be reviewed or compared later.
