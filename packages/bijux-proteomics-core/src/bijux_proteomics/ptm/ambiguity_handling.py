# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""PTM ambiguity review and site-group quantification surfaces."""

from __future__ import annotations

from bijux_proteomics.ptm.contracts import PtmSiteEntry, PtmSiteGroupEvidenceEntry


def build_ptm_site_group_evidence(
    site_entries: tuple[PtmSiteEntry, ...],
) -> tuple[PtmSiteGroupEvidenceEntry, ...]:
    """Group PTM site evidence by candidate-position set when localization stays unresolved."""

    grouped: dict[tuple[str, str, tuple[int, ...]], list[PtmSiteEntry]] = {}
    for entry in site_entries:
        candidate_positions = (
            entry.candidate_positions if entry.candidate_positions else (entry.position,)
        )
        grouped.setdefault(
            (entry.protein_ref, entry.modification_name, candidate_positions),
            [],
        ).append(entry)

    group_entries: list[PtmSiteGroupEvidenceEntry] = []
    for (protein_ref, modification_name, candidate_positions), bucket in sorted(
        grouped.items()
    ):
        unresolved = len(candidate_positions) > 1 or any(
            entry.ambiguous for entry in bucket
        )
        positions_token = "|".join(str(position) for position in candidate_positions)
        note = (
            "site evidence remains unresolved across multiple candidate positions"
            if unresolved
            else "site evidence resolves to one protein position"
        )
        group_entries.append(
            PtmSiteGroupEvidenceEntry(
                group_key=f"{protein_ref}:{modification_name}:{positions_token}",
                protein_ref=protein_ref,
                modification_name=modification_name,
                candidate_positions=candidate_positions,
                site_keys=tuple(sorted(entry.site_key for entry in bucket)),
                spectrum_count=sum(entry.spectrum_count for entry in bucket),
                peptide_count=sum(entry.peptide_count for entry in bucket),
                sample_ids=tuple(
                    sorted(
                        {
                            sample_id
                            for entry in bucket
                            for sample_id in entry.sample_ids
                        }
                    )
                ),
                unresolved=unresolved,
                note=note,
            )
        )
    return tuple(group_entries)
