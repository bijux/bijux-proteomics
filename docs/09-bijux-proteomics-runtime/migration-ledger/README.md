---
title: Migration Ledger
audience: maintainer
type: guide
status: canonical
owner: bijux-proteomics-runtime
last_reviewed: 2026-04-26
---

# agentic-proteins Migration Ledger

This ledger is the review record for moving legacy `agentic-proteins` modules
into the canonical proteomics package family. It exists so migration decisions
can be inspected from checked-in documentation rather than inferred from
one-off pull requests.

Each module is classified once, assigned to a target owner, and given a reason
that explains why that ownership is technically defensible.

```mermaid
flowchart LR
    legacy["legacy module path"]
    rules["classification rules<br/>rules.toml"]
    bucket["ownership bucket"]
    owner["target owner package"]
    summary["checked-in ledger and summary"]
    pr["migration pull request"]
    classDef page fill:var(--bijux-mermaid-page-fill),stroke:var(--bijux-mermaid-page-stroke),color:var(--bijux-mermaid-page-text),stroke-width:2px;
    classDef positive fill:var(--bijux-mermaid-positive-fill),stroke:var(--bijux-mermaid-positive-stroke),color:var(--bijux-mermaid-positive-text);
    classDef caution fill:var(--bijux-mermaid-caution-fill),stroke:var(--bijux-mermaid-caution-stroke),color:var(--bijux-mermaid-caution-text);
    classDef action fill:var(--bijux-mermaid-action-fill),stroke:var(--bijux-mermaid-action-stroke),color:var(--bijux-mermaid-action-text);
    class legacy,page rules;
    class bucket caution;
    class owner,summary positive;
    class pr action;
    legacy --> rules --> bucket --> owner --> summary --> pr
```

## How To Read The Buckets

- `runtime_execution_ownership`: the module is part of the canonical runtime
  surface and should live in `bijux-proteomics-runtime`
- `runtime_support_internal_review`: the module looks runtime-adjacent, but it
  still needs semantic review before final placement is locked
- `domain_ownership`: the module expresses lower-layer domain meaning and should
  move out of runtime ownership

These buckets are deliberately strict. They separate clear runtime control
surfaces from mixed or domain-heavy modules so migration does not quietly
collapse package boundaries.

## Required Fields

- `module_path`: the source module under legacy `agentic-proteins`
- `bucket`: the migration status and ownership confidence level
- `owner_package`: the canonical target package
- `reason`: the justification a reviewer should be able to defend in a pull
  request

## Sources Of Truth

- rules: `configs/runtime-boundaries/migration-ledger/rules.toml`
- generated ledger:
  `docs/09-bijux-proteomics-runtime/migration-ledger/agentic-proteins-module-ledger.csv`
- generated summary:
  `docs/09-bijux-proteomics-runtime/migration-ledger/agentic-proteins-module-ledger-summary.md`

## Regeneration And Validation

- `make quality-runtime-migration-ledger` validates freshness and coverage
- `PYTHONPATH=packages/bijux-proteomics-dev/src python3 -m bijux_proteomics_dev.quality.architecture.runtime_migration_ledger`
  regenerates the checked-in outputs

## Review Expectations

When ownership changes, keep the rule, the generated outputs, and the written
rationale in the same pull request.

1. Update `configs/runtime-boundaries/migration-ledger/rules.toml`.
2. Regenerate the ledger outputs.
3. Run `make quality-runtime-migration-ledger`.
4. Explain the ownership change in the pull request so readers do not have to
   reconstruct the reasoning from diffs alone.
