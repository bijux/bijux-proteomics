---
title: makes
audience: mixed
type: index
status: canonical
owner: bijux-proteomics-dev-docs
last_reviewed: 2026-04-26
---

# makes

Open this section to understand the shared command surface that ties local work,
CI validation, package dispatch, and release-oriented automation together.

The make layer is a real repository interface. These pages exist so a
maintainer can trace a command from `Makefile` to the fragment that owns it
without having to reverse-engineer the whole tree from includes alone.

```mermaid
flowchart LR
    root["root entrypoints"]
    env["environment model"]
    dispatch["package dispatch"]
    ci["CI targets"]
    release["release surfaces"]
    reader["reader question<br/>which make surface should I change?"]
    classDef page fill:var(--bijux-mermaid-page-fill),stroke:var(--bijux-mermaid-page-stroke),color:var(--bijux-mermaid-page-text),stroke-width:2px;
    classDef positive fill:var(--bijux-mermaid-positive-fill),stroke:var(--bijux-mermaid-positive-stroke),color:var(--bijux-mermaid-positive-text);
    classDef anchor fill:var(--bijux-mermaid-anchor-fill),stroke:var(--bijux-mermaid-anchor-stroke),color:var(--bijux-mermaid-anchor-text);
    class root,page reader;
    class env,dispatch,ci,release positive;
    root --> reader
    env --> reader
    dispatch --> reader
    ci --> reader
    release --> reader
```

## Pages In This Section

- [Make System Overview](https://bijux.io/bijux-proteomics/08-bijux-proteomics-maintain/makes/make-system-overview/)
- [Root Entrypoints](https://bijux.io/bijux-proteomics/08-bijux-proteomics-maintain/makes/root-entrypoints/)
- [Environment Model](https://bijux.io/bijux-proteomics/08-bijux-proteomics-maintain/makes/environment-model/)
- [Repository Layout](https://bijux.io/bijux-proteomics/08-bijux-proteomics-maintain/makes/repository-layout/)
- [Package Dispatch](https://bijux.io/bijux-proteomics/08-bijux-proteomics-maintain/makes/package-dispatch/)
- [CI Targets](https://bijux.io/bijux-proteomics/08-bijux-proteomics-maintain/makes/ci-targets/)
- [Package Contracts](https://bijux.io/bijux-proteomics/08-bijux-proteomics-maintain/makes/package-contracts/)
- [Release Surfaces](https://bijux.io/bijux-proteomics/08-bijux-proteomics-maintain/makes/release-surfaces/)
- [Authoring Rules](https://bijux.io/bijux-proteomics/08-bijux-proteomics-maintain/makes/authoring-rules/)

## Open This Section When

- the concern is about shared Make entrypoints rather than package code itself
- you need to understand how local commands, CI targets, and release commands
  are routed
- you are editing the repository command surface that maintainers and
  automation both depend on

## Open Another Section When

- the question is about GitHub Actions triggers rather than Make routing
- the issue belongs to one product package contract instead of a shared command
  layer
- you only need one concrete package page and already know which page owns it

## Choose A Page

- open [Make System Overview](https://bijux.io/bijux-proteomics/08-bijux-proteomics-maintain/makes/make-system-overview/) for the broad structure
  first
- open [Root Entrypoints](https://bijux.io/bijux-proteomics/08-bijux-proteomics-maintain/makes/root-entrypoints/) when the concern starts at the
  top-level command surface
- open [Package Dispatch](https://bijux.io/bijux-proteomics/08-bijux-proteomics-maintain/makes/package-dispatch/) when the question is how shared
  targets route into one package or many
- open [CI Targets](https://bijux.io/bijux-proteomics/08-bijux-proteomics-maintain/makes/ci-targets/) or [Release Surfaces](https://bijux.io/bijux-proteomics/08-bijux-proteomics-maintain/makes/release-surfaces/)
  when the concern is automation-facing rather than developer-facing

## Bottom Line

This section lets a maintainer trace a command name to the owning make surface
quickly. It prevents the make layer from feeling like a flat bag of targets
with hidden routing rules.

