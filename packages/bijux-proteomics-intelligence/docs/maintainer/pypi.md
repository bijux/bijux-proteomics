# PyPI Maintainer Notes

- package: `bijux-proteomics-intelligence`
- owner: Bijan Mousavi (`bijan@bijux.io`)
- repository: `bijux/bijux-proteomics`

Release checklist:

1. Verify README and package docs describe current ranking/scenario behavior.
2. Confirm behavioral deltas are covered by scenario and ranking tests.
3. Run `make lint test quality security` from repository root.
4. Verify `.github/workflows/publish-bijux-proteomics-intelligence.yml` is configured for tag-triggered publish (`v*`) with trusted publishing permissions.
5. Create and push the release tag (`vX.Y.Z`) after changelog and metadata are final.
6. Confirm the publish workflow uploaded and released both wheel and sdist artifacts.
