# proteomics-core

`proteomics-core` is the install and import alias for bijux-proteomics-core.

Use this package when you want the canonical core distribution under a shorter
package name while keeping the same scientific processing owner.

## Installation

```bash
pip install proteomics-core
```

## Quick Start

```python
from proteomics_core import parse_fasta_document
```

## Route To Canonical Docs

- [Product architecture](https://bijux.io/bijux-proteomics/01-bijux-proteomics/foundation/product-architecture/)
- [Cross-package ownership](https://bijux.io/bijux-proteomics/01-bijux-proteomics/foundation/cross-package-ownership/)
- [Core package handbook](https://bijux.io/bijux-proteomics/04-bijux-proteomics-core/)

## Boundary

This package is a naming alias only. It does not own an independent
assay-processing surface, evidence model, runtime layer, or lab layer.

## Changelog

- [Changelog](CHANGELOG.md)
