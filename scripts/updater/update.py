"""Update an image source submodule to latest permitted upstream release."""

from __future__ import annotations

import re
import subprocess
from dataclasses import dataclass
from pathlib import Path

from scripts import _git_tags

from . import _git
from .version import VersionScheme, latest_matching_version

_UPSTREAM = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")


@dataclass(frozen=True)
class UpdateResult:
    """Source snapshot selected by an update."""

    old_revision: str
    new_revision: str
    version: str


def _remote_tags(repository: str) -> dict[str, str]:
    if _UPSTREAM.fullmatch(repository) is None:
        raise ValueError(f"invalid GitHub repository: {repository!r}")
    return _git_tags.remote(f"https://github.com/{repository}.git")


def update(
    *,
    image_dir: Path,
    upstream: str,
    tag_pattern: str = r"^v?[0-9]+\.[0-9]+\.[0-9]+$",
    version_scheme: VersionScheme = "semver",
) -> UpdateResult:
    """Update ``image_dir/src`` to highest permitted release tag."""
    image_dir = image_dir.resolve()
    source = image_dir / "src"
    root = _git.repository_root(image_dir)
    if source.parent != image_dir or not source.is_dir():
        raise ValueError(f"missing source submodule: {source}")

    _git.gitlink_revision(root, source)
    old_revision = _git.revision(source)
    _git.require_clean(source)
    tags = _remote_tags(upstream)
    tag, version = latest_matching_version(tags, tag_pattern, version_scheme)
    new_revision = tags[tag]

    if old_revision != new_revision:
        url = f"https://github.com/{upstream}.git"
        subprocess.run(
            ["git", "fetch", "--depth=1", url, f"refs/tags/{tag}"],
            cwd=source,
            check=True,
        )
        fetched = _git.output(["rev-parse", "FETCH_HEAD^{commit}"], cwd=source)
        if fetched != new_revision:
            raise ValueError(f"upstream tag changed while updating: {tag}")
        subprocess.run(["git", "checkout", "--detach", fetched], cwd=source, check=True)

    return UpdateResult(old_revision, new_revision, version)
