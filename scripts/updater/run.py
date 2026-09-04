"""Run project-specific image updaters."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


def discover(root: Path) -> list[Path]:
    """Find image directories with an updater and source submodule."""
    images = root / "images"
    if not images.is_dir():
        return []
    return sorted(
        path.parent
        for path in images.glob("*/update.py")
        if (path.parent / "src").is_dir()
    )


def main() -> None:
    """Run all updaters, or selected image updaters."""
    parser = argparse.ArgumentParser()
    parser.add_argument("images", nargs="*")
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[2]
    available = {path.name: path for path in discover(root)}
    selected = args.images or sorted(available)
    unknown = sorted(set(selected) - available.keys())
    if unknown:
        parser.error(f"unknown images: {', '.join(unknown)}")
    for name in selected:
        subprocess.run([sys.executable, str(available[name] / "update.py")], check=True)


if __name__ == "__main__":
    main()
