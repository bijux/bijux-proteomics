# PyPI Maintainer Notes

- package: `bijux-proteomics-intelligence`
- owner: Bijan Mousavi (`bijan@bijux.io`)
- repository: `bijux/bijux-proteomics`

Release checklist:

1. Verify README and package docs describe current ranking/scenario behavior.
2. Confirm behavioral deltas are covered by scenario and ranking tests.
3. Run `make lint test quality security` from repository root.
4. Build and verify package metadata before publishing.
