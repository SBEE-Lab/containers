"""Publish discoverable GitHub releases for immutable OCI images."""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import tempfile
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from scripts.builder.build import _verify_attestation

_DIGEST = re.compile(r"^sha256:[0-9a-f]{64}$")
_REVISION = re.compile(r"^[0-9a-f]{40}$")


@dataclass(frozen=True)
class ImageRelease:
    """Immutable identity exposed by one GitHub release."""

    image: str
    version: str
    digest: str
    revision: str

    @property
    def name(self) -> str:
        return self.image.rsplit("/", 1)[-1]

    @property
    def tag(self) -> str:
        return f"{self.name}-{self.version}"

    @property
    def reference(self) -> str:
        return f"{self.image}@{self.digest}"

    def manifest(self) -> dict[str, object]:
        return {
            "schemaVersion": 1,
            **asdict(self),
            "reference": self.reference,
        }


def _validated_release(data: dict[str, Any]) -> ImageRelease:
    fields = ("image", "version", "digest", "revision")
    if any(not isinstance(data.get(field), str) or not data[field] for field in fields):
        raise ValueError("release identity has missing or invalid fields")
    release = ImageRelease(*(data[field] for field in fields))
    if _DIGEST.fullmatch(release.digest) is None:
        raise ValueError(f"invalid image digest: {release.digest}")
    if _REVISION.fullmatch(release.revision) is None:
        raise ValueError(f"invalid source revision: {release.revision}")
    return release


def load_build_release(path: Path) -> ImageRelease:
    """Read release identity emitted by a successful build."""
    data = json.loads(path.read_text())
    if not isinstance(data, dict):
        raise TypeError(f"invalid build result: {path}")
    return _validated_release(data)


def load_registry_release(
    image: str, version: str, inspection: dict[str, Any]
) -> ImageRelease:
    """Recover release identity from an existing tagged Registry image."""
    labels = inspection.get("Labels")
    if not isinstance(labels, dict):
        raise TypeError(f"missing labels on {image}:{version}")
    if inspection.get("Name") != image:
        raise ValueError(
            f"Registry returned unexpected image name for {image}:{version}"
        )
    if labels.get("org.opencontainers.image.version") != version:
        raise ValueError(f"version label does not match {image}:{version}")
    return _validated_release(
        {
            "image": image,
            "version": version,
            "digest": inspection.get("Digest"),
            "revision": labels.get("org.opencontainers.image.revision"),
        }
    )


def _notes(release: ImageRelease) -> str:
    return (
        f"Immutable OCI release for `{release.image}`.\n\n"
        "```console\n"
        f"docker pull {release.image}:{release.version}\n"
        f"docker pull {release.reference}\n"
        "```\n\n"
        f"- Source revision: `{release.revision}`\n"
        f"- OCI digest: `{release.digest}`\n"
        "- SBOM: verified\n"
        "- Provenance: verified\n"
    )


def _existing_release_matches(release: ImageRelease, directory: Path) -> bool:
    viewed = subprocess.run(
        ["gh", "release", "view", release.tag],
        check=False,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    if viewed.returncode != 0:
        return False
    subprocess.run(
        [
            "gh",
            "release",
            "download",
            release.tag,
            "--pattern",
            "release-manifest.json",
            "--dir",
            str(directory),
            "--clobber",
        ],
        check=True,
    )
    existing = json.loads((directory / "release-manifest.json").read_text())
    if existing != release.manifest():
        raise ValueError(f"existing GitHub release differs: {release.tag}")
    return True


def publish(release: ImageRelease, target: str) -> None:
    """Create one idempotent GitHub release with machine-readable identity."""
    with tempfile.TemporaryDirectory(prefix="image-release-") as temporary:
        directory = Path(temporary)
        if _existing_release_matches(release, directory):
            return
        manifest = directory / "release-manifest.json"
        notes = directory / "notes.md"
        manifest.write_text(json.dumps(release.manifest(), indent=2) + "\n")
        notes.write_text(_notes(release))
        subprocess.run(
            [
                "gh",
                "release",
                "create",
                release.tag,
                "--target",
                target,
                "--title",
                release.tag,
                "--notes-file",
                str(notes),
                str(manifest),
            ],
            check=True,
        )


def _inspect(image: str, version: str) -> ImageRelease:
    output = subprocess.run(
        ["skopeo", "inspect", f"docker://{image}:{version}"],
        check=True,
        stdout=subprocess.PIPE,
        text=True,
    ).stdout
    inspection = json.loads(output)
    if not isinstance(inspection, dict):
        raise TypeError(f"invalid Registry inspection for {image}:{version}")
    release = load_registry_release(image, version, inspection)
    _verify_attestation(release.reference, "SBOM.SPDX")
    _verify_attestation(release.reference, "Provenance.SLSA")
    return release


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--target", default=os.environ.get("GITHUB_SHA", "HEAD"))
    subparsers = parser.add_subparsers(dest="command", required=True)
    publish_parser = subparsers.add_parser("publish")
    publish_parser.add_argument("results", nargs="+", type=Path)
    backfill_parser = subparsers.add_parser("backfill")
    backfill_parser.add_argument("image")
    backfill_parser.add_argument("version")
    args = parser.parse_args()

    releases = (
        [load_build_release(path) for path in args.results]
        if args.command == "publish"
        else [_inspect(args.image, args.version)]
    )
    for release in releases:
        publish(release, args.target)


if __name__ == "__main__":
    main()
