#!/usr/bin/env python3
"""Build MULTI-evolve image from pinned SBEE release source."""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[2]))

from scripts.builder import build
from scripts.updater.calver import SBEE_CALVER_TAG_PATTERN


def main() -> None:
    """Build MULTI-evolve and optionally push its immutable CalVer tag."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--push", action="store_true")
    args = parser.parse_args()
    result = build(
        image_dir=Path(__file__).parent,
        image="registry.sjanglab.org/sjanglab/multievolve",
        tag_pattern=SBEE_CALVER_TAG_PATTERN,
        version_scheme="sbee-calver",
        push=args.push,
    )
    print(result.digest)


if __name__ == "__main__":
    main()
