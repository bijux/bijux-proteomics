---
title: deploy-docs
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-dev-docs
last_reviewed: 2026-04-10
---

# deploy-docs

`deploy-docs.yml` is the workflow that turns the checked-in handbook into the
published site.

Documentation in this repository is treated as a maintained surface, not an
optional by-product. The deploy workflow is therefore part of the
documentation contract rather than a convenience step.

It runs on `main` when docs-related files change and can also be started
manually. The job tree stays small on purpose: build the strict site, validate
the published assets, then deploy the Pages artifact.

The asset validation step checks both the generated homepage and the checked-in
browser icon files under `docs/assets/site-icons/` after they are copied into
the built site output.

## Workflow Anchors

- `.github/workflows/deploy-docs.yml`
- `mkdocs.yml` and `mkdocs.shared.yml`
- `docs/` as the published source tree

