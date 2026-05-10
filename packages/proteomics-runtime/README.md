# proteomics-runtime

`proteomics-runtime` is the install and import alias for
bijux-proteomics-runtime.

Use this package when you want the canonical runtime package under a shorter
distribution and import name while keeping the same execution owner.

## Installation

```bash
pip install proteomics-runtime
```

## Quick Start

```python
from proteomics_runtime import AppConfig, RunManager, create_app
```

```bash
proteomics-runtime --help
```

## Route To Canonical Docs

- [Product architecture](https://bijux.io/bijux-proteomics/01-bijux-proteomics/foundation/product-architecture/)
- [Cross-package ownership](https://bijux.io/bijux-proteomics/01-bijux-proteomics/foundation/cross-package-ownership/)
- [Runtime package handbook](https://bijux.io/bijux-proteomics/09-bijux-proteomics-runtime/)

## Boundary

This package is a naming alias only. It does not define a second execution
owner or a second runtime migration target.

## Changelog

- [Changelog](CHANGELOG.md)
