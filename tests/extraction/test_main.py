"""Tests for the extraction CLI, against a stub client rather than a live model."""

import json
from pathlib import Path
from typing import Any, cast

import pytest
from openai import OpenAI
from tenacity import wait_none

from finalscoring.extraction.__main__ import (
    default_output,
    extracted_sources,
    main,
    pending_items,
    read_items,
    run,
)
from finalscoring.extraction.llm import ReviewExtractor
from finalscoring.scraping.item import RawItem
from tests.extraction.test_llm import ONE_REVIEW, SETTINGS, StubClient

ROUNDUP = "https://example.com/roundup"
OTHER = "https://example.com/other"


def _raw_line(url: str) -> str:
    item = RawItem.model_validate(
        {"url": url, "spider_slug": "spiel-des-jahres", "raw_text": "Jane Doe fand Catan gut."}
    )
    return item.model_dump_json() + "\n"


def _input_file(tmp_path: Path, *urls: str) -> Path:
    path = tmp_path / "raw.jl"
    path.write_text("".join(_raw_line(url) for url in urls), encoding="utf-8")
    return path


def _extractor(*responses: str | Exception) -> ReviewExtractor:
    return ReviewExtractor(
        settings=SETTINGS, client=cast("OpenAI", StubClient(*responses)), wait=wait_none()
    )


def _sources(output: Path) -> list[Any]:
    lines = output.read_text(encoding="utf-8").splitlines()
    return [json.loads(line)["source_url"] for line in lines]


def test_every_item_becomes_a_record(tmp_path):
    inputs = _input_file(tmp_path, ROUNDUP, OTHER)
    output = tmp_path / "out" / "extraction.jl"

    failures = run([inputs], output, _extractor(json.dumps(ONE_REVIEW), json.dumps(ONE_REVIEW)))

    assert failures == 0
    assert _sources(output) == [ROUNDUP, OTHER]


def test_already_extracted_sources_are_skipped(tmp_path):
    """Re-running the same command resumes; it does not redo an hour of work."""
    inputs = _input_file(tmp_path, ROUNDUP, OTHER)
    output = tmp_path / "out" / "extraction.jl"
    run([inputs], output, _extractor(json.dumps(ONE_REVIEW), json.dumps(ONE_REVIEW)))

    second = tmp_path / "out" / "extraction-2.jl"
    failures = run([inputs], second, _extractor())

    assert failures == 0
    assert not second.exists()


def test_a_repeated_source_is_extracted_once(tmp_path):
    """Globbing two crawls of one spider must not double a multi-hour run."""
    first = tmp_path / "a.jl"
    first.write_text(_raw_line(ROUNDUP), encoding="utf-8")
    second = tmp_path / "b.jl"
    second.write_text(_raw_line(ROUNDUP), encoding="utf-8")
    output = tmp_path / "out" / "extraction.jl"

    run([first, second], output, _extractor(json.dumps(ONE_REVIEW)))

    assert _sources(output) == [ROUNDUP]


def test_a_sibling_file_counts_as_done(tmp_path):
    """The done-set is the output directory, not just the file being written."""
    inputs = _input_file(tmp_path, ROUNDUP)
    output_dir = tmp_path / "out"
    output_dir.mkdir()
    (output_dir / "earlier.jl").write_text(
        json.dumps({"source_url": ROUNDUP}) + "\n", encoding="utf-8"
    )

    run([inputs], output_dir / "extraction.jl", _extractor())

    assert not (output_dir / "extraction.jl").exists()


def test_force_re_extracts(tmp_path):
    inputs = _input_file(tmp_path, ROUNDUP)
    output = tmp_path / "out" / "extraction.jl"
    run([inputs], output, _extractor(json.dumps(ONE_REVIEW)))

    run([inputs], output, _extractor(json.dumps(ONE_REVIEW)), force=True)

    assert _sources(output) == [ROUNDUP, ROUNDUP]


def test_limit_caps_the_run(tmp_path):
    inputs = _input_file(tmp_path, ROUNDUP, OTHER)
    output = tmp_path / "out" / "extraction.jl"

    run([inputs], output, _extractor(json.dumps(ONE_REVIEW)), limit=1)

    assert _sources(output) == [ROUNDUP]


def test_one_failing_item_does_not_end_the_run(tmp_path):
    """Item 81 of 93 going bad must not throw away items 82 through 93."""
    inputs = _input_file(tmp_path, ROUNDUP, OTHER)
    output = tmp_path / "out" / "extraction.jl"
    responses = ["nope", "nope", "nope", json.dumps(ONE_REVIEW)]

    failures = run([inputs], output, _extractor(*responses))

    assert failures == 1
    assert _sources(output) == [OTHER]


def test_a_malformed_input_line_is_skipped(tmp_path):
    inputs = tmp_path / "raw.jl"
    inputs.write_text(f"not json\n{{}}\n\n{_raw_line(ROUNDUP)}", encoding="utf-8")
    output = tmp_path / "out" / "extraction.jl"

    failures = run([inputs], output, _extractor(json.dumps(ONE_REVIEW)))

    assert failures == 0
    assert _sources(output) == [ROUNDUP]


def test_finished_records_survive_an_interrupted_run(tmp_path):
    """The point of resuming: whatever completed is on disk, not in a buffer."""
    inputs = _input_file(tmp_path, ROUNDUP, OTHER)
    output = tmp_path / "out" / "extraction.jl"

    with pytest.raises(RuntimeError):
        run([inputs], output, _extractor(json.dumps(ONE_REVIEW), RuntimeError("power cut")))

    assert _sources(output) == [ROUNDUP]


def test_nothing_to_do_leaves_no_empty_file(tmp_path):
    inputs = _input_file(tmp_path)
    output = tmp_path / "out" / "extraction.jl"

    run([inputs], output, _extractor())

    assert not output.exists()


def test_read_items_spans_several_files(tmp_path):
    first = tmp_path / "a.jl"
    first.write_text(_raw_line(ROUNDUP), encoding="utf-8")
    second = tmp_path / "b.jl"
    second.write_text(_raw_line(OTHER), encoding="utf-8")

    assert [item.url for item in read_items([first, second])] == [ROUNDUP, OTHER]


def test_pending_items_is_lazy(tmp_path):
    """`--limit 1` must not parse ninety-three items to extract one."""
    items = read_items([_input_file(tmp_path, ROUNDUP, OTHER)])

    assert next(pending_items(items, [])).url == ROUNDUP
    assert [item.url for item in items] == [OTHER]


def test_extracted_sources_ignores_unreadable_lines(tmp_path):
    path = tmp_path / "extraction.jl"
    path.write_text(
        f'garbage\n"a string"\n{json.dumps({"source_url": ROUNDUP})}\n', encoding="utf-8"
    )

    assert extracted_sources(tmp_path) == {ROUNDUP}


def test_the_default_output_is_not_next_to_the_raw_items():
    """A `*.jl` glob over the results dir must not pick up extraction records."""
    output = default_output(SETTINGS)

    assert output.parent == SETTINGS.results_dir / "extraction"
    assert output.suffix == ".jl"


def test_a_missing_input_file_is_a_usage_error(tmp_path):
    with pytest.raises(SystemExit) as excinfo:
        main([str(tmp_path / "nope.jl")])

    assert excinfo.value.code == 2
