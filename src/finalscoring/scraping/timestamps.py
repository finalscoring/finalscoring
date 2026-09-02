"""Parsing the ISO timestamps sources put in their metadata.

`parse_iso` keeps the offset as written — use it when the source states one.
`as_utc` additionally reads a naive value as UTC; use it only where the source
guarantees that (a WordPress REST `date_gmt`, an htmldate day-string), never for
a bare `article:published_time`, which is site-local.
"""

from datetime import UTC, datetime


def parse_iso(value: str | None) -> datetime | None:
    """Parse an ISO timestamp, keeping the offset as written. Use when the source states one."""
    if not value:
        return None
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        return None


def as_utc(value: str | None) -> datetime | None:
    """Like `parse_iso`, but read a naive value as UTC. Use only where the source guarantees that."""
    parsed = parse_iso(value)
    if parsed is None:
        return None
    return parsed.replace(tzinfo=UTC) if parsed.tzinfo is None else parsed
