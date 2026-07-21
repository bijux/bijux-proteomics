---
title: Compatibility CLI
audience: mixed
type: reference
status: canonical
owner: agentic-proteins-docs
last_reviewed: 2026-07-21
---

# Compatibility CLI

The `agentic-proteins` executable preserves the command-line contract that
predates `bijux-proteomics-runtime`. It is not a separate implementation: the
entrypoint exports the canonical runtime `click` command object directly.
Command names, arguments, output envelopes, exit behavior, and runtime
artifacts therefore come from the runtime package.

The compatibility rule is direct: new workflow use should start from `bijux-proteomics-runtime --help`.
Keep `agentic-proteins` only where an existing consumer cannot yet change its
executable name.

```bash
# Preserved invocation
agentic-proteins run --sequence MKTIIALSYIFCLVFADYKDDDDK --dry-run --json

# Canonical invocation with the same command semantics
bijux-proteomics-runtime run \
  --sequence MKTIIALSYIFCLVFADYKDDDDK \
  --dry-run \
  --json
```

## Forwarded commands

The compatibility executable exposes the complete runtime command tree:

| Command | Operator intent |
| --- | --- |
| `identity` | Print the canonical runtime identity and version context. |
| `run` | Validate a sequence, configure providers, and create a run. |
| `resume` | Continue work from a stored candidate. |
| `import-result` | Register output produced by an external engine. |
| `compare` | Compare two persisted runs. |
| `inspect-candidate` | Inspect a candidate without starting execution. |
| `export-report` | Render the report associated with a run. |
| `reproduce` | Re-execute from a recorded run configuration. |
| `api ...` | Serve or query runtime status, artifacts, evidence, history, and review packets. |

`run` accepts either `--sequence` or `--fasta`, never both. Real structure
providers are opt-in, while `--dry-run` performs planning and validation
without executing tools. Use `--json` for machine consumers; command failures
then use the runtime error envelope instead of free-form terminal output.

## Compatibility guarantee

The package tests assert that the compatibility and runtime CLI objects are
identical and that their help text is byte-for-byte equivalent. The HTTP app
factory is forwarded under the same rule. A difference between the two names
is a compatibility defect, not an alternative behavior to document.

## Migration verification

Test the historical and Runtime executables with the same input fixture and
resolved environment. Compare more than successful completion:

| Observable | Required parity |
| --- | --- |
| command discovery | command tree, option names, defaults, required arguments |
| machine output | JSON schema, field meaning, ordering guarantees, error envelope |
| terminal behavior | exit status, stdout/stderr ownership, refusal explanation |
| execution custody | provider decision, run identity, artifact paths and digests |
| recovery | persisted candidate, resume boundary, comparison and replay behavior |

After parity is established, change the executable name in the caller and keep
the resulting Runtime run bundle as migration evidence. A help-text match alone
does not establish state, artifact, or replay equivalence.

The full option-level reference lives in the
[runtime CLI reference](../../09-bijux-proteomics-runtime/cli-reference.md).
