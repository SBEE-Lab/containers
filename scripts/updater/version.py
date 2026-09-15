"""Release tag policies shared by image builders and source updaters."""

from __future__ import annotations

import re
from collections.abc import Iterable
from typing import Literal

from .calver import CalVer
from .semver import SemVer

VersionScheme = Literal["semver", "sbee-calver"]


def _parse(tag: str, scheme: VersionScheme) -> SemVer | CalVer:
    if scheme == "semver":
        return SemVer.parse(tag)
    if scheme == "sbee-calver":
        return CalVer.parse(tag)
    raise ValueError(f"unknown version scheme: {scheme!r}")


def latest_matching_version(
    tags: Iterable[str], tag_pattern: str, scheme: VersionScheme
) -> tuple[str, str]:
    """Return selected source tag and normalized OCI version."""
    if scheme not in ("semver", "sbee-calver"):
        raise ValueError(f"unknown version scheme: {scheme!r}")
    policy = re.compile(tag_pattern)
    candidates: list[tuple[SemVer | CalVer, str]] = []
    for tag in tags:
        if policy.fullmatch(tag) is None:
            continue
        try:
            candidates.append((_parse(tag, scheme), tag))
        except ValueError:
            continue
    if not candidates:
        raise ValueError(f"no {scheme} tag matches project policy")
    version, tag = max(candidates)
    return tag, str(version)
