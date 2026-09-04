"""Git operations used by image source updates."""

from __future__ import annotations

import subprocess
from pathlib import Path


def output(arguments: list[str], *, cwd: Path) -> str:
    """Run Git and return stripped stdout."""
    return subprocess.run(
        ["git", *arguments],
        cwd=cwd,
        check=True,
        stdout=subprocess.PIPE,
        text=True,
    ).stdout.strip()


def repository_root(path: Path) -> Path:
    """Find superproject root containing an image directory."""
    return Path(output(["rev-parse", "--show-toplevel"], cwd=path)).resolve()


def gitlink_revision(root: Path, source: Path) -> str:
    """Read exact commit recorded for a submodule path."""
    relative = source.relative_to(root)
    fields = output(["ls-files", "--stage", "--", str(relative)], cwd=root).split()
    if len(fields) < 2 or fields[0] != "160000":
        raise ValueError(f"not a registered submodule: {relative}")
    return fields[1]


def revision(repository: Path) -> str:
    """Read commit currently checked out in a repository."""
    return output(["rev-parse", "HEAD^{commit}"], cwd=repository)


def require_clean(source: Path) -> None:
    """Refuse to overwrite local source changes."""
    if output(["status", "--porcelain"], cwd=source):
        raise ValueError(f"submodule has local changes: {source}")
