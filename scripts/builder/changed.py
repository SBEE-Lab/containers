"""Select images whose committed source gitlinks changed."""

from __future__ import annotations

import argparse
import re
import subprocess
from pathlib import Path

_SOURCE_PATH = re.compile(r"^images/([^/]+)/src$")


def _output(root: Path, arguments: list[str]) -> str:
    return subprocess.run(
        ["git", *arguments],
        cwd=root,
        check=True,
        stdout=subprocess.PIPE,
        text=True,
    ).stdout.strip()


def _image_at_revision(root: Path, revision: str, path: str) -> str | None:
    match = _SOURCE_PATH.fullmatch(path)
    if match is None:
        return None
    entry = _output(root, ["ls-tree", revision, "--", path]).split()
    if len(entry) < 3 or entry[0] != "160000" or entry[1] != "commit":
        return None
    return match[1]


def all_images(root: Path, revision: str) -> list[str]:
    """List images backed by source submodules at a revision."""
    lines = _output(root, ["ls-tree", "-r", "--full-tree", revision, "--", "images"])
    paths = [line.split("\t", 1)[1] for line in lines.splitlines() if "\t" in line]
    return sorted(
        image
        for path in paths
        if (image := _image_at_revision(root, revision, path)) is not None
    )


def changed_images(root: Path, before: str, after: str) -> list[str]:
    """List images whose source gitlink changed between two revisions."""
    if set(before) == {"0"}:
        return all_images(root, after)
    paths = _output(
        root,
        ["diff", "--name-only", "--diff-filter=AMRT", before, after, "--", "images"],
    ).splitlines()
    return sorted(
        image
        for path in paths
        if (image := _image_at_revision(root, after, path)) is not None
    )


def main() -> None:
    """Print one selected image name per line."""
    parser = argparse.ArgumentParser()
    parser.add_argument("before", nargs="?")
    parser.add_argument("after", nargs="?", default="HEAD")
    parser.add_argument("--all", action="store_true")
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[2]
    if args.all:
        images = all_images(root, args.after)
    elif args.before is None:
        parser.error("before revision is required unless --all is used")
    else:
        images = changed_images(root, args.before, args.after)
    print(*images, sep="\n")


if __name__ == "__main__":
    main()
