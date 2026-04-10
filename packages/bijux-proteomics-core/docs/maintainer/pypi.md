# PyPI Maintainer Notes

## Release Surface

[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-3776AB?logo=python&logoColor=white)](https://pypi.org/project/bijux-proteomics-core/)
[![License: Apache-2.0](https://img.shields.io/badge/license-Apache--2.0-0F766E)](https://github.com/bijux/bijux-proteomics/blob/main/LICENSE)
[![Verify](https://github.com/bijux/bijux-proteomics/actions/workflows/verify.yml/badge.svg)](https://github.com/bijux/bijux-proteomics/actions/workflows/verify.yml)
[![Publish](https://github.com/bijux/bijux-proteomics/actions/workflows/publish.yml/badge.svg)](https://github.com/bijux/bijux-proteomics/actions/workflows/publish.yml)
[![Docs](https://github.com/bijux/bijux-proteomics/actions/workflows/deploy-docs.yml/badge.svg)](https://github.com/bijux/bijux-proteomics/actions/workflows/deploy-docs.yml)

- package guide: <https://bijux.io/bijux-proteomics/bijux-proteomics-core/>
- release and versioning: <https://bijux.io/bijux-proteomics/bijux-proteomics-core/operations/release-and-versioning/>
- package directory: <https://github.com/bijux/bijux-proteomics/tree/main/packages/bijux-proteomics-core>
- verify workflow: <https://github.com/bijux/bijux-proteomics/actions/workflows/verify.yml>
- publish workflow: <https://github.com/bijux/bijux-proteomics/actions/workflows/publish.yml>
- docs workflow: <https://github.com/bijux/bijux-proteomics/actions/workflows/deploy-docs.yml>

- package: `bijux-proteomics-core`
- owner: Bijan Mousavi (`bijan@bijux.io`)
- repository: `bijux/bijux-proteomics`

Release checklist:

1. Validate `README.md` and package docs describe current domain ownership.
2. Confirm compatibility-sensitive model changes are reflected in tests.
3. Run `make lint test quality security` from repository root.
4. Verify `.github/workflows/publish.yml` is configured for tag-triggered publish (`v*`) with PyPI trusted publishing.
5. Create and push the release tag (`vX.Y.Z`) after changelog and metadata are final.
6. Confirm the publish workflow uploaded and released both wheel and sdist artifacts.
