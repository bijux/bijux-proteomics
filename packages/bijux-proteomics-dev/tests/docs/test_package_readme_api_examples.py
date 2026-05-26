from __future__ import annotations

from pathlib import Path
import re

REPO_ROOT = next(
    parent
    for parent in Path(__file__).resolve().parents
    if (parent / "packages").is_dir() and (parent / "configs").is_dir()
)


def _real_package_names() -> tuple[str, ...]:
    return (
        "bijux-proteomics-foundation",
        "bijux-proteomics-core",
        "bijux-proteomics-runtime",
    )


def _package_readme(package_name: str) -> Path:
    return REPO_ROOT / "packages" / package_name / "README.md"


def _section(text: str, heading: str) -> str:
    marker = f"## {heading}\n"
    start = text.find(marker)
    assert start >= 0, f"missing section heading: {heading}"
    start += len(marker)
    end = text.find("\n## ", start)
    if end < 0:
        end = len(text)
    return text[start:end]


def _python_blocks(section: str) -> tuple[str, ...]:
    return tuple(
        block.strip()
        for block in re.findall(r"```python\n(.*?)```", section, flags=re.DOTALL)
    )


def test_real_package_readmes_expose_api_and_non_goal_sections() -> None:
    failures: list[str] = []

    for package_name in _real_package_names():
        path = _package_readme(package_name)
        text = path.read_text(encoding="utf-8")
        for heading in ("Public APIs", "What this package must not do"):
            if f"## {heading}" not in text:
                failures.append(
                    f"{path.relative_to(REPO_ROOT).as_posix()}: missing section {heading!r}"
                )

    assert not failures, "package README API sections failed:\n" + "\n".join(failures)


def test_real_package_readme_public_api_examples_execute(tmp_path: Path) -> None:
    for package_name in _real_package_names():
        path = _package_readme(package_name)
        section = _section(path.read_text(encoding="utf-8"), "Public APIs")
        blocks = _python_blocks(section)
        assert blocks, f"{path.relative_to(REPO_ROOT).as_posix()}: no python examples found"
        example_tmp = tmp_path / package_name
        example_tmp.mkdir(parents=True, exist_ok=True)
        globals_dict = {
            "__name__": "__readme_example__",
            "TMP_PATH": example_tmp,
        }
        for index, block in enumerate(blocks, start=1):
            exec(
                compile(
                    block,
                    f"{path.relative_to(REPO_ROOT).as_posix()}::public_api_example_{index}",
                    "exec",
                ),
                globals_dict,
                globals_dict,
            )
