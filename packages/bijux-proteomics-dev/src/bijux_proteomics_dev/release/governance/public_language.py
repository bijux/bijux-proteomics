from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path

from bijux_proteomics_dev.governance.runtime.topology import REPO_ROOT

__all__ = [
    "PUBLIC_LANGUAGE_GLOSSARY_PATH",
    "PublicLanguageGlossary",
    "PublicLanguageIssue",
    "PublicLanguageTerm",
    "build_public_language_glossary",
    "run",
    "validate_public_language",
]


FOUNDATION_DIR = REPO_ROOT / "docs" / "01-bijux-proteomics" / "foundation"
PUBLIC_LANGUAGE_GLOSSARY_PATH = FOUNDATION_DIR / "public-language-glossary.md"
_LAST_REVIEWED = "2026-07-21"


@dataclass(frozen=True)
class PublicLanguageTerm:
    """One governed public term or retired phrase."""

    term: str
    status: str
    preferred_phrase: str
    allowed_surfaces: tuple[str, ...]
    rationale: str


@dataclass(frozen=True)
class PublicLanguageGlossary:
    """The governed public language contract for release-facing wording."""

    allowed_terms: tuple[PublicLanguageTerm, ...]
    retired_terms: tuple[PublicLanguageTerm, ...]


@dataclass(frozen=True)
class PublicLanguageIssue:
    """One public-language drift issue."""

    code: str
    detail: str


def build_public_language_glossary() -> PublicLanguageGlossary:
    """Build the repository-owned public language contract."""

    return PublicLanguageGlossary(
        allowed_terms=(
            PublicLanguageTerm(
                term="outsider-auditable",
                status="allowed",
                preferred_phrase="outsider-auditable",
                allowed_surfaces=(
                    "README.md",
                    "docs/01-bijux-proteomics/foundation/flagship-release-candidate.md",
                    "docs/01-bijux-proteomics/foundation/workflow-claim-limits.md",
                ),
                rationale="Reserved for workflow families whose package, rerun, and review surfaces survive skeptical inspection without maintainer narration.",
            ),
            PublicLanguageTerm(
                term="internal-support-only",
                status="allowed",
                preferred_phrase="internal-support-only",
                allowed_surfaces=(
                    "README.md",
                    "docs/01-bijux-proteomics/foundation/flagship-release-candidate.md",
                    "docs/01-bijux-proteomics/foundation/workflow-claim-limits.md",
                    "docs/01-bijux-proteomics/foundation/why-multiplex-stops-at-internal-support.md",
                ),
                rationale="Marks workflow families with real implementation and evidence that still do not support outsider-facing reliance.",
            ),
            PublicLanguageTerm(
                term="independent rerun dossier",
                status="allowed",
                preferred_phrase="independent rerun dossier",
                allowed_surfaces=(
                    "docs/01-bijux-proteomics/foundation/independent-rerun-dossiers.md",
                    "docs/01-bijux-proteomics/foundation/flagship-release-candidate.md",
                ),
                rationale="Names the reviewer-facing artifact that tests whether one workflow sentence survives a second challenge lane.",
            ),
            PublicLanguageTerm(
                term="external review kit",
                status="allowed",
                preferred_phrase="external review kit",
                allowed_surfaces=(
                    "docs/01-bijux-proteomics/foundation/external-review-kits.md",
                    "docs/01-bijux-proteomics/foundation/flagship-release-candidate.md",
                ),
                rationale="Names the shortest outsider inspection route through benchmark, rerun, and recommendation evidence for one workflow family.",
            ),
            PublicLanguageTerm(
                term="decision brief",
                status="allowed",
                preferred_phrase="decision brief",
                allowed_surfaces=(
                    "packages/bijux-proteomics-runtime/src/bijux_proteomics_runtime/api/routes/decision_briefs.py",
                ),
                rationale="Identifies the stable route contract for package-owned packet creation, lookup, diff, and export operations.",
            ),
        ),
        retired_terms=(
            PublicLanguageTerm(
                term="authority boundary",
                status="retired",
                preferred_phrase="claim limits or internal-support limit",
                allowed_surfaces=(),
                rationale="Hides whether a claim is supported, blocked, or refused.",
            ),
            PublicLanguageTerm(
                term="workflow authority matrix",
                status="retired",
                preferred_phrase="workflow claim limits",
                allowed_surfaces=(),
                rationale="Projects general authority instead of stating family-specific claim limits.",
            ),
            PublicLanguageTerm(
                term="canonical workflow",
                status="retired",
                preferred_phrase="what one workflow family supports today",
                allowed_surfaces=(),
                rationale="Suggests broader finality than the bounded workflow sentence supported by current evidence.",
            ),
            PublicLanguageTerm(
                term="reviewable-proteomics",
                status="retired",
                preferred_phrase="flagship workflow chain or bounded workflow family",
                allowed_surfaces=(),
                rationale="Was an internal campaign label rather than a durable product or workflow concept.",
            ),
            PublicLanguageTerm(
                term="multiplex authority boundary",
                status="retired",
                preferred_phrase="why multiplex stops at internal support",
                allowed_surfaces=(),
                rationale="Obscures the direct statement that multiplex stops at internal support.",
            ),
        ),
    )


def _front_matter(title: str) -> list[str]:
    return [
        "---",
        f"title: {title}",
        "audience: mixed",
        "type: explanation",
        "status: canonical",
        "owner: bijux-proteomics-docs",
        f"last_reviewed: {_LAST_REVIEWED}",
        "---",
        "",
    ]


def _render_glossary(glossary: PublicLanguageGlossary) -> str:
    lines = _front_matter("Public Language Glossary")
    lines.extend(
        [
            "# Public Language Glossary",
            "",
            "Public terms separate workflow evidence, reviewer access, and route contracts without implying authority that the underlying proof has not earned.",
            "",
            "```mermaid",
            "flowchart LR",
            '    C["scientific or operational claim"] --> E["inspect governed evidence"]',
            '    E --> T{"term status"}',
            '    T -->|allowed| A["use the bounded definition"]',
            '    T -->|retired| R["use the named replacement"]',
            '    A --> P["public sentence"]',
            '    R --> P',
            "```",
            "",
            "## Allowed Terms",
            "",
            "| term | use it as | allowed surfaces | why it stays |",
            "| --- | --- | --- | --- |",
        ]
    )
    for term in glossary.allowed_terms:
        lines.append(
            f"| `{term.term}` | `{term.preferred_phrase}` | {', '.join(f'`{surface}`' for surface in term.allowed_surfaces)} | {term.rationale} |"
        )
    lines.extend(
        [
            "",
            "## Retired Terms",
            "",
            "| retired phrase | use instead | why it was retired |",
            "| --- | --- | --- |",
        ]
    )
    for term in glossary.retired_terms:
        lines.append(
            f"| `{term.term}` | `{term.preferred_phrase}` | {term.rationale} |"
        )
    lines.extend(
        [
            "",
            "## Validation boundary",
            "",
            "- `validate_public_language()` rejects retired phrases in root docs, package READMEs, foundation docs, and release-support surfaces.",
            "- `workflow_public_scrutiny.py` and `final_preflight.py` require the glossary to match the checked contract.",
            "- A term that is absent from the allowed set carries no governed release meaning.",
        ]
    )
    return "\n".join(lines) + "\n"


def _target_paths(repo_root: Path) -> tuple[Path, ...]:
    foundation_docs = [
        repo_root / "docs" / "01-bijux-proteomics" / "foundation" / name
        for name in (
            "index.md",
            "flagship-release-candidate.md",
            "elite-readiness-scorecard.md",
            "release-readiness-matrix.md",
            "release-narrowing-protocol.md",
            "hostile-review-kit.md",
            "public-artifact-index.md",
            "public-artifact-role-matrix.md",
            "independent-rerun-dossiers.md",
            "external-review-kits.md",
            "workflow-claim-limits.md",
            "why-multiplex-stops-at-internal-support.md",
            "what-one-workflow-family-supports-today.md",
        )
    ]
    package_readmes = sorted((repo_root / "packages").glob("*/README.md"))
    explicit = [
        repo_root / "README.md",
        repo_root / "docs" / "index.md",
        repo_root
        / "docs"
        / "08-bijux-proteomics-maintain"
        / "bijux-proteomics-dev"
        / "release-support.md",
        repo_root
        / "packages"
        / "bijux-proteomics-runtime"
        / "src"
        / "bijux_proteomics_runtime"
        / "api"
        / "routes"
        / "decision_briefs.py",
    ]
    seen: set[Path] = set()
    ordered: list[Path] = []
    for path in (*explicit, *foundation_docs, *package_readmes):
        if path in seen or not path.exists():
            continue
        seen.add(path)
        ordered.append(path)
    return tuple(ordered)


def validate_public_language(
    repo_root: Path = REPO_ROOT,
) -> tuple[PublicLanguageIssue, ...]:
    """Reject retired public-language phrases after the cleanup."""

    issues: list[PublicLanguageIssue] = []
    glossary = build_public_language_glossary()
    retired_terms = tuple(term.term.lower() for term in glossary.retired_terms)
    for path in _target_paths(repo_root):
        text = path.read_text(encoding="utf-8").lower()
        for term in retired_terms:
            if term in text:
                issues.append(
                    PublicLanguageIssue(
                        code="retired-public-language",
                        detail=f"{path.relative_to(repo_root).as_posix()} still uses retired phrase {term!r}",
                    )
                )
    return tuple(issues)


def run(check: bool = False) -> int:
    """Write or verify the governed public-language glossary."""

    rendered = _render_glossary(build_public_language_glossary())
    if check:
        return int(
            PUBLIC_LANGUAGE_GLOSSARY_PATH.read_text(encoding="utf-8") != rendered
        )
    PUBLIC_LANGUAGE_GLOSSARY_PATH.write_text(rendered, encoding="utf-8")
    return 0


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="verify without writing")
    args = parser.parse_args()
    raise SystemExit(run(check=args.check))


if __name__ == "__main__":
    main()
