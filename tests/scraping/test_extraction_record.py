"""Tests for the extraction output envelope."""

from datetime import UTC
from typing import Any

from finalscoring.scraping.extract import PROMPT_V1, ExtractedReview, ExtractionResult
from finalscoring.scraping.extraction_record import ExtractionRecord, prompt_sha


def _record(**kwargs: Any) -> ExtractionRecord:
    return ExtractionRecord.model_validate(
        {
            "source_url": "https://example.com/a",
            "model": "qwen2.5:7b",
            "prompt_version": "extract_v1",
            "prompt_sha": prompt_sha(PROMPT_V1),
            "result": ExtractionResult(
                reviews=[
                    ExtractedReview(
                        game_title="Catan",
                        reviewer_name="Jane Doe",
                        rating=8,
                        sentiment="positive",
                        language="en",
                    ),
                ],
            ),
        }
        | kwargs
    )


def test_prompt_sha_is_deterministic():
    assert prompt_sha("hello") == prompt_sha("hello")


def test_prompt_sha_changes_with_the_prompt():
    """This is the whole point — an in-place edit must not go unnoticed."""
    assert prompt_sha("hello") != prompt_sha("hello!")


def test_prompt_sha_is_a_short_hex_string():
    assert len(prompt_sha(PROMPT_V1)) == 12
    assert all(c in "0123456789abcdef" for c in prompt_sha(PROMPT_V1))


def test_extracted_at_defaults_to_utc_now():
    assert _record().extracted_at.tzinfo == UTC


def test_record_round_trips_through_json():
    record = _record()

    restored = ExtractionRecord.model_validate_json(record.model_dump_json())

    assert restored == record


def test_record_carries_the_model_and_prompt_that_produced_it():
    record = _record(model="qwen2.5:7b", prompt_version="extract_v1")

    assert record.model == "qwen2.5:7b"
    assert record.prompt_version == "extract_v1"
    assert record.prompt_sha == prompt_sha(PROMPT_V1)
