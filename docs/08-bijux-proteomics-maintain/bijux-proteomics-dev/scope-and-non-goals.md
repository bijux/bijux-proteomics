---
title: Scope and Non-Goals
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-dev-docs
last_reviewed: 2026-04-26
---

# Scope and Non-Goals

This package owns repository-health enforcement. It should stay narrow enough that product behavior still belongs to product packages.

## In Scope

- repository-wide docs, contract, release, security, and quality enforcement
- helper code that backs Make targets and workflow rules
- tooling that keeps checked-in policy easier to audit

## Out Of Scope

- runtime or product-package feature behavior
- user-facing domain semantics
- automation whose best home is a product package itself

## First Proof Check

- `src/bijux_proteomics_dev/`
- maintainer tests and workflow call sites

