# PyPI Maintainer Notes

- package: `bijux-proteomics-core`
- owner: Bijan Mousavi (`bijan@bijux.io`)
- repository: `bijux/bijux-proteomics`

Release checklist:

1. Validate `README.md` and package docs describe current domain ownership.
2. Confirm compatibility-sensitive model changes are reflected in tests.
3. Run `make lint test quality security` from repository root.
4. Build and verify package metadata before publishing.
