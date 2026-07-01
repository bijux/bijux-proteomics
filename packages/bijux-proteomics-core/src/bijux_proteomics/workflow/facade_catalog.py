# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Catalog helpers for governed workflow facade owner ledgers."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class WorkflowFacadeOwner:
    """One owned module that contributes public symbols to a workflow facade."""

    owner_module: str
    rationale: str
    excluded_exports: tuple[str, ...] = ()


def copy_facade_owners(
    owners: tuple[WorkflowFacadeOwner, ...],
    *,
    excluded_exports: tuple[str, ...] = (),
) -> tuple[WorkflowFacadeOwner, ...]:
    """Copy facade owners while preserving order and extending exclusions."""

    return tuple(
        WorkflowFacadeOwner(
            owner_module=owner.owner_module,
            rationale=owner.rationale,
            excluded_exports=(*owner.excluded_exports, *excluded_exports),
        )
        for owner in owners
    )


def facade_owner_modules(
    owners: tuple[WorkflowFacadeOwner, ...],
) -> frozenset[str]:
    """Return the canonical owner modules represented by a facade catalog."""

    return frozenset(owner.owner_module for owner in owners)


def select_facade_owners(
    owners: tuple[WorkflowFacadeOwner, ...],
    owner_modules: set[str] | frozenset[str],
    *,
    excluded_exports: tuple[str, ...] = (),
) -> tuple[WorkflowFacadeOwner, ...]:
    """Copy only the owners whose modules belong to the selected compatibility set."""

    return tuple(
        WorkflowFacadeOwner(
            owner_module=owner.owner_module,
            rationale=owner.rationale,
            excluded_exports=(*owner.excluded_exports, *excluded_exports),
        )
        for owner in owners
        if owner.owner_module in owner_modules
    )


__all__ = [
    "WorkflowFacadeOwner",
    "copy_facade_owners",
    "facade_owner_modules",
    "select_facade_owners",
]
