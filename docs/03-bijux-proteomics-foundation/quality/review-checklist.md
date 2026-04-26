---
title: Review Checklist
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-foundation-docs
last_reviewed: 2026-04-26
---

# Review Checklist

Reviewing changes in `bijux-proteomics-foundation` should include both behavior and documentation.

The checklist is not here to slow people down with ceremony. It is here to stop
fast review from becoming shallow review when a change touches boundaries,
contracts, or proof.

This page shows how `bijux-proteomics-foundation` earns trust and where skepticism still belongs.

## Checklist

- did ownership stay inside the correct package boundary
- do interface or artifact changes have matching docs and tests
- are filenames, commit messages, and symbols still clear enough to age well

## Concrete Anchors

- tests/unit for api, contracts, core, interfaces, model, and runtime
- tests/e2e for governed flow behavior
- README.md

## Open This Page When

- you are reviewing tests, invariants, limitations, or ongoing risks
- you need evidence that the documented contract is actually defended
- you are deciding whether a change is truly done rather than merely implemented

## Decision Rule

Use `Review Checklist` to decide whether `bijux-proteomics-foundation` has actually earned trust after a change. If one narrow green check hides a wider contract, risk, or validation gap, the work is not done yet.

## What You Can Resolve Here

- what currently proves the `bijux-proteomics-foundation` contract instead of merely describing it
- which risks, limits, and assumptions still need explicit skepticism
- what a reviewer should be able to say before accepting a change as done

## Review Focus

- compare the documented proof story with the actual test layout and release posture
- look for limitations or risks that should have moved with recent behavior changes
- verify that the claimed done-ness standard still reflects real validation practice

## Limits

Tests, checks, and review practice remain the proof for this package. If they drift, this page is wrong.

## Read Next

- open foundation when the risk appears to be boundary confusion rather than missing tests
- open architecture when the proof gap points to structural drift
- open interfaces or operations when the proof question is really about a contract or workflow

