# PyPI Maintainer Notes

- package: `bijux-proteomics-knowledge`
- owner: Bijan Mousavi (`bijan@bijux.io`)
- repository: `bijux/bijux-proteomics`

Release checklist:

1. Confirm docs and README describe current evidence and conflict semantics.
2. Verify conflict-resolution and graph-validation tests pass.
3. Run `make lint test quality security` from repository root.
4. Build and verify package metadata before publishing.
