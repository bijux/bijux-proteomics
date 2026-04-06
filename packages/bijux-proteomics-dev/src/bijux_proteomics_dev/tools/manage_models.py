# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""
Prepare, build, and test protein folding model environments.

This all-in-one script handles the entire lifecycle for local model setup:
1. PREPARE: Downloads model assets and generates functional Dockerfiles
   and inference wrappers for ESMFold and RoseTTAFold-All-Atom.
2. BUILD: Builds Docker images from the generated assets.
3. TEST: Runs a smoke test on the built images using a sample FASTA file.

Usage:
  # Run the full pipeline for all models (rebuilds images by default)
  python scripts/manage_models.py

  # Skip rebuilding images if they already exist
  python scripts/manage_models.py --skip-rebuild

  # Prepare assets only, do not build or test
  python scripts/manage_models.py --no-build
"""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import textwrap
from pathlib import Path
from typing import Optional

# --- Dependency Checks ---
try:
    from huggingface_hub import snapshot_download, list_repo_refs

    HF_OK = True
except ImportError:
    HF_OK = False

try:
    import requests

    REQ_OK = True
except ImportError:
    REQ_OK = False

# --- Path Constants ---
ROOT = Path(__file__).resolve().parents[1]
MODELS_DIR = ROOT / "models"
ESMFOLD_ROOT = MODELS_DIR / "esmfold"
ROSETTA_ROOT = MODELS_DIR / "rosettafold"
TEST_OUTPUT_DIR = ROOT / "artifacts" / "test_manage_models"
# Assume a sample FASTA exists for testing
SAMPLE_FASTA_DIR = ROOT / "examples"
SAMPLE_FASTA_PATH = SAMPLE_FASTA_DIR / "sample_protein.fasta"


# ----------------------------- UTILITY FUNCTIONS -----------------------------


def log(msg: str) -> None:
    """Prints a message to stdout."""
    print(msg, flush=True)


def ensure_dir(p: Path) -> None:
    """Ensures a directory exists."""
    p.mkdir(parents=True, exist_ok=True)


def run(cmd: list[str], cwd: Optional[Path] = None) -> str:
    """Runs a command, captures output, and raises an error on failure."""
    log(f" > Running: {' '.join(cmd)}")
    try:
        proc = subprocess.run(
            cmd, cwd=cwd, check=True, capture_output=True, text=True, encoding="utf-8"
        )
        return proc.stdout.strip()
    except subprocess.CalledProcessError as e:
        error_message = f"""
Command failed (exit code {e.returncode}): {" ".join(cmd)}
--- STDOUT ---
{e.stdout}
--- STDERR ---
{e.stderr}
"""
        raise RuntimeError(error_message) from e
    except FileNotFoundError:
        raise RuntimeError(
            f"Command '{cmd[0]}' not found. Is Docker installed and running?"
        )


def find_latest_version(model_root: Path) -> Path:
    """Finds the most recently prepared model version directory."""
    versions = [
        d for d in model_root.iterdir() if d.is_dir() and (d / ".prepared.ok").exists()
    ]
    if not versions:
        raise FileNotFoundError(
            f"No prepared model versions found in {model_root}. Run the 'prepare' step first."
        )
    return max(versions, key=lambda d: d.stat().st_mtime)


def get_latest_hf_revision(repo_id: str) -> str:
    if not HF_OK:
        raise RuntimeError("'huggingface_hub' not installed.")
    refs = list_repo_refs(repo_id)
    main_branch = next((b for b in refs.branches if b.name == "main"), None)
    if not main_branch:
        raise RuntimeError(f"Could not find 'main' branch in repo '{repo_id}'")
    return main_branch.target_commit


def get_latest_github_commit(repo_slug: str) -> str:
    if not REQ_OK:
        raise RuntimeError("'requests' not installed.")
    api_url, headers = (
        f"https://api.github.com/repos/{repo_slug}/commits/main",
        {"Accept": "application/vnd.github.v3+json"},
    )
    try:
        r = requests.get(api_url, timeout=30, headers=headers)
        r.raise_for_status()
        return r.json()["sha"]
    except requests.RequestException as e:
        raise RuntimeError(f"Failed to fetch latest commit for {repo_slug}: {e}") from e


def git_clone_repo(url: str, out_dir: Path, revision: str, force: bool) -> None:
    if shutil.which("git") is None:
        raise RuntimeError("'git' not found in PATH.")
    if out_dir.exists() and not force:
        log(f" - Repo exists at {out_dir} (use --force to re-clone).")
        return
    if out_dir.exists():
        shutil.rmtree(out_dir)
    log(f" Cloning {url}...")
    run(["git", "clone", url, str(out_dir)])
    run(["git", "checkout", revision], cwd=out_dir)
    log(f" - Cloned repo at revision {revision[:7]}.")


def download_file(url: str, dst: Path) -> None:
    if not REQ_OK:
        raise RuntimeError("'requests' is not installed.")
    log(f" - Downloading from {url} to {dst}")
    with requests.get(url, stream=True, timeout=120) as r:
        r.raise_for_status()
        with open(dst, "wb") as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)


# ----------------------------- ESMFOLD SECTION -----------------------------

_ESMFOLD_DOCKERFILE = textwrap.dedent("""\
    # Dockerfile for ESMFold inference using Hugging Face transformers.
    FROM nvidia/cuda:12.1.1-cudnn8-runtime-ubuntu22.04

    ENV DEBIAN_FRONTEND=noninteractive \\
        PYTHONDONTWRITEBYTECODE=1 \\
        PYTHONUNBUFFERED=1

    # Install base system dependencies
    RUN apt-get update && apt-get install -y --no-install-recommends \\
        python3.10 python3-pip \\
        && rm -rf /var/lib/apt/lists/*

    # Install only the required Python libraries.
    # No C compilation is needed, making the build faster and smaller.
    RUN pip install --no-cache-dir \\
        'torch' \\
        'transformers[accelerate]==4.35.2' \\
        --extra-index-url https://download.pytorch.org/whl/cu121

    WORKDIR /app
    COPY models/esmfold/run_esmfold.py /app/

    VOLUME ["/models", "/inputs", "/outputs"]
    ENTRYPOINT ["python3", "/app/run_esmfold.py"]
""")

_ESMFOLD_WRAPPER = textwrap.dedent("""\
    #!/usr/bin/env python3
    import argparse, os, torch
    from transformers import AutoTokenizer, EsmForProteinFolding

    def read_fasta_one(path: str) -> tuple[str, str]:
        '''Return (sequence, id) from a single-record FASTA file.'''
        header = None
        parts = []
        with open(path, "r") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                if line.startswith(">"):
                    header = line[1:].split()[0]
                else:
                    parts.append(line)
        if not parts:
            raise ValueError(f"No sequence found in FASTA: {path}")
        return ("".join(parts), header or "sequence")

    def main():
        parser = argparse.ArgumentParser(description="Fold a protein using ESMFold.")
        parser.add_argument("--fasta", required=True, help="Path to input FASTA file.")
        parser.add_argument("--output_dir", required=True, help="Directory to save the output PDB file.")
        parser.add_argument("--model_dir", required=True, help="Path to the downloaded ESMFold model directory.")
        args = parser.parse_args()

        print(f"Loading ESMFold model from: {args.model_dir}")
        tokenizer = AutoTokenizer.from_pretrained(args.model_dir)
        model = EsmForProteinFolding.from_pretrained(args.model_dir)

        device = "cuda" if torch.cuda.is_available() else "cpu"
        model = model.to(device)
        print(f"Model loaded successfully on {device.upper()}.")

        sequence, protein_id = read_fasta_one(args.fasta)
        print(f"Processing sequence '{protein_id}' ({len(sequence)} residues).")

        tokenized_input = tokenizer([sequence], return_tensors="pt", add_special_tokens=False)['input_ids'].to(device)
        with torch.no_grad():
            output = model(tokenized_input)

        pdb_string = model.output_to_pdb(output)[0]

        os.makedirs(args.output_dir, exist_ok=True)
        output_path = os.path.join(args.output_dir, f"{protein_id}_esmfold_predicted.pdb")
        with open(output_path, "w") as f: f.write(pdb_string)
        print(f"Success: Predicted structure saved to: {output_path}")

    if __name__ == "__main__": main()
""")


def prepare_esmfold(
    root_dir: Path,
    repo_id: str,
    revision: Optional[str],
    hf_token: Optional[str],
    force: bool,
) -> None:
    log("\n--- [ESMFold] Preparing Assets ---")
    ensure_dir(root_dir)
    latest_rev = revision or get_latest_hf_revision(repo_id)
    version_dir = root_dir / latest_rev[:10]
    marker = version_dir / ".prepared.ok"
    log(f" Target revision: {latest_rev}")

    if marker.exists() and not force:
        log(
            f" - ESMFold version {latest_rev[:10]} is already prepared (use --force to override)."
        )
    else:
        ensure_dir(version_dir)
        log(f" - Downloading HF snapshot: {repo_id}@{latest_rev}")
        snapshot_download(
            repo_id=repo_id,
            revision=latest_rev,
            local_dir=version_dir,
            local_dir_use_symlinks=False,
            token=hf_token,
            etag_timeout=60,
        )
        marker.write_text(f"ok - {repo_id}@{latest_rev}\n")
        log(f" - ESMFold snapshot saved to {version_dir}")

    (root_dir / "esmfold.Dockerfile").write_text(_ESMFOLD_DOCKERFILE)
    wrapper_path = root_dir / "run_esmfold.py"
    wrapper_path.write_text(_ESMFOLD_WRAPPER)
    os.chmod(wrapper_path, 0o755)
    log(f" - Wrote ESMFold Dockerfile and inference script.")


# ----------------------------- ROSETTAFOLD SECTION -----------------------------


def prepare_rosettafold(
    root_dir: Path, github_repo: str, weights_url: Optional[str], force: bool
) -> None:
    log("\n--- [RoseTTAFold] Preparing Assets ---")
    ensure_dir(root_dir)
    latest_sha = get_latest_github_commit(github_repo)
    version_dir = root_dir / latest_sha[:10]
    marker = version_dir / ".prepared.ok"
    log(f"  Target revision: {latest_sha}")

    if marker.exists() and not force:
        log(
            f"  - RoseTTAFold version {latest_sha[:10]} is already prepared (use --force)."
        )
    else:
        git_clone_repo(
            f"https://github.com/{github_repo}.git", version_dir, latest_sha, force
        )
        if weights_url:
            weights_path = version_dir / "weights"
            ensure_dir(weights_path)
            download_file(weights_url, weights_path / "RFAA_paper_weights.pt")
        marker.write_text(f"ok - {github_repo}@{latest_sha}\n")
        log("  - RoseTTAFold repository and weights are ready.")

    repo_df = version_dir / "Dockerfile"
    if not repo_df.exists():
        raise FileNotFoundError(f"Repo Dockerfile not found at {repo_df}")
    log(f"  - Using repo Dockerfile: {repo_df}")


# ----------------------------- BUILD & TEST PIPELINE -----------------------------


def build_and_test_pipeline(model_name: str, force_build: bool, no_test: bool):
    """Orchestrates the build and test sequence for a given model."""
    if model_name == "esmfold":
        build_fn, test_fn = build_esmfold_image, smoke_test_esmfold
    elif model_name == "rosettafold":
        build_fn, test_fn = build_rosettafold_image, smoke_test_rosettafold
    else:
        return

    try:
        build_fn(force_build)
        if not no_test:
            test_fn()
    except (RuntimeError, FileNotFoundError, AssertionError) as e:
        log(f"\nERROR: Pipeline for {model_name} failed: {e}")
        sys.exit(1)


def build_esmfold_image(force: bool):
    log("\n--- [ESMFold] Building Docker Image ---")
    image_tag = "esmfold-agentic-proteins:latest"
    dockerfile_path = ESMFOLD_ROOT / "esmfold.Dockerfile"
    if not dockerfile_path.exists():
        raise FileNotFoundError(f"Dockerfile not found: {dockerfile_path}")

    existing_image = run(["docker", "images", "-q", image_tag])
    if existing_image and not force:
        log(f" - Image {image_tag} already exists (use --skip-rebuild to avoid this).")
        return

    log(f" Building {image_tag}...")
    run(["docker", "build", "-t", image_tag, "-f", str(dockerfile_path), str(ROOT)])
    log(f" - Successfully built {image_tag}")


def build_rosettafold_image(force: bool):
    log("\n--- [RoseTTAFold] Building Docker Image ---")
    image_tag = "rosettafold-agentic-proteins:latest"
    version_dir = find_latest_version(ROSETTA_ROOT)
    repo_dockerfile = version_dir / "Dockerfile"
    if not repo_dockerfile.exists():
        raise FileNotFoundError(f"Repo Dockerfile not found: {repo_dockerfile}")

    existing_image = run(["docker", "images", "-q", image_tag])
    if existing_image and not force:
        log(f"  - Image {image_tag} already exists (use --skip-rebuild to avoid this).")
        return

    log("  Building with repo Dockerfile and repo as build context...")
    run(
        [
            "docker",
            "build",
            "--platform",
            "linux/amd64",
            "-t",
            image_tag,
            "-f",
            str(repo_dockerfile),
            str(
                version_dir
            ),  # build context MUST be the repo dir because Dockerfile uses ADD .
        ]
    )
    log(f"  - Successfully built {image_tag}")


def smoke_test_esmfold():
    log("\n--- [ESMFold] Running Smoke Test ---")
    image_tag, test_dir = (
        "esmfold-agentic-proteins:latest",
        TEST_OUTPUT_DIR / "esmfold_test",
    )
    if test_dir.exists():
        shutil.rmtree(test_dir)
    ensure_dir(test_dir)
    shutil.copy(SAMPLE_FASTA_PATH, test_dir / "input.fasta")

    model_version_dir = find_latest_version(ESMFOLD_ROOT)
    docker_command = [
        "docker",
        "run",
        "--rm",
        "-v",
        f"{test_dir}:/io",
        "-v",
        f"{model_version_dir}:/models/esmfold_version:ro",
        image_tag,
        "--fasta",
        "/io/input.fasta",
        "--output_dir",
        "/io",
        "--model_dir",
        "/models/esmfold_version",
    ]
    run(docker_command)

    if not list(test_dir.glob("*.pdb")):
        raise AssertionError("Smoke test failed: No PDB file was generated.")
    log(f" - Smoke test passed. Output PDB found in {test_dir}")


def smoke_test_rosettafold():
    log("\n--- [RoseTTAFold] Running Smoke Test ---")
    image_tag = "rosettafold-agentic-proteins:latest"
    out = run(
        [
            "docker",
            "run",
            "--rm",
            "--platform",
            "linux/amd64",
            image_tag,
            "python",
            "-c",
            "import rf2aa; print('rf2aa import ok')",
        ]
    )
    if "rf2aa import ok" not in out:
        raise AssertionError("Smoke test failed: rf2aa import did not succeed.")
    log("  - Smoke test passed (rf2aa import).")


# ----------------------------- MAIN CLI -----------------------------


def main():
    p = argparse.ArgumentParser(
        description="Prepare, build, and test protein folding model environments.",
        formatter_class=argparse.RawTextHelpFormatter,
    )
    p.add_argument(
        "--only",
        choices=["esmfold", "rosettafold", "all"],
        default="all",
        help="Which model pipeline to run.",
    )
    # Main pipeline control
    p.add_argument("--no-prepare", action="store_true", help="Skip asset preparation.")
    p.add_argument(
        "--no-build", action="store_true", help="Skip Docker build and test steps."
    )
    p.add_argument(
        "--no-test", action="store_true", help="Skip smoke test after building."
    )
    # Fine-grained control
    p.add_argument(
        "--force", action="store_true", help="Force re-download of model assets."
    )
    p.add_argument(
        "--skip-rebuild",
        action="store_true",
        help="Do not rebuild a Docker image if it already exists.",
    )
    # Model-specific arguments
    p.add_argument(
        "--hf-repo-id",
        default="facebook/esmfold_v1",
        help="Hugging Face repo ID for ESMFold.",
    )
    p.add_argument(
        "--hf-revision", default=None, help="Optional HF revision for ESMFold."
    )
    p.add_argument(
        "--github-repo",
        default="baker-laboratory/RoseTTAFold-All-Atom",
        help="GitHub repo for RoseTTAFold.",
    )
    p.add_argument(
        "--rosetta-weights-url",
        default="http://files.ipd.uw.edu/pub/RF-All-Atom/weights/RFAA_paper_weights.pt",
        help="URL for RoseTTAFold weights.",
    )
    args = p.parse_args()

    # Determine if a rebuild should be forced
    force_build_flag = not args.skip_rebuild

    # Setup a sample FASTA for testing
    ensure_dir(SAMPLE_FASTA_DIR)
    if not SAMPLE_FASTA_PATH.exists():
        log(f"Creating a dummy sample FASTA for testing at {SAMPLE_FASTA_PATH}")
        SAMPLE_FASTA_PATH.write_text(">sample_protein\nMAAKESLSVY")

    try:
        if args.only in ("esmfold", "all"):
            if not args.no_prepare:
                prepare_esmfold(
                    ESMFOLD_ROOT,
                    args.hf_repo_id,
                    args.hf_revision,
                    os.getenv("HF_TOKEN"),
                    args.force,
                )
            if not args.no_build:
                build_and_test_pipeline("esmfold", force_build_flag, args.no_test)

        if args.only in ("rosettafold", "all"):
            if not args.no_prepare:
                prepare_rosettafold(
                    ROSETTA_ROOT, args.github_repo, args.rosetta_weights_url, args.force
                )
            if not args.no_build:
                build_and_test_pipeline("rosettafold", force_build_flag, args.no_test)

        log("\nAll selected tasks completed successfully.")

    except (RuntimeError, FileNotFoundError, AssertionError) as e:
        log(f"\nERROR: An error occurred: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        log("\nOperation cancelled by user.")
        sys.exit(130)


if __name__ == "__main__":
    main()
