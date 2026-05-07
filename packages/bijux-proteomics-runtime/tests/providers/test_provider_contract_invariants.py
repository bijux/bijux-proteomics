from __future__ import annotations

from bijux_proteomics_runtime.providers.contracts import (
    PredictionResult,
    ProviderArtifactGuarantees,
    ProviderExecutionContract,
    ProviderFailureGuarantees,
    provider_contract_supports_error_code,
    validate_prediction_result,
)


def test_provider_contract_declares_machine_readable_failure_codes() -> None:
    contract = ProviderExecutionContract(
        cooperative_cancellation=True,
        failure_guarantees=ProviderFailureGuarantees(
            expected_error_codes=("TIMEOUT", "REMOTE_ERROR"),
            cancellation_code="CANCELLED",
            partial_output_code="NO_OUTPUT",
            malformed_input_code="BAD_INPUT",
            corrupted_artifact_code="INVALID_OUTPUT_SHAPE",
        ),
    )

    assert provider_contract_supports_error_code(contract, "TIMEOUT")
    assert provider_contract_supports_error_code(contract, "CANCELLED")
    assert provider_contract_supports_error_code(contract, "INVALID_OUTPUT_SHAPE")
    assert not provider_contract_supports_error_code(contract, "AUTH_ERROR")


def test_validate_prediction_result_flags_partial_and_malformed_outputs() -> None:
    contract = ProviderExecutionContract(
        cooperative_cancellation=True,
        artifact_guarantees=ProviderArtifactGuarantees(
            pdb_text_required=True,
            raw_payload_required=True,
            required_raw_keys=("mean_plddt", "artifact_manifest"),
        ),
    )

    result = PredictionResult(
        pdb_text="",
        provider="wrong-provider",
        raw={"mean_plddt": 82.4},
    )

    assert validate_prediction_result(
        result,
        provider_name="heuristic_proxy",
        contract=contract,
    ) == [
        "missing_pdb_text",
        "provider_name_mismatch",
        "missing_raw_key:artifact_manifest",
    ]


def test_validate_prediction_result_accepts_contract_complete_outputs() -> None:
    contract = ProviderExecutionContract(
        cooperative_cancellation=False,
        artifact_guarantees=ProviderArtifactGuarantees(
            pdb_text_required=True,
            raw_payload_required=True,
            required_raw_keys=("mean_plddt", "artifact_manifest"),
        ),
    )
    result = PredictionResult(
        pdb_text="ATOM      1  CA  GLY A   1      10.000  10.000  10.000  1.00 95.00           C",
        provider="heuristic_proxy",
        raw={
            "mean_plddt": 95.0,
            "artifact_manifest": {"predicted_pdb": "predicted.pdb"},
        },
    )

    assert (
        validate_prediction_result(
            result,
            provider_name="heuristic_proxy",
            contract=contract,
        )
        == []
    )
