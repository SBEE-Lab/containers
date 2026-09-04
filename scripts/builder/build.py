"""Build one immutable submodule snapshot with Docker Buildx."""

from __future__ import annotations

import json
import os
import re
import subprocess
import tarfile
import tempfile
from dataclasses import dataclass
from pathlib import Path

from scripts import _git_tags
from scripts.updater.semver import SemVer, latest_matching_tag

from ._metadata import read_image_digest


@dataclass(frozen=True)
class BuildResult:
    """Identity of a completed image build."""

    digest: str
    revision: str
    version: str


def _output(arguments: list[str], *, cwd: Path) -> str:
    return subprocess.run(
        ["git", *arguments],
        cwd=cwd,
        check=True,
        stdout=subprocess.PIPE,
        text=True,
    ).stdout.strip()


def _snapshot_revision(image_dir: Path) -> tuple[Path, Path, str]:
    image_dir = image_dir.resolve()
    root = Path(_output(["rev-parse", "--show-toplevel"], cwd=image_dir)).resolve()
    source = image_dir / "src"
    relative = source.relative_to(root)
    fields = _output(["ls-tree", "HEAD", "--", str(relative)], cwd=root).split()
    if len(fields) < 3 or fields[0] != "160000" or fields[1] != "commit":
        raise ValueError(f"no committed source submodule at {relative}")
    return root, source, fields[2]


def _version_for_revision(source: Path, revision: str) -> str:
    tags = _git_tags.remote("origin", cwd=source)
    matching = [tag for tag, commit in tags.items() if commit == revision]
    tag = latest_matching_tag(matching, r"^v?[0-9]+\.[0-9]+\.[0-9]+$")
    return str(SemVer.parse(tag))


def _export_snapshot(source: Path, revision: str, destination: Path) -> None:
    archive = destination.parent / "source.tar"
    with archive.open("wb") as output:
        subprocess.run(
            ["git", "archive", "--format=tar", revision],
            cwd=source,
            check=True,
            stdout=output,
        )
    destination.mkdir()
    with tarfile.open(archive) as source_archive:
        source_archive.extractall(destination, filter="data")


def _require_unpublished(image: str) -> None:
    result = subprocess.run(
        ["skopeo", "inspect", f"docker://{image}"],
        check=False,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
        text=True,
    )
    if result.returncode == 0:
        raise ValueError(f"refusing to overwrite published image: {image}")
    error = result.stderr.lower()
    if "manifest unknown" not in error and "manifest_unknown" not in error:
        raise subprocess.CalledProcessError(
            result.returncode,
            result.args,
            stderr=result.stderr,
        )


def _derive_dockerfile(
    source: Path, destination: Path, build_arguments: list[str]
) -> None:
    """Declare non-secret build arguments in each stage of a derived Dockerfile."""
    for name in build_arguments:
        if re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", name) is None:
            raise ValueError(f"invalid build argument name: {name}")

    lines: list[str] = []
    stages = 0
    for line in source.read_text().splitlines(keepends=True):
        lines.append(line)
        if re.match(r"^\s*FROM(?:\s|$)", line, re.IGNORECASE):
            stages += 1
            lines.extend(f"ARG {name}\n" for name in build_arguments)
    if stages == 0:
        raise ValueError(f"Dockerfile has no FROM instruction: {source}")
    destination.write_text("".join(lines))


def _build_argument_arguments(build_arguments: dict[str, str]) -> list[str]:
    return [
        argument
        for name, value in build_arguments.items()
        for argument in ("--build-arg", f"{name}={value}")
    ]


def _attestation_arguments() -> list[str]:
    return ["--provenance=mode=max,version=v1", "--sbom=true"]


def _registry_cache_arguments(image: str) -> list[str]:
    cache = f"{image}-cache:buildkit"
    return [
        "--cache-from",
        f"type=registry,ref={cache}",
        "--cache-to",
        f"type=registry,ref={cache},mode=max,image-manifest=true,oci-mediatypes=true",
    ]


def _verify_attestation(reference: str, attribute: str) -> None:
    output = subprocess.run(
        [
            "docker",
            "buildx",
            "imagetools",
            "inspect",
            reference,
            "--format",
            f"{{{{ json .{attribute} }}}}",
        ],
        check=True,
        stdout=subprocess.PIPE,
        text=True,
    ).stdout
    value = json.loads(output)
    if not isinstance(value, dict) or not value:
        raise ValueError(f"missing {attribute} attestation for {reference}")


def _record_summary(result: BuildResult, image: str) -> None:
    summary = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary is None:
        return
    with Path(summary).open("a") as output:
        output.write(
            f"### `{image}:{result.version}`\n\n"
            f"- Source: `{result.revision}`\n"
            f"- Digest: `{result.digest}`\n"
            "- SBOM: verified\n"
            "- Provenance: verified\n"
        )


def build(
    *,
    image_dir: Path,
    image: str,
    dockerfile: str = "Dockerfile",
    build_arguments: dict[str, str] | None = None,
    push: bool = False,
) -> BuildResult:
    """Build source recorded by committed submodule gitlink."""
    image_dir = image_dir.resolve()
    build_arguments = build_arguments or {}
    _root, source, revision = _snapshot_revision(image_dir)
    version = _version_for_revision(source, revision)
    tag = f"{image}:{version}"
    if push:
        _require_unpublished(tag)

    with tempfile.TemporaryDirectory(prefix="container-build-") as directory:
        temporary = Path(directory)
        context = temporary / "src"
        metadata = temporary / "metadata.json"
        _export_snapshot(source, revision, context)
        source_dockerfile = context / dockerfile
        build_dockerfile = source_dockerfile
        if build_arguments:
            build_dockerfile = temporary / "Dockerfile.derived"
            _derive_dockerfile(
                source_dockerfile, build_dockerfile, list(build_arguments)
            )
        subprocess.run(
            [
                "docker",
                "buildx",
                "build",
                "--file",
                str(build_dockerfile),
                "--platform",
                "linux/amd64",
                "--tag",
                tag,
                *_build_argument_arguments(build_arguments),
                *_attestation_arguments(),
                "--metadata-file",
                str(metadata),
                *(_registry_cache_arguments(image) if push else []),
                "--push" if push else "--load",
                str(context),
            ],
            check=True,
        )
        result = BuildResult(read_image_digest(metadata), revision, version)
        if push:
            reference = f"{image}@{result.digest}"
            _verify_attestation(reference, "SBOM.SPDX")
            _verify_attestation(reference, "Provenance.SLSA")
        _record_summary(result, image)
        return result
