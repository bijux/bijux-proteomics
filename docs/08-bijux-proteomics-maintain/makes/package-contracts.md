---
title: Package Contracts
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-dev-docs
last_reviewed: 2026-04-10
---

# Package Contracts

Shared package behavior should be defined once and reused honestly.

Files such as `makes/bijux-py/package.mk`, `makes/bijux-py/api.mk`,
`makes/bijux-py/api-contract.mk`, `makes/bijux-py/api-freeze.mk`, and
`makes/bijux-py/api-live-contract.mk` describe reusable contracts that
package-specific files then bind to the proteomics packages.

## Contract Rule

When package behavior is shared, encode it in a reusable fragment instead of
copying target logic across many package files.

## Purpose

This page explains where package-level make contracts are defined and reused.

## Stability

Keep it aligned with the shared package contract fragments that currently
exist.
