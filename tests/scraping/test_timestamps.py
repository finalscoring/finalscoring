"""Tests for the shared ISO-timestamp helpers."""

from datetime import UTC, datetime

from finalscoring.scraping.timestamps import as_utc, parse_iso


def test_parse_iso_keeps_the_offset_as_written():
    assert parse_iso("2026-08-27T00:11:51+00:00") == datetime(2026, 8, 27, 0, 11, 51, tzinfo=UTC)


def test_parse_iso_leaves_a_naive_value_naive():
    assert parse_iso("2026-01-02T03:04:05") == datetime(2026, 1, 2, 3, 4, 5)


def test_parse_iso_returns_none_for_missing_or_unparseable():
    assert parse_iso(None) is None
    assert parse_iso("") is None
    assert parse_iso("not a date") is None


def test_as_utc_reads_a_naive_value_as_utc():
    assert as_utc("2011-03-14") == datetime(2011, 3, 14, tzinfo=UTC)
    assert as_utc("2026-01-02T03:04:05") == datetime(2026, 1, 2, 3, 4, 5, tzinfo=UTC)


def test_as_utc_keeps_an_explicit_offset():
    assert as_utc("2011-03-14T09:00:00+00:00") == datetime(2011, 3, 14, 9, tzinfo=UTC)


def test_as_utc_returns_none_for_missing_or_unparseable():
    assert as_utc(None) is None
    assert as_utc("") is None
    assert as_utc("not a date") is None
