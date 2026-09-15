"""Strict SBEE curated CalVer tag handling."""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date

SBEE_CALVER_TAG_PATTERN = r"^sbee-(?P<year>[0-9]{4})\.(?P<month>[0-9]{2})\.(?P<day>[0-9]{2})\.(?P<sequence>[1-9][0-9]*)$"
_CALVER_TAG = re.compile(SBEE_CALVER_TAG_PATTERN)


@dataclass(frozen=True, order=True)
class CalVer:
    """Calendar release ordered by date and daily sequence."""

    year: int
    month: int
    day: int
    sequence: int

    def __str__(self) -> str:
        """Render normalized OCI-compatible version without source prefix."""
        return f"{self.year:04d}.{self.month:02d}.{self.day:02d}.{self.sequence}"

    @classmethod
    def parse(cls, tag: str) -> CalVer:
        """Parse an immutable ``sbee-YYYY.MM.DD.N`` source tag."""
        match = _CALVER_TAG.fullmatch(tag)
        if match is None:
            raise ValueError(f"not an SBEE CalVer tag: {tag!r}")
        values = tuple(
            int(match[name]) for name in ("year", "month", "day", "sequence")
        )
        try:
            date(*values[:3])
        except ValueError as error:
            raise ValueError(f"not an SBEE CalVer tag: {tag!r}") from error
        return cls(*values)
