---
title: Review Checklist
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-foundation-docs
last_reviewed: 2026-07-21
---

# Review Checklist

Review Foundation changes as repository-wide contract changes. A passing unit
test in Foundation is insufficient when every downstream package may persist,
hash, migrate, or interpret the affected value.

## Ownership

- Identify at least two real consumers of a proposed shared primitive.
- Confirm the meaning is identical across consumers and contains no downstream
  policy.
- Reject reverse imports and optional behavior that requires a product package.
- Prefer the existing owner when the change is scientific, operational,
  evidential, decisional, or laboratory-facing.

## Representation And Semantics

- Compare validation, defaults, optionality, enumeration values, units, and
  failure behavior.
- Inspect canonical JSON and stable-value ordering.
- Recompute hashes only through the governed policy; never patch a digest.
- Distinguish document ID, content hash, revision, and schema version.
- Verify refusals and errors remain typed rather than collapsing to null values.

## Compatibility

| Change | Evidence |
| --- | --- |
| identifier or prefix | construction, classification, invalid form, downstream fixtures |
| model field or default | old/new validation, serialization, schema, consumer behavior |
| canonicalization or hashing | golden bytes and digests across supported values |
| document metadata | round trip, revision, lineage, producer, old reader behavior |
| migration | complete path, missing path, cycle, deprecated target, wrong output version |
| public import | root API ledger, wheel contents, downstream import inventory |
| exception or outcome | caller handling and preserved failure distinction |

## Required Verification

Run focused Foundation tests, serialization and compatibility suites, public
API and package-shape checks, then affected downstream tests and documentation
gates. Inspect built-wheel imports when the public surface changes. Retain old
fixtures when persisted data is involved.

## Approval Boundary

Approve only when the owner is correct, current consumers agree on meaning,
generated artifacts match source, migrations or explicit rejection cover old
data, and downstream evidence is green or the blocker is recorded. Do not
weaken a compatibility check to accept an undocumented semantic change.
