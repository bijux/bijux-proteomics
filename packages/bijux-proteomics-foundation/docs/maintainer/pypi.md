# PyPI Maintainer Notes

- package: `bijux-proteomics-foundation`
- owner: Bijan Mousavi (`bijan@bijux.io`)
- repository: `bijux/bijux-proteomics`

Release checklist:

1. Confirm `README.md` reflects current package ownership and boundaries.
2. Verify package version in `pyproject.toml` is intentionally set.
3. Run `make lint test quality security` from repository root.
4. Verify `.github/workflows/publish-bijux-proteomics-foundation.yml` is configured for tag-triggered publish (`v*`) with trusted publishing permissions.
5. Create and push the release tag (`vX.Y.Z`) after changelog and metadata are final.
6. Confirm the publish workflow uploaded and released both wheel and sdist artifacts.
