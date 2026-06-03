# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Private test-support helpers for source-tree cyclomatic complexity ceilings."""

from __future__ import annotations

import ast
from dataclasses import dataclass
from pathlib import Path

from bijux_proteomics_foundation.testing.generated_file_markers import (
    is_marked_generated_file,
)


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
    skipped_marked_generated_count: int
    approved_over_ceiling: tuple[SourceFunctionComplexityObservation, ...]
    unexpected_over_ceiling: tuple[SourceFunctionComplexityObservation, ...]
    stale_exceptions: tuple[SourceFunctionComplexityException, ...]


def build_source_tree_complexity_report(
    source_root: Path,
    *,
    ceiling: int,
    exceptions: tuple[SourceFunctionComplexityException, ...] = (),
    exclude_marked_generated: bool = False,
) -> SourceTreeComplexityReport:
    """Scan one source tree and classify functions above the shared complexity ceiling."""

    exception_by_key = {
        (entry.relative_path, entry.qualified_name): entry for entry in exceptions
    }
    approved_over_ceiling: list[SourceFunctionComplexityObservation] = []
    unexpected_over_ceiling: list[SourceFunctionComplexityObservation] = []
    observed_complexities: dict[tuple[str, str], int] = {}
    skipped_marked_generated_count = 0

    for path in sorted(source_root.rglob("*.py")):
        if exclude_marked_generated and is_marked_generated_file(path):
            skipped_marked_generated_count += 1
            continue
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
        skipped_marked_generated_count=skipped_marked_generated_count,
        approved_over_ceiling=tuple(approved_over_ceiling),
        unexpected_over_ceiling=tuple(unexpected_over_ceiling),
        stale_exceptions=stale_exceptions,
    )


@dataclass(frozen=True)
class _FunctionComplexity:
    """Recorded complexity score for one collected function or method."""

    qualified_name: str
    complexity: int


class _ComplexityCounter(ast.NodeVisitor):
    def __init__(self) -> None:
        """Start every function at the baseline cyclomatic complexity of one."""
        self.complexity = 1

    def visit_If(self, node: ast.If) -> None:
        """Count each conditional branch and continue into its body."""
        self.complexity += 1
        self.generic_visit(node)

    def visit_IfExp(self, node: ast.IfExp) -> None:
        """Count ternary expressions as one additional decision branch."""
        self.complexity += 1
        self.generic_visit(node)

    def visit_For(self, node: ast.For) -> None:
        """Count synchronous loops as one additional decision branch."""
        self.complexity += 1
        self.generic_visit(node)

    def visit_AsyncFor(self, node: ast.AsyncFor) -> None:
        """Count asynchronous loops as one additional decision branch."""
        self.complexity += 1
        self.generic_visit(node)

    def visit_While(self, node: ast.While) -> None:
        """Count while loops as one additional decision branch."""
        self.complexity += 1
        self.generic_visit(node)

    def visit_Try(self, node: ast.Try) -> None:
        """Count exception handlers and alternate try branches toward complexity."""
        self.complexity += len(node.handlers)
        if node.orelse:
            self.complexity += 1
        if node.finalbody:
            self.complexity += 1
        self.generic_visit(node)

    def visit_BoolOp(self, node: ast.BoolOp) -> None:
        """Count chained boolean operands beyond the first as decision points."""
        self.complexity += max(0, len(node.values) - 1)
        self.generic_visit(node)

    def visit_comprehension(self, node: ast.comprehension) -> None:
        """Count each comprehension generator as one additional branch."""
        self.complexity += 1
        self.generic_visit(node)

    def visit_Assert(self, node: ast.Assert) -> None:
        """Count assert guards as one additional branching condition."""
        self.complexity += 1
        self.generic_visit(node)

    def visit_Match(self, node: ast.Match) -> None:
        """Count match cases toward the overall branch total."""
        self.complexity += len(node.cases)
        self.generic_visit(node)

    def visit_match_case(self, node: ast.match_case) -> None:
        """Count guarded match cases as an extra decision within the case."""
        if node.guard is not None:
            self.complexity += 1
        self.generic_visit(node)

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        """Stop nested function bodies from inflating the current function score."""
        return None

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        """Stop nested async function bodies from inflating the current score."""
        return None

    def visit_Lambda(self, node: ast.Lambda) -> None:
        """Ignore nested lambdas while scoring the surrounding callable."""
        return None

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        """Ignore nested class bodies while scoring the surrounding callable."""
        return None


def _collect_function_complexities(
    module: ast.Module,
) -> tuple[_FunctionComplexity, ...]:
    """Collect qualified function names and complexity scores from one module AST."""
    collector = _FunctionCollector()
    collector.visit(module)
    return tuple(collector.functions)


class _FunctionCollector(ast.NodeVisitor):
    def __init__(self) -> None:
        """Initialize nested scope tracking for qualified function names."""
        self._scope: list[str] = []
        self.functions: list[_FunctionComplexity] = []

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        """Enter class scope so contained functions receive class-qualified names."""
        self._scope.append(node.name)
        self.generic_visit(node)
        self._scope.pop()

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        """Record one synchronous function and recurse into nested definitions."""
        self._record_function(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        """Record one asynchronous function and recurse into nested definitions."""
        self._record_function(node)

    def _record_function(
        self,
        node: ast.FunctionDef | ast.AsyncFunctionDef,
    ) -> None:
        """Compute and store complexity for one function using the current scope."""
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
