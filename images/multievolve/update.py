#!/usr/bin/env python3
"""Update MULTI-evolve source to latest SBEE calendar release."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[2]))

from scripts.updater import update
from scripts.updater.calver import SBEE_CALVER_TAG_PATTERN

if __name__ == "__main__":
    result = update(
        image_dir=Path(__file__).parent,
        upstream="SBEE-Lab/MULTI-evolve",
        tag_pattern=SBEE_CALVER_TAG_PATTERN,
        version_scheme="sbee-calver",
    )
    print(f"{result.old_revision} -> {result.new_revision} ({result.version})")
