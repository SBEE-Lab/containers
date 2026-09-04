#!/usr/bin/env python3
"""Update AlphaFold 3 source to latest stable upstream release."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[2]))

from scripts.updater import update


if __name__ == "__main__":
    result = update(
        image_dir=Path(__file__).parent,
        upstream="google-deepmind/alphafold3",
    )
    print(f"{result.old_revision} -> {result.new_revision} ({result.version})")
