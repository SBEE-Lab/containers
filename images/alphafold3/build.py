#!/usr/bin/env python3
"""Build AlphaFold 3 image from pinned upstream source."""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[2]))

from scripts.builder import build


def main() -> None:
    """Build AlphaFold 3 and optionally push its immutable version tag."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--push", action="store_true")
    args = parser.parse_args()
    result = build(
        image_dir=Path(__file__).parent,
        image="registry.sjanglab.org/sjanglab/alphafold3",
        dockerfile="docker/Dockerfile",
        push=args.push,
    )
    print(result.digest)


if __name__ == "__main__":
    main()
