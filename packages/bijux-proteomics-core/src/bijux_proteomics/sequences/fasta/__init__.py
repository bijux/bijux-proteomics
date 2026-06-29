# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Canonical FASTA owner package for sequence intake and residue policy."""

from __future__ import annotations

from bijux_proteomics.sequences.fasta.models import (
    DecoyGenerationManifest,
    DecoyGenerationMode,
    DecoyGenerationReport,
    DuplicateAccessionPolicy,
    FastaDatabaseComposition,
    FastaDeduplicationReport,
    FastaFilterReport,
    FastaParseMode,
    FastaParseReport,
    FastaProvenanceManifest,
    FastaSequenceRecord,
    FastaStatsReport,
    NormalizedProteinRecord,
    ProteinSequence,
    RejectedFastaRecord,
    ResiduePolicyEntry,
    ResiduePolicyState,
    SequenceIssueSeverity,
    SequenceResiduePolicy,
    SequenceValidationIssue,
    SequenceValidationResult,
    TargetDecoyValidationReport,
    UniProtAccession,
    sequence_length,
)
from bijux_proteomics.sequences.fasta.policies import (
    build_sequence_residue_policy,
    canonicalize_protein_reference,
    parse_uniprot_accession,
    sequence_checksum,
)

__all__ = [
    "DecoyGenerationManifest",
    "DecoyGenerationMode",
    "DecoyGenerationReport",
    "DuplicateAccessionPolicy",
    "FastaDatabaseComposition",
    "FastaDeduplicationReport",
    "FastaFilterReport",
    "FastaParseMode",
    "FastaParseReport",
    "FastaProvenanceManifest",
    "FastaSequenceRecord",
    "FastaStatsReport",
    "NormalizedProteinRecord",
    "ProteinSequence",
    "RejectedFastaRecord",
    "ResiduePolicyEntry",
    "ResiduePolicyState",
    "SequenceIssueSeverity",
    "SequenceResiduePolicy",
    "SequenceValidationIssue",
    "SequenceValidationResult",
    "TargetDecoyValidationReport",
    "UniProtAccession",
    "build_sequence_residue_policy",
    "canonicalize_protein_reference",
    "parse_uniprot_accession",
    "sequence_checksum",
    "sequence_length",
]
