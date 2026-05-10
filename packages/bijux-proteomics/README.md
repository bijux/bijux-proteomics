# bijux-proteomics

`bijux-proteomics` is the install and command alias for bijux-proteomics-core.

Use this distribution when you want the canonical core package under the
top-level `bijux-proteomics` name on PyPI without creating a second scientific
owner surface.

## Installation

```bash
pip install bijux-proteomics
```

This alias installs the canonical core distribution:
`bijux-proteomics-core`.

The stable Python import root remains `bijux_proteomics`, and the flagship core
CLI command remains `bijux-proteomics`.

## Route To Canonical Docs

- [Product architecture](https://bijux.io/bijux-proteomics/01-bijux-proteomics/foundation/product-architecture/)
- [Cross-package ownership](https://bijux.io/bijux-proteomics/01-bijux-proteomics/foundation/cross-package-ownership/)
- [Core package handbook](https://bijux.io/bijux-proteomics/04-bijux-proteomics-core/)

## Boundary

This package exists to reserve the matching distribution name and install the
canonical core command surface. It does not own assay-processing logic,
runtime orchestration, recommendation policy, or lab planning.

## Changelog

- [Changelog](CHANGELOG.md)
