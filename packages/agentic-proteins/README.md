# Agentic Proteins
<a id="top"></a>

**A deterministic, artifact-first protein design runtime and CLI** — strict invariants, reproducible runs, and traceable outputs. Build reliable design workflows that are audit-ready and repeatable.

[![PyPI - Version](https://img.shields.io/pypi/v/agentic-proteins.svg)](https://pypi.org/project/agentic-proteins/)
[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-blue.svg)](https://pypi.org/project/agentic-proteins/)
[![Typing: typed (PEP 561)](https://img.shields.io/badge/typing-typed-4F8CC9.svg)](https://peps.python.org/pep-0561/)
[![License: Apache-2.0](https://img.shields.io/badge/license-Apache--2.0-green.svg)](https://github.com/bijux/bijux-proteomics/blob/main/LICENSE)
[![Documentation](https://img.shields.io/badge/docs-GitHub%20Pages-brightgreen)](https://bijux.github.io/bijux-proteomics/)
[![CI Status](https://github.com/bijux/bijux-proteomics/actions/workflows/ci.yml/badge.svg)](https://github.com/bijux/bijux-proteomics/actions)

> **At a glance:** deterministic execution • artifact immutability • invariant enforcement • reproducible runs • API + CLI surfaces • structured telemetry  
> **Quality:** coverage floors enforced per module, benchmark regression gate active, docs linted and built in CI, no telemetry.

---

## Table of Contents

* [Why Agentic Proteins?](#why-agentic-proteins)
* [Try It in 20 Seconds](#try-it-in-20-seconds)
* [Key Features](#key-features)
* [Installation](#installation)
* [Quick Start](#quick-start)
* [Artifacts & Reproducibility](#artifacts--reproducibility)
* [API Surface](#api-surface)
* [Built-in Commands](#built-in-commands)
* [Tests & Quality](#tests--quality)
* [Project Tree](#project-tree)
* [Docs & Resources](#docs--resources)
* [Contributing](#contributing)
* [License](#license)



---

<a id="why-agentic-proteins"></a>
## Why Agentic Proteins?

Most protein design tooling prioritizes iteration speed. Agentic Proteins prioritizes **repeatability, traceability, and audit-ready artifacts**:

* **Determinism first** for reliable experiments and CI validation.
* **Artifact immutability** with hash-checked outputs.
* **Invariant enforcement** for predictable execution paths.
* **Clear boundaries** between deterministic execution and stochastic components.



---

<a id="try-it-in-20-seconds"></a>
## Try It in 20 Seconds

```bash
pipx install agentic-proteins  # Or: pip install agentic-proteins
agentic-proteins --version
agentic-proteins run --sequence "ACDEFGHIKLMNPQRSTVWY"
agentic-proteins inspect-candidate <candidate_id>
```



---

<a id="key-features"></a>
## Key Features

* **Deterministic execution** — reproducible runs with seeded randomness.
* **Artifact-first workflow** — immutable artifacts with stable hashes.
* **Invariant enforcement** — fail-fast checks across runtime boundaries.
* **Dual surface** — CLI and API share the same contracts.
* **Structured telemetry** — correlation IDs and traceable logs.



---

<a id="installation"></a>
## Installation

Requires **Python 3.11+**.

```bash
# Isolated install (recommended)
pipx install agentic-proteins

# Standard
pip install agentic-proteins
```

Upgrade: `pipx upgrade agentic-proteins` or `pip install --upgrade agentic-proteins`.



---

<a id="quick-start"></a>
## Quick Start

```bash
# Discover commands/flags
agentic-proteins --help

# Run a deterministic design cycle
agentic-proteins run --sequence "ACDEFGHIKLMNPQRSTVWY" --seed 7

# Inspect artifacts
agentic-proteins inspect-candidate <candidate_id>
```



---

<a id="artifacts--reproducibility"></a>
## Artifacts & Reproducibility

Artifacts are immutable and hash-addressed. Reproducing a run verifies hashes before returning outputs.

```bash
agentic-proteins reproduce <run_id>
```

Docs: [Execution Lifecycle](https://bijux.github.io/bijux-proteomics/architecture/execution_lifecycle/) · [Invariants](https://bijux.github.io/bijux-proteomics/architecture/invariants/)



---

<a id="api-surface"></a>
## API Surface

The HTTP API exposes the same contracts as the CLI.

Docs: [API Overview](https://bijux.github.io/bijux-proteomics/api/overview/) · [Schema](https://bijux.github.io/bijux-proteomics/api/schema/)



---

<a id="built-in-commands"></a>
## Built-in Commands

| Command | Description | Example |
| ------- | ----------- | ------- |
| `run` | Execute a design run | `agentic-proteins run --sequence ...` |
| `inspect-candidate` | Inspect a candidate artifact | `agentic-proteins inspect-candidate <id>` |
| `reproduce` | Replay a run with hash checks | `agentic-proteins reproduce <run_id>` |
| `api` | Start the API server | `agentic-proteins api --host 0.0.0.0` |

Full surface: [CLI Surface](https://bijux.github.io/bijux-proteomics/interface/cli_surface/)



---

<a id="tests--quality"></a>
## Tests & Quality

* **Coverage floors:** enforced per module in CI.
* **Benchmarks:** regression gate on critical path.
* **Docs:** linted and built in CI.

Quick commands:

```bash
make test
make lint
make quality
```

Artifacts: Generated in CI; see GitHub Actions for logs and reports.



---

<a id="project-tree"></a>
## Project Tree

```
api/            # OpenAPI schemas
configs/        # Lint/type/security configs
docs/           # MkDocs site
makes/          # Task modules (docs, test, lint, etc.)
scripts/        # Helper scripts
packages/agentic-proteins/src/agentic_proteins/  # Runtime + CLI implementation
tests/          # unit / integration / e2e
```



---

<a id="docs--resources"></a>
## Docs & Resources

* **Site**: https://bijux.github.io/bijux-proteomics/
* **Changelog**: https://github.com/bijux/bijux-proteomics/blob/main/CHANGELOG.md
* **Repository**: https://github.com/bijux/bijux-proteomics
* **Issues**: https://github.com/bijux/bijux-proteomics/issues
* **Security** (private reports): https://github.com/bijux/bijux-proteomics/security/advisories/new
* **Artifacts**: https://bijux.github.io/bijux-proteomics/artifacts/



---

<a id="contributing"></a>
## Contributing

Welcome. See **[CONTRIBUTING.md](https://github.com/bijux/bijux-proteomics/blob/main/CONTRIBUTING.md)** for setup and test guidance.



---

<a id="license"></a>
## License

Apache-2.0 — see **[LICENSE](https://github.com/bijux/bijux-proteomics/blob/main/LICENSE)**.
© 2025 Bijan Mousavi.
