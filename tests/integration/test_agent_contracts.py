# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

import importlib
import inspect
import os
import sys
from pathlib import Path

import pytest

from agentic_proteins.registry.agents import AgentRegistry
from agentic_proteins.core.decisions import Decision
from agentic_proteins.agents.schemas import (
    CoordinatorAgentOutput,
    CriticAgentOutput,
    FailureAnalysisAgentOutput,
    InputValidationAgentOutput,
    PlannerAgentOutput,
    QualityControlAgentOutput,
    ReportingAgentOutput,
)
from agentic_proteins.agents.planning.schemas import PlanDecision
from agentic_proteins.validation.agents import ALLOWED_TOOL_NAMESPACE, validate_agent


AGENT_MODULES = [
    "agentic_proteins.agents.planning.planner",
    "agentic_proteins.agents.verification.input_validation",
    "agentic_proteins.agents.analysis.sequence_analysis",
    "agentic_proteins.agents.analysis.structure",
    "agentic_proteins.agents.verification.quality_control",
    "agentic_proteins.agents.verification.critic",
    "agentic_proteins.agents.analysis.failure_analysis",
    "agentic_proteins.agents.reporting.reporting",
    "agentic_proteins.agents.execution.coordinator",
]


AGENT_CLASSES = [
    "PlannerAgent",
    "InputValidationAgent",
    "SequenceAnalysisAgent",
    "StructureAgent",
    "QualityControlAgent",
    "CriticAgent",
    "FailureAnalysisAgent",
    "ReportingAgent",
    "CoordinatorAgent",
]


def _repo_files(root: Path) -> set[Path]:
    scan_roots = [
        root / "packages" / "agentic-proteins" / "src",
        root / "tests",
        root / "docs",
        root / "scripts",
        root / "makefiles",
        root / "artifacts",
    ]
    files: set[Path] = set()
    for scan_root in scan_roots:
        if not scan_root.exists():
            continue
        for path in scan_root.rglob("*"):
            if path.is_file():
                files.add(path)
    return files


def test_agents_import_purity(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("PYTHONDONTWRITEBYTECODE", "1")
    sys.dont_write_bytecode = True

    allowed_keys = {"COLUMNS", "LINES"}
    allowed_defaults = {"COLUMNS": "80", "LINES": "24"}
    original_getenv = os.getenv
    original_getitem = os.environ.__class__.__getitem__

    def _blocked_getenv(key, *_args, **_kwargs):
        if key in allowed_keys:
            return original_getenv(key)
        raise AssertionError("Environment variables must not be read at import time.")

    def _blocked_getitem(_self, _key):
        if _key in allowed_keys:
            try:
                return original_getitem(os.environ, _key)
            except KeyError:
                return allowed_defaults[_key]
        raise AssertionError("Environment variables must not be read at import time.")

    monkeypatch.setattr(os, "getenv", _blocked_getenv)
    monkeypatch.setattr(os.environ.__class__, "__getitem__", _blocked_getitem, raising=False)
    monkeypatch.setattr(os.environ, "get", _blocked_getenv, raising=False)

    root = Path(__file__).resolve().parents[2]
    before_files = _repo_files(root)
    before_modules = set(sys.modules)

    for module in AGENT_MODULES:
        importlib.import_module(module)

    after_files = _repo_files(root)
    after_modules = set(sys.modules)

    new_files = after_files - before_files
    assert not new_files, f"Agent imports must not write files: {sorted(new_files)[:5]}"

    heavy = {"torch", "jax", "jaxlib", "tensorflow"}
    newly_imported = after_modules - before_modules
    assert not (heavy & newly_imported), "Heavy libraries must not be imported at module load."


def test_validate_agent_contracts() -> None:
    for module_name, class_name in zip(AGENT_MODULES, AGENT_CLASSES, strict=True):
        module = importlib.import_module(module_name)
        agent_cls = getattr(module, class_name)
        validate_agent(agent_cls)


def test_registry_explicit_registration() -> None:
    AgentRegistry._registry.clear()
    AgentRegistry._locked = False
    for module_name, class_name in zip(AGENT_MODULES, AGENT_CLASSES, strict=True):
        module = importlib.import_module(module_name)
        agent_cls = getattr(module, class_name)
        AgentRegistry.register(agent_cls)
    AgentRegistry.lock()
    with pytest.raises(ValueError):
        AgentRegistry.register(agent_cls)


def test_validate_requested_tools_rejects_unknown() -> None:
    module = importlib.import_module("agentic_proteins.agents.analysis.sequence_analysis")
    agent = module.SequenceAnalysisAgent()
    with pytest.raises(ValueError):
        agent.validate_requested_tools({"not_registered_tool"})


def test_decision_only_outputs_signature() -> None:
    for module_name, class_name in zip(AGENT_MODULES, AGENT_CLASSES, strict=True):
        module = importlib.import_module(module_name)
        agent_cls = getattr(module, class_name)
        sig = inspect.signature(agent_cls.decide)
        if agent_cls.name == "planner":
            assert sig.return_annotation in {PlanDecision, PlannerAgentOutput}
        elif agent_cls.name == "quality_control":
            assert sig.return_annotation is QualityControlAgentOutput
        elif agent_cls.name == "critic":
            assert sig.return_annotation is CriticAgentOutput
        elif agent_cls.name == "coordinator":
            assert sig.return_annotation is CoordinatorAgentOutput
        elif agent_cls.name == "input_validation":
            assert sig.return_annotation is InputValidationAgentOutput
        elif agent_cls.name == "failure_analysis":
            assert sig.return_annotation is FailureAnalysisAgentOutput
        elif agent_cls.name == "reporting":
            assert sig.return_annotation is ReportingAgentOutput
        else:
            assert sig.return_annotation is Decision


def test_no_cross_agent_imports() -> None:
    root = Path(__file__).resolve().parents[2]
    agents_dir = (
        root / "packages" / "agentic-proteins" / "src" / "agentic_proteins" / "agents"
    )
    forbidden = {
        "planner",
        "sequence_analysis",
        "structure",
        "quality_control",
        "critic",
        "coordinator",
        "input_validation",
        "failure_analysis",
        "reporting",
    }
    for path in agents_dir.glob("*.py"):
        if path.name in {"__init__.py", "base.py"}:
            continue
        content = path.read_text()
        for module in forbidden:
            if f"agentic_proteins.agents.{module}" in content:
                raise AssertionError(f"Cross-agent import found in {path}")


def test_agents_import_only_allowed_domains() -> None:
    root = Path(__file__).resolve().parents[2]
    agents_dir = (
        root / "packages" / "agentic-proteins" / "src" / "agentic_proteins" / "agents"
    )
    allowed_prefixes = (
        "from agentic_proteins.agents.schemas",
        "from agentic_proteins.core.decisions",
        "from agentic_proteins.core.execution",
        "from agentic_proteins.core.observations",
        "from agentic_proteins.domain.",
        "from agentic_proteins.execution.evaluation.",
        "from agentic_proteins.execution.schemas",
        "from agentic_proteins.memory.schemas",
        "from agentic_proteins.agents.planning.schemas",
        "from agentic_proteins.registry.",
        "from agentic_proteins.validation.",
        "from agentic_proteins.agents.base",
        "import agentic_proteins.agents.schemas",
        "import agentic_proteins.core.decisions",
        "import agentic_proteins.core.execution",
        "import agentic_proteins.core.observations",
        "import agentic_proteins.domain.",
        "import agentic_proteins.execution.evaluation.",
        "import agentic_proteins.execution.schemas",
        "import agentic_proteins.memory.schemas",
        "import agentic_proteins.agents.planning.schemas",
        "import agentic_proteins.registry.",
        "import agentic_proteins.validation.",
        "import agentic_proteins.agents.base",
    )
    for path in agents_dir.glob("*.py"):
        if path.name in {"__init__.py", "base.py"}:
            continue
        content = path.read_text()
        for line in content.splitlines():
            stripped = line.lstrip()
            if stripped.startswith("from agentic_proteins.") or stripped.startswith("import agentic_proteins."):
                if not stripped.startswith(allowed_prefixes):
                    raise AssertionError(f"Agent import outside allowed domains: {path}")


def test_capability_coverage() -> None:
    capability_map: dict[str, list[str]] = {}
    for module_name, class_name in zip(AGENT_MODULES, AGENT_CLASSES, strict=True):
        module = importlib.import_module(module_name)
        agent_cls = getattr(module, class_name)
        for capability in agent_cls.capabilities:
            capability_map.setdefault(capability, []).append(agent_cls.name)

    assert capability_map, "No capabilities declared."
    duplicates = {cap: agents for cap, agents in capability_map.items() if len(agents) > 1}
    assert not duplicates, f"Duplicated capabilities detected: {duplicates}"


def test_tool_allowlists_in_namespace() -> None:
    for module_name, class_name in zip(AGENT_MODULES, AGENT_CLASSES, strict=True):
        module = importlib.import_module(module_name)
        agent_cls = getattr(module, class_name)
        assert agent_cls.allowed_tools.issubset(ALLOWED_TOOL_NAMESPACE)
