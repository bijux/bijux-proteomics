from __future__ import annotations

from pathlib import Path

from bijux_proteomics_runtime.providers.assurance import (
    ProviderRealityTier,
    build_execution_reality_matrix,
    build_provider_capability_matrix,
    cpu_safe_conformance_providers,
    provider_validation_lanes,
)


def _repo_root() -> Path:
    return next(
        parent
        for parent in Path(__file__).resolve().parents
        if (parent / "packages").is_dir() and (parent / "configs").is_dir()
    )


def test_provider_validation_lanes_keep_fixtures_and_tests_visible() -> None:
    repo_root = _repo_root()
    lanes = provider_validation_lanes()

    assert lanes
    for lane in lanes:
        for fixture_path in lane.repo_relative_fixture_paths:
            assert (repo_root / fixture_path).exists(), fixture_path
        for test_path in lane.validating_test_paths:
            assert (repo_root / test_path).exists(), test_path
        assert lane.expected_artifact_paths


def test_provider_capability_matrix_exposes_contract_and_validation_shape() -> None:
    rows = {row.provider_name: row for row in build_provider_capability_matrix()}

    assert rows["heuristic_proxy"].supports_cpu is True
    assert "heuristic_cpu_conformance" in rows["heuristic_proxy"].validation_lane_ids
    assert "mean_plddt" in rows["heuristic_proxy"].required_raw_keys
    assert "BAD_INPUT" in rows["heuristic_proxy"].expected_error_codes
    assert "esmfold_real_local" in rows["local_esmfold"].validation_lane_ids


def test_execution_reality_matrix_distinguishes_cpu_safe_and_real_validation() -> None:
    rows = {row.provider_name: row for row in build_execution_reality_matrix()}

    assert ProviderRealityTier.CPU_SAFE_CONFORMANCE in rows["heuristic_proxy"].reality_tiers
    assert ProviderRealityTier.REAL_LOCAL_VALIDATION in rows["local_esmfold"].reality_tiers
    assert ProviderRealityTier.REAL_REMOTE_VALIDATION in rows["api_colabfold"].reality_tiers
    assert rows["api_openprotein_esmfold"].simulation_only is False


def test_cpu_safe_conformance_providers_are_always_available_to_runtime() -> None:
    providers = cpu_safe_conformance_providers()

    assert "heuristic_proxy" in providers
    assert providers
