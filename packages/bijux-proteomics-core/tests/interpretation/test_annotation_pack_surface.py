# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

import json
from pathlib import Path

import pytest

from bijux_proteomics.interpretation.annotation_packs import (
    AnnotationPackTableName,
    AnnotationPackValidationError,
    load_annotation_pack,
    render_annotation_pack_json,
)
from bijux_proteomics.interpretation.biological_context_mapping import (
    BiologicalContextKind,
)
from bijux_proteomics.interpretation.complex_enrichment import ComplexMemberKind
from bijux_proteomics.interpretation.pathway_enrichment import PathwayMemberKind
from bijux_proteomics.interpretation.regulator_inference import RegulatorEvidenceType
from bijux_proteomics_foundation import DocumentSchema


def _write_pack(path: Path, payload: dict[str, object]) -> Path:
    path.write_text(json.dumps(payload, sort_keys=True) + "\n", encoding="utf-8")
    return path


def test_load_annotation_pack_normalizes_supported_tables(tmp_path: Path) -> None:
    pack_path = _write_pack(
        tmp_path / "annotation_pack_valid.json",
        {
            "document_schema": DocumentSchema(
                created_by="bijux-proteomics-benchmark",
                document_kind="annotation_pack",
                package_name="bijux-proteomics-benchmark",
                status="generated",
            ).to_dict(),
            "pack_name": "benchmark-annotations",
            "pack_version": "2026.05",
            "protein_features": [
                {
                    "protein_ref": "sp|P04637|P53_HUMAN",
                    "gene_symbol": "TP53",
                    "description": "tumor protein p53",
                }
            ],
            "pathways": [
                {
                    "pathway_id": "pathway:stress_response",
                    "pathway_name": "stress response",
                    "protein_ref": "P04637",
                }
            ],
            "complexes": [
                {
                    "complex_id": "complex:guardian",
                    "complex_name": "guardian complex",
                    "gene_symbol": "TP53",
                }
            ],
            "compartments": [
                {
                    "protein_ref": "P04637",
                    "context_id": "GO:0005737",
                    "context_name": "cytoplasm",
                }
            ],
            "drug_targets": [
                {
                    "protein_ref": "P04637",
                    "context_id": "drugbank:DB0001",
                    "context_name": "example inhibitor",
                }
            ],
            "disease_terms": [
                {
                    "protein_ref": "P04637",
                    "context_id": "DOID:162",
                    "context_name": "cancer",
                }
            ],
            "kinase_substrates": [
                {
                    "regulator": "MAPK1",
                    "site_key": "P04637:S15",
                    "source_name": "phosphosite",
                }
            ],
            "orthologs": [
                {
                    "source_species": "human",
                    "source_protein_ref": "P04637",
                    "target_species": "mouse",
                    "target_protein_ref": "P02340",
                    "source_gene_symbol": "TP53",
                    "target_gene_symbol": "Trp53",
                }
            ],
            "metadata": {"curator": "team-bijux"},
        },
    )

    pack = load_annotation_pack(pack_path)

    assert pack.pack_name == "benchmark-annotations"
    assert pack.pack_version == "2026.05"
    assert pack.summary.protein_feature_count == 1
    assert pack.summary.pathway_count == 1
    assert pack.summary.complex_count == 1
    assert pack.summary.compartment_count == 1
    assert pack.summary.drug_target_count == 1
    assert pack.summary.disease_term_count == 1
    assert pack.summary.kinase_substrate_count == 1
    assert pack.summary.ortholog_count == 1
    assert pack.metadata == {"curator": "team-bijux"}
    assert pack.protein_features[0].protein_ref == "P04637"
    assert pack.pathways[0].member_kind is PathwayMemberKind.PROTEIN
    assert pack.pathways[0].member_id == "P04637"
    assert pack.complexes[0].member_kind is ComplexMemberKind.GENE
    assert pack.compartments[0].context_kind is BiologicalContextKind.SUBCELLULAR_COMPARTMENT
    assert pack.drug_targets[0].context_kind is BiologicalContextKind.DRUG_TARGET
    assert pack.disease_terms[0].context_kind is BiologicalContextKind.DISEASE_TERM
    assert pack.kinase_substrates[0].evidence_type is RegulatorEvidenceType.KINASE_SUBSTRATE
    assert pack.kinase_substrates[0].site_key == "P04637:S15"
    assert pack.orthologs[0].source_protein_ref == "P04637"
    assert pack.orthologs[0].target_protein_ref == "P02340"


def test_load_annotation_pack_raises_row_level_validation_errors(tmp_path: Path) -> None:
    pack_path = _write_pack(
        tmp_path / "annotation_pack_invalid.json",
        {
            "pack_name": "broken-annotations",
            "protein_features": [
                {
                    "protein_ref": "P04637",
                }
            ],
            "pathways": [
                {
                    "pathway_id": "pathway:stress_response",
                    "protein_ref": "P04637",
                    "gene_symbol": "TP53",
                }
            ],
            "complexes": [
                ["not", "an", "object"]
            ],
            "compartments": [
                {
                    "protein_ref": "P04637",
                }
            ],
            "kinase_substrates": [
                {
                    "regulator": "MAPK1",
                    "site_key": 15,
                }
            ],
            "orthologs": [
                {
                    "source_species": "human",
                    "source_protein_ref": "P04637",
                    "target_species": "mouse",
                }
            ],
        },
    )

    with pytest.raises(AnnotationPackValidationError) as exc_info:
        load_annotation_pack(pack_path)

    report = exc_info.value.report
    rejected = {
        (row.table_name, row.row_number): row.reason
        for row in report.rejected_rows
    }

    assert report.source_path == str(pack_path)
    assert rejected[(AnnotationPackTableName.PROTEIN_FEATURES, 1)] == (
        "protein feature row requires at least one annotation field"
    )
    assert rejected[(AnnotationPackTableName.PATHWAYS, 1)] == (
        "pathway row must choose protein_ref or gene_symbol, not both"
    )
    assert rejected[(AnnotationPackTableName.COMPLEXES, 1)] == (
        "annotation pack rows must be JSON objects"
    )
    assert rejected[(AnnotationPackTableName.COMPARTMENTS, 1)] == (
        "context_id: Field required"
    )
    assert rejected[(AnnotationPackTableName.KINASE_SUBSTRATES, 1)] == (
        "site_key: Input should be a valid string"
    )
    assert rejected[(AnnotationPackTableName.ORTHOLOGS, 1)] == (
        "target_protein_ref: Field required"
    )


def test_render_annotation_pack_json_round_trips_loaded_pack(tmp_path: Path) -> None:
    original_path = _write_pack(
        tmp_path / "annotation_pack_round_trip.json",
        {
            "document_schema": DocumentSchema(
                created_by="bijux-proteomics-benchmark",
                document_kind="annotation_pack",
                package_name="bijux-proteomics-benchmark",
                status="generated",
            ).to_dict(),
            "pack_name": "round-trip-pack",
            "pack_version": "2026.05",
            "protein_features": [
                {
                    "protein_ref": "sp|P04637|P53_HUMAN",
                    "gene_symbol": "TP53",
                    "description": "tumor protein p53",
                    "annotation_identifier": "ENSP00000269305",
                }
            ],
            "pathways": [
                {
                    "pathway_id": "pathway:stress_response",
                    "pathway_name": "stress response",
                    "gene_symbol": "TP53",
                    "source_name": "reactome",
                }
            ],
            "complexes": [
                {
                    "complex_id": "complex:guardian",
                    "complex_name": "guardian complex",
                    "protein_ref": "P04637",
                    "source_accession": "complexportal:CPX-1",
                }
            ],
            "compartments": [
                {
                    "protein_ref": "P04637",
                    "context_id": "GO:0005737",
                    "context_name": "cytoplasm",
                    "source_name": "GO",
                }
            ],
            "drug_targets": [
                {
                    "protein_ref": "P04637",
                    "context_id": "drugbank:DB0001",
                    "context_name": "example inhibitor",
                    "source_accession": "DrugBank:DB0001",
                    "metadata": {"relationship_type": "direct_target"},
                }
            ],
            "disease_terms": [
                {
                    "protein_ref": "P04637",
                    "context_id": "DOID:162",
                    "context_name": "cancer",
                    "source_name": "Disease Ontology",
                }
            ],
            "kinase_substrates": [
                {
                    "regulator": "MAPK1",
                    "site_key": "P04637:S15:Phospho",
                    "source_accession": "PSP:0001",
                }
            ],
            "orthologs": [
                {
                    "source_species": "human",
                    "source_protein_ref": "P04637",
                    "target_species": "mouse",
                    "target_protein_ref": "P02340",
                    "source_gene_symbol": "TP53",
                    "target_gene_symbol": "Trp53",
                }
            ],
            "metadata": {"curator": "team-bijux"},
        },
    )
    loaded_pack = load_annotation_pack(original_path)
    exported_path = tmp_path / "annotation_pack_exported.json"
    exported_path.write_text(
        render_annotation_pack_json(loaded_pack),
        encoding="utf-8",
    )

    reloaded_pack = load_annotation_pack(exported_path)

    assert reloaded_pack == loaded_pack.model_copy(
        update={"source_path": str(exported_path)}
    )
