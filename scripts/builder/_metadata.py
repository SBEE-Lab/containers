"""Read structured metadata emitted by Docker Buildx."""

from __future__ import annotations

import json
import re
from pathlib import Path

_DIGEST = re.compile(r"^sha256:[0-9a-f]{64}$")


def read_image_digest(path: Path) -> str:
    """Return validated image digest from a Buildx metadata file."""
    metadata = json.loads(path.read_text())
    digest = metadata.get("containerimage.digest")
    if not isinstance(digest, str) or _DIGEST.fullmatch(digest) is None:
        raise ValueError(f"missing or invalid image digest in {path}")
    return digest
