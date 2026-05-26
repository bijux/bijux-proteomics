# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Private test-support helpers for source-tree cyclomatic complexity ceilings."""

from __future__ import annotations

import ast
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class SourceFunctionComplexityException:
    """One temporary cyclomatic complexity exception for a function or method."""

    relative_path: str
    qualified_name: str
    allowed_complexity: int
    temporary_reason: str


@dataclass(frozen=True)
class SourceFunctionComplexityObservation:
    """Observed cyclomatic complexity state for one function or method."""

    relative_path: str
    qualified_name: str
    complexity: int
    allowed_complexity: int | None
    temporary_reason: str | None


@dataclass(frozen=True)
class SourceTreeComplexityReport:
    """Structured report over one source tree cyclomatic complexity scan."""

    source_root: Path
    ceiling: int
    scanned_function_count: int
    approved_over_ceiling: tuple[SourceFunctionComplexityObservation, ...]
    unexpected_over_ceiling: tuple[SourceFunctionComplexityObservation, ...]
    stale_exceptions: tuple[SourceFunctionComplexityException, ...]


def build_source_tree_complexity_report(
    source_root: Path,
    *,
    ceiling: int,
    exceptions: tuple[SourceFunctionComplexityException, ...] = (),
) -> SourceTreeComplexityReport:
    """Scan one source tree and classify functions above the shared complexity ceiling."""

    exception_by_key = {
        (entry.relative_path, entry.qualified_name): entry for entry in exceptions
    }
    approved_over_ceiling: list[SourceFunctionComplexityObservation] = []
    unexpected_over_ceiling: list[SourceFunctionComplexityObservation] = []
    observed_complexities: dict[tuple[str, str], int] = {}

    for path in sorted(source_root.rglob("*.py")):
        relative_path = path.relative_to(source_root).as_posix()
        module = ast.parse(path.read_text(), filename=str(path))
        for function in _collect_function_complexities(module):
            key = (relative_path, function.qualified_name)
            observed_complexities[key] = function.complexity
            if function.complexity <= ceiling:
                continue
            exception = exception_by_key.get(key)
            observation = SourceFunctionComplexityObservation(
                relative_path=relative_path,
                qualified_name=function.qualified_name,
                complexity=function.complexity,
                allowed_complexity=(
                    None if exception is None else exception.allowed_complexity
                ),
                temporary_reason=(
                    None if exception is None else exception.temporary_reason
                ),
            )
            if exception is None or function.complexity > exception.allowed_complexity:
                unexpected_over_ceiling.append(observation)
            else:
                approved_over_ceiling.append(observation)

    stale_exceptions = tuple(
        entry
        for entry in exceptions
        if observed_complexities.get((entry.relative_path, entry.qualified_name), 0)
        <= ceiling
    )

    return SourceTreeComplexityReport(
        source_root=source_root,
        ceiling=ceiling,
        scanned_function_count=len(observed_complexities),
        approved_over_ceiling=tuple(approved_over_ceiling),
        unexpected_over_ceiling=tuple(unexpected_over_ceiling),
        stale_exceptions=stale_exceptions,
    )


@dataclass(frozen=True)
class _FunctionComplexity:
    qualified_name: str
    complexity: int


class _ComplexityCounter(ast.NodeVisitor):
    def __init__(self) -> None:
        self.complexity = 1

    def visit_If(self, node: ast.If) -> None:
        self.complexity += 1
        self.generic_visit(node)

    def visit_IfExp(self, node: ast.IfExp) -> None:
        self.complexity += 1
        self.generic_visit(node)

    def visit_For(self, node: ast.For) -> None:
        self.complexity += 1
        self.generic_visit(node)

    def visit_AsyncFor(self, node: ast.AsyncFor) -> None:
        self.complexity += 1
        self.generic_visit(node)

    def visit_While(self, node: ast.While) -> None:
        self.complexity += 1
        self.generic_visit(node)

    def visit_Try(self, node: ast.Try) -> None:
        self.complexity += len(node.handlers)
        if node.orelse:
            self.complexity += 1
        if node.finalbody:
            self.complexity += 1
        self.generic_visit(node)

    def visit_BoolOp(self, node: ast.BoolOp) -> None:
        self.complexity += max(0, len(node.values) - 1)
        self.generic_visit(node)

    def visit_comprehension(self, node: ast.comprehension) -> None:
        self.complexity += 1
        self.generic_visit(node)

    def visit_Assert(self, node: ast.Assert) -> None:
        self.complexity += 1
        self.generic_visit(node)

    def visit_Match(self, node: ast.Match) -> None:
        self.complexity += len(node.cases)
        self.generic_visit(node)

    def visit_match_case(self, node: ast.match_case) -> None:
        if node.guard is not None:
            self.complexity += 1
        self.generic_visit(node)

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        return None

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        return None

    def visit_Lambda(self, node: ast.Lambda) -> None:
        return None

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        return None


def _collect_function_complexities(
    module: ast.Module,
) -> tuple[_FunctionComplexity, ...]:
    collector = _FunctionCollector()
    collector.visit(module)
    return tuple(collector.functions)


class _FunctionCollector(ast.NodeVisitor):
    def __init__(self) -> None:
        self._scope: list[str] = []
        self.functions: list[_FunctionComplexity] = []

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        self._scope.append(node.name)
        self.generic_visit(node)
        self._scope.pop()

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self._record_function(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        self._record_function(node)

    def _record_function(
        self,
        node: ast.FunctionDef | ast.AsyncFunctionDef,
    ) -> None:
        qualified_name = ".".join((*self._scope, node.name))
        counter = _ComplexityCounter()
        for statement in node.body:
            counter.visit(statement)
        self.functions.append(
            _FunctionComplexity(
                qualified_name=qualified_name,
                complexity=counter.complexity,
            )
        )
        self._scope.append(node.name)
        self.generic_visit(node)
        self._scope.pop()


__all__ = [
    "SourceFunctionComplexityException",
    "SourceFunctionComplexityObservation",
    "SourceTreeComplexityReport",
    "build_source_tree_complexity_report",
]
