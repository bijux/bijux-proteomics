# proteomics-core

<!-- bijux-proteomics-badges:generated:start -->
[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-3776AB?logo=python&logoColor=white)](https://pypi.org/project/proteomics-core/)
[![Typing: typed](https://img.shields.io/badge/typing-typed%20(PEP%20561)-0A7BBB)](https://pypi.org/project/proteomics-core/)
[![License: Apache-2.0](https://img.shields.io/badge/license-Apache--2.0-0F766E)](https://github.com/bijux/bijux-proteomics/blob/main/LICENSE)
[![CI Status](https://github.com/bijux/bijux-proteomics/actions/workflows/verify.yml/badge.svg?branch=main)](https://github.com/bijux/bijux-proteomics/actions/workflows/verify.yml?query=branch%3Amain)
[![GitHub Repository](https://img.shields.io/badge/github-bijux%2Fbijux--proteomics-181717?logo=github)](https://github.com/bijux/bijux-proteomics)

[![proteomics-core](https://img.shields.io/pypi/v/proteomics-core?label=proteomics--core&logo=pypi)](https://pypi.org/project/proteomics-core/)
[![agentic-proteins](https://img.shields.io/pypi/v/agentic-proteins?label=agentic--proteins&logo=pypi)](https://pypi.org/project/agentic-proteins/)
[![bijux-proteomics-foundation](https://img.shields.io/pypi/v/bijux-proteomics-foundation?label=foundation&logo=pypi)](https://pypi.org/project/bijux-proteomics-foundation/)
[![bijux-proteomics-core](https://img.shields.io/pypi/v/bijux-proteomics-core?label=core&logo=pypi)](https://pypi.org/project/bijux-proteomics-core/)
[![bijux-proteomics-runtime](https://img.shields.io/pypi/v/bijux-proteomics-runtime?label=runtime&logo=pypi)](https://pypi.org/project/bijux-proteomics-runtime/)
[![bijux-proteomics-intelligence](https://img.shields.io/pypi/v/bijux-proteomics-intelligence?label=intelligence&logo=pypi)](https://pypi.org/project/bijux-proteomics-intelligence/)
[![bijux-proteomics-knowledge](https://img.shields.io/pypi/v/bijux-proteomics-knowledge?label=knowledge&logo=pypi)](https://pypi.org/project/bijux-proteomics-knowledge/)
[![bijux-proteomics-lab](https://img.shields.io/pypi/v/bijux-proteomics-lab?label=lab&logo=pypi)](https://pypi.org/project/bijux-proteomics-lab/)

[![proteomics-core](https://img.shields.io/badge/proteomics--core-ghcr-181717?logo=github)](https://github.com/bijux/bijux-proteomics/pkgs/container/bijux-proteomics%2Fproteomics-core)
[![agentic-proteins](https://img.shields.io/badge/agentic--proteins-ghcr-181717?logo=github)](https://github.com/bijux/bijux-proteomics/pkgs/container/bijux-proteomics%2Fagentic-proteins)
[![bijux-proteomics-foundation](https://img.shields.io/badge/foundation-ghcr-181717?logo=github)](https://github.com/bijux/bijux-proteomics/pkgs/container/bijux-proteomics%2Fbijux-proteomics-foundation)
[![bijux-proteomics-core](https://img.shields.io/badge/core-ghcr-181717?logo=github)](https://github.com/bijux/bijux-proteomics/pkgs/container/bijux-proteomics%2Fbijux-proteomics-core)
[![bijux-proteomics-runtime](https://img.shields.io/badge/runtime-ghcr-181717?logo=github)](https://github.com/bijux/bijux-proteomics/pkgs/container/bijux-proteomics%2Fbijux-proteomics-runtime)
[![bijux-proteomics-intelligence](https://img.shields.io/badge/intelligence-ghcr-181717?logo=github)](https://github.com/bijux/bijux-proteomics/pkgs/container/bijux-proteomics%2Fbijux-proteomics-intelligence)
[![bijux-proteomics-knowledge](https://img.shields.io/badge/knowledge-ghcr-181717?logo=github)](https://github.com/bijux/bijux-proteomics/pkgs/container/bijux-proteomics%2Fbijux-proteomics-knowledge)
[![bijux-proteomics-lab](https://img.shields.io/badge/lab-ghcr-181717?logo=github)](https://github.com/bijux/bijux-proteomics/pkgs/container/bijux-proteomics%2Fbijux-proteomics-lab)

[![proteomics-core docs](https://img.shields.io/badge/docs-proteomics--core-2563EB?logo=materialformkdocs&logoColor=white)](https://bijux.io/bijux-proteomics/04-bijux-proteomics-core/)
[![agentic-proteins docs](https://img.shields.io/badge/docs-agentic--proteins-2563EB?logo=materialformkdocs&logoColor=white)](https://bijux.io/bijux-proteomics/02-agentic-proteins/)
[![bijux-proteomics-foundation docs](https://img.shields.io/badge/docs-foundation-2563EB?logo=materialformkdocs&logoColor=white)](https://bijux.io/bijux-proteomics/03-bijux-proteomics-foundation/)
[![bijux-proteomics-core docs](https://img.shields.io/badge/docs-core-2563EB?logo=materialformkdocs&logoColor=white)](https://bijux.io/bijux-proteomics/04-bijux-proteomics-core/)
[![bijux-proteomics-runtime docs](https://img.shields.io/badge/docs-runtime-2563EB?logo=materialformkdocs&logoColor=white)](https://bijux.io/bijux-proteomics/09-bijux-proteomics-runtime/)
[![bijux-proteomics-intelligence docs](https://img.shields.io/badge/docs-intelligence-2563EB?logo=materialformkdocs&logoColor=white)](https://bijux.io/bijux-proteomics/05-bijux-proteomics-intelligence/)
[![bijux-proteomics-knowledge docs](https://img.shields.io/badge/docs-knowledge-2563EB?logo=materialformkdocs&logoColor=white)](https://bijux.io/bijux-proteomics/06-bijux-proteomics-knowledge/)
[![bijux-proteomics-lab docs](https://img.shields.io/badge/docs-lab-2563EB?logo=materialformkdocs&logoColor=white)](https://bijux.io/bijux-proteomics/07-bijux-proteomics-lab/)
<!-- bijux-proteomics-badges:generated:end -->

`proteomics-core` is the compatibility alias for the canonical core owner
`bijux-proteomics-core`.
It is the install and import alias for bijux-proteomics-core.

Use this package when you want a shorter distribution and import name while
keeping the same scientific processing owner and behavior.

## Installation

```bash
pip install proteomics-core
```

## Public APIs

The alias forwards core scientific imports through `proteomics_core`:

```python
from proteomics_core import parse_fasta_document

report = parse_fasta_document(">sp|P11111|PTM1 Protein 1\nMPEPTIDEK\n")

assert report.total_records == 1
assert len(report.accepted_records) == 1
assert report.accepted_records[0].canonical_accession == "P11111"
```

## Package identity

- Distribution name: `proteomics-core`
- Import root: `proteomics_core`
- Canonical owner package: `bijux-proteomics-core`
- Canonical owner import root: `bijux_proteomics`

## Package boundaries

- this package owns compatibility naming for the core package surface
- all scientific semantics remain owned by `bijux-proteomics-core`
- new exports must appear in the canonical owner before they appear here

## What this package must not do

- invent independent core behavior or documentation claims
- fork canonical scientific or workflow semantics
- become a second release-policy owner for the core surface

## Contract checkpoints

- forwarded imports must keep canonical behavior without semantic drift
- docs must keep the canonical owner explicit
- alias compatibility tests must stay green when exports or packaging change

## Choose this package when

- you need a shorter core-specific distribution name than the canonical owner
- migration constraints prefer `proteomics_core` imports
- packaging or compatibility work needs a named alias for the core owner

## Route elsewhere when

- the change alters scientific parsing, review, or workflow behavior
- the work introduces exports that are not already owned by core
- the package would stop being a forwarding alias

## Verification route

- run alias compatibility tests before changing imports or packaging metadata
- review `docs/ARCHITECTURE.md`, `docs/BOUNDARIES.md`, and `docs/CONTRACTS.md`
  when alias claims or boundaries shift
- validate the canonical core README and tests when behavior changes are being
  proposed

## Review questions

- does the change preserve this package as a compatibility alias only
- is the canonical owner still named clearly for maintainers and consumers
- would the same behavior remain correct if consumers imported core directly

## Escalation route

- route scientific behavior changes to `bijux-proteomics-core`
- stop and review boundaries when the alias starts gaining package-local logic
- escalate before release when package metadata or import routing could confuse
  core ownership

## Consumer impact signals

- import-path or package-name changes are high-impact because downstream code
  may import this alias directly
- alias contract wording changes should still be reviewed against canonical core
- documentation-only clarifications carry lower release risk than routing or
  metadata changes

## Explicit non-goals

- this package does not own assay-processing or workflow semantics
- this package does not define runtime, intelligence, knowledge, or lab policy
- this package does not replace the canonical core release surface

## Documentation

- Release guidance lives in this `README.md`, this package `CHANGELOG.md`, and
  package `docs/*.md` under the canonical core owner surface.
- [Product architecture](https://bijux.io/bijux-proteomics/01-bijux-proteomics/foundation/product-architecture/)
- [Cross-package ownership](https://bijux.io/bijux-proteomics/01-bijux-proteomics/foundation/cross-package-ownership/)
- [Canonical core package docs](https://bijux.io/bijux-proteomics/04-bijux-proteomics-core/)
- [Changelog](CHANGELOG.md)
