# PyPI Maintainer Notes

- package: `bijux-proteomics-core`
- owner: Bijan Mousavi (`bijan@bijux.io`)
- repository: `bijux/bijux-proteomics`

Release checklist:

1. Validate `README.md` and package docs describe current domain ownership.
2. Confirm compatibility-sensitive model changes are reflected in tests.
3. Run `make lint test quality security` from repository root.
4. Verify `.github/workflows/publish-bijux-proteomics-core.yml` is configured for tag-triggered publish (`v*`) with trusted publishing permissions.
5. Create and push the release tag (`vX.Y.Z`) after changelog and metadata are final.
6. Confirm the publish workflow uploaded and released both wheel and sdist artifacts.
