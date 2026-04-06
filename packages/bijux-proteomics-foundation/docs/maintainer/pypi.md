# PyPI Maintainer Notes

- package: `bijux-proteomics-foundation`
- owner: Bijan Mousavi (`bijan@bijux.io`)
- repository: `bijux/bijux-proteomics`

Release checklist:

1. Confirm `README.md` reflects current package ownership and boundaries.
2. Verify package version in `pyproject.toml` is intentionally set.
3. Run `make lint test quality security` from repository root.
4. Build package artifacts and confirm metadata fields are complete.
