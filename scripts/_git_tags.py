"""Resolve lightweight and annotated remote Git tags to commits."""

from __future__ import annotations

import subprocess
from pathlib import Path


def parse(lines: list[str]) -> dict[str, str]:
    """Map tags to commits, preferring peeled annotated-tag revisions."""
    direct: dict[str, str] = {}
    peeled: dict[str, str] = {}
    prefix = "refs/tags/"
    for line in lines:
        revision, ref = line.split("\t", 1)
        if not ref.startswith(prefix):
            continue
        tag = ref[len(prefix) :]
        if tag.endswith("^{}"):
            peeled[tag[:-3]] = revision
        else:
            direct[tag] = revision
    return direct | peeled


def remote(remote: str, *, cwd: Path | None = None) -> dict[str, str]:
    """List remote tags without changing local refs or working trees."""
    lines = subprocess.run(
        ["git", "ls-remote", "--tags", remote],
        cwd=cwd,
        check=True,
        stdout=subprocess.PIPE,
        text=True,
    ).stdout.splitlines()
    return parse(lines)
