"""Strict stable SemVer tag handling."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Iterable

_STABLE_TAG = re.compile(
    r"^v?(?P<major>0|[1-9][0-9]*)\.(?P<minor>0|[1-9][0-9]*)\.(?P<patch>0|[1-9][0-9]*)$"
)


@dataclass(frozen=True, order=True)
class SemVer:
    """Stable SemVer core version."""

    major: int
    minor: int
    patch: int

    def __str__(self) -> str:
        """Render normalized version without a tag prefix."""
        return f"{self.major}.{self.minor}.{self.patch}"

    @classmethod
    def parse(cls, tag: str) -> SemVer:
        """Parse a stable SemVer tag with an optional ``v`` prefix."""
        match = _STABLE_TAG.fullmatch(tag)
        if match is None:
            raise ValueError(f"not a stable SemVer tag: {tag!r}")
        return cls(*(int(match[name]) for name in ("major", "minor", "patch")))


def latest_matching_tag(tags: Iterable[str], tag_pattern: str) -> str:
    """Return highest stable SemVer tag accepted by project policy."""
    policy = re.compile(tag_pattern)
    candidates: list[tuple[SemVer, str]] = []
    for tag in tags:
        if policy.fullmatch(tag) is None:
            continue
        try:
            candidates.append((SemVer.parse(tag), tag))
        except ValueError:
            continue
    if not candidates:
        raise ValueError("no stable SemVer tag matches project policy")
    return max(candidates)[1]
