# PyPI Maintainer Notes

- package: `agentic-proteins`
- owner: Bijan Mousavi (`bijan@bijux.io`)
- repository: `bijux/bijux-proteomics`

Release checklist:

1. Verify `README.md` and package docs reflect current runtime ownership.
2. Confirm `CHANGELOG.md` includes release-relevant behavior changes.
3. Run `make lint test quality security` from repository root.
4. Verify `.github/workflows/publish-agentic-proteins.yml` is configured for tag-triggered publish (`v*`) with trusted publishing permissions.
5. Create and push the release tag (`vX.Y.Z`) after changelog and metadata are final.
6. Confirm the publish workflow uploaded and released both wheel and sdist artifacts.
