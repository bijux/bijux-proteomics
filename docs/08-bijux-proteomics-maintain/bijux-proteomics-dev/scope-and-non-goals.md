---
title: Scope and Non-Goals
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-dev-docs
last_reviewed: 2026-04-10
---

# Scope and Non-Goals

The maintainer package is for repository health, not product behavior.

That distinction protects the architecture. When maintainer automation starts
absorbing runtime rules or scientific semantics, the repository loses the clear
ownership lines that make the package family understandable.

## In Scope

- docs, schema, release, and dependency-policy enforcement
- maintainer-only tooling used by root automation and CI
- repository checks that span more than one package or shared artifact family

## Out Of Scope

- runtime behavior that belongs in `agentic-proteins`
- domain contracts that belong in `bijux-proteomics-*` product packages
- quiet shortcuts that override package-owned rules from the root

## Purpose

This page keeps the maintainer package from becoming an unbounded dumping
ground.

## Stability

Update it only when repository authority genuinely moves into or out of
`bijux-proteomics-dev`.
