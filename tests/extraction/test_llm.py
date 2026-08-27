"""Tests for the extraction call, against a stub rather than a live model."""

import json
from dataclasses import replace
from pathlib import Path
from typing import Any, cast

import httpx2
import pytest
from openai import APITimeoutError, NotFoundError, OpenAI
from tenacity import wait_none

from finalscoring.extraction.llm import ExtractionFailed, ReviewExtractor
from finalscoring.extraction.record import prompt_sha
from finalscoring.extraction.schema import PROMPT_VERSION
from finalscoring.scraping.item import RawItem
from finalscoring.settings import Settings

SETTINGS = Settings(
    llm_base_url="http://localhost:11434/v1",
    llm_model="qwen2.5:7b",
    llm_api_key="not-needed",  # pragma: allowlist secret
    llm_timeout=5.0,
    llm_max_attempts=3,
    llm_context="html",
    scraper_user_agent="TestBot/1.0",
    scraper_delay=0.0,
    scraper_concurrency=1,
    results_dir=Path("/tmp/results"),
    jobs_dir=Path("/tmp/jobs"),
    db_path=Path("/tmp/fs.db"),
)

ONE_REVIEW = {
    "reviews": [
        {
            "game": {"title": "Catan"},
            "reviewer_name": "Jane Doe",
            "rating": 8,
            "sentiment": "positive",
            "language": "en",
        },
    ],
}


class StubClient:
    """Enough of the OpenAI client surface for the code path under test."""

    def __init__(self, *responses: str | Exception) -> None:
        self._responses = list(responses)
        self.calls: list[dict[str, Any]] = []
        self.chat = self

    @property
    def completions(self) -> StubClient:
        return self

    def create(self, **kwargs: Any) -> Any:
        self.calls.append(kwargs)
        response = self._responses.pop(0)
        if isinstance(response, Exception):
            raise response
        return _completion(response)


def _completion(content: str | None) -> Any:
    message = type("Message", (), {"content": content})()
    choice = type("Choice", (), {"message": message})()
    return type("Completion", (), {"choices": [choice]})()


def _item(**kwargs: Any) -> RawItem:
    return RawItem.model_validate(
        {
            "url": "https://example.com/roundup",
            "spider_slug": "spiel-des-jahres",
            "raw_text": "Jane Doe fand Catan gut.",
        }
        | kwargs
    )


def _extractor(
    *responses: str | Exception,
    settings: Settings = SETTINGS,
) -> tuple[ReviewExtractor, StubClient]:
    # wait_none: the backoff is real in production, but sleeping through it
    # here would add half a minute to the suite for no extra coverage.
    stub = StubClient(*responses)
    extractor = ReviewExtractor(
        settings=settings,
        client=cast("OpenAI", stub),
        wait=wait_none(),
    )
    return extractor, stub


def test_a_valid_response_becomes_a_record():
    extractor, _stub = _extractor(json.dumps(ONE_REVIEW))

    record = extractor.extract(_item())

    assert record.source_url == "https://example.com/roundup"
    assert len(record.result.reviews) == 1
    assert record.result.reviews[0].game.title == "Catan"


def test_the_record_is_stamped_with_model_and_prompt():
    """Provenance comes from the caller, never from the model's own output."""
    extractor, _stub = _extractor(json.dumps(ONE_REVIEW))

    record = extractor.extract(_item())

    assert record.model == "qwen2.5:7b"
    assert record.prompt_version == PROMPT_VERSION
    assert record.prompt_sha == prompt_sha(extractor.prompt)


def test_the_prompt_and_the_article_are_sent_separately():
    """The article is user content; the instructions are not."""
    extractor, stub = _extractor(json.dumps(ONE_REVIEW))

    extractor.extract(_item(raw_text="Ein wirklich gutes Spiel."))

    (call,) = stub.calls
    system, user = call["messages"]
    assert system["role"] == "system"
    assert system["content"] == extractor.prompt
    assert user["role"] == "user"
    assert "Ein wirklich gutes Spiel." in user["content"]


def test_the_page_metadata_is_sent_with_the_article():
    """The model was being asked to name outlets without the page's site name."""
    extractor, stub = _extractor(json.dumps(ONE_REVIEW))

    extractor.extract(_item(og_site_name="Spiel des Jahres", title="Kritikenrundschau"))

    (call,) = stub.calls
    user = call["messages"][1]["content"]
    assert "site: Spiel des Jahres" in user
    assert "title: Kritikenrundschau" in user


def test_the_context_mode_is_configurable():
    """So the two can be measured against each other on one corpus."""
    html = "<p>Ein <strong>wirklich</strong> gutes Spiel.</p>"
    as_text, stub_text = _extractor(
        json.dumps(ONE_REVIEW), settings=replace(SETTINGS, llm_context="text")
    )
    as_html, stub_html = _extractor(json.dumps(ONE_REVIEW))

    as_text.extract(_item(raw_html=html))
    as_html.extract(_item(raw_html=html))

    assert "<strong>" not in stub_text.calls[0]["messages"][1]["content"]
    assert "<strong>" in stub_html.calls[0]["messages"][1]["content"]


def test_a_schema_is_requested():
    extractor, stub = _extractor(json.dumps(ONE_REVIEW))

    extractor.extract(_item())

    (call,) = stub.calls
    assert call["response_format"]["type"] == "json_schema"


def test_malformed_json_is_retried():
    """A weak server is a retry problem, not a data-quality problem."""
    extractor, stub = _extractor("not json at all", json.dumps(ONE_REVIEW))

    record = extractor.extract(_item())

    assert len(record.result.reviews) == 1
    assert len(stub.calls) == 2


def test_a_response_failing_validation_is_retried():
    """rating=99 is out of range, so the first answer must not be accepted."""
    bad = {"reviews": [dict(ONE_REVIEW["reviews"][0], rating=99)]}
    extractor, stub = _extractor(json.dumps(bad), json.dumps(ONE_REVIEW))

    record = extractor.extract(_item())

    assert record.result.reviews[0].rating == 8
    assert len(stub.calls) == 2


def test_an_empty_response_is_retried():
    extractor, _stub = _extractor("", json.dumps(ONE_REVIEW))

    record = extractor.extract(_item())

    assert len(record.result.reviews) == 1


def test_giving_up_raises_extraction_failed():
    extractor, stub = _extractor("nope", "still nope", "nope again")

    with pytest.raises(ExtractionFailed) as excinfo:
        extractor.extract(_item())

    assert "https://example.com/roundup" in str(excinfo.value)
    assert len(stub.calls) == 3


def test_attempts_are_configurable():
    settings = replace(SETTINGS, llm_max_attempts=2)
    extractor, stub = _extractor("no", "no", "no", settings=settings)

    with pytest.raises(ExtractionFailed):
        extractor.extract(_item())

    assert len(stub.calls) == 2


def test_an_empty_review_list_is_a_valid_answer():
    """A page with no reviews on it is a normal outcome, not a failure."""
    extractor, _stub = _extractor(json.dumps({"reviews": []}))

    record = extractor.extract(_item())

    assert record.result.reviews == []


def _not_found() -> NotFoundError:
    request = httpx2.Request("POST", "http://localhost:11434/v1/chat/completions")
    response = httpx2.Response(404, request=request, json={"error": {"message": "no model"}})
    return NotFoundError("model not found", response=response, body=None)


def test_a_timeout_is_retried():
    """Slow once is not the same as broken."""
    extractor, stub = _extractor(
        APITimeoutError(request=httpx2.Request("POST", "http://localhost/")),
        json.dumps(ONE_REVIEW),
    )

    record = extractor.extract(_item())

    assert len(record.result.reviews) == 1
    assert len(stub.calls) == 2


def test_a_missing_model_fails_without_retrying():
    """Retrying a 404 spends three timeouts to learn what the first one said."""
    extractor, stub = _extractor(_not_found(), _not_found(), _not_found())

    with pytest.raises(ExtractionFailed):
        extractor.extract(_item())

    assert len(stub.calls) == 1


def test_sdk_errors_surface_as_extraction_failed():
    """Callers handle one exception type, not the SDK's hierarchy."""
    extractor, _stub = _extractor(_not_found())

    with pytest.raises(ExtractionFailed) as excinfo:
        extractor.extract(_item())

    assert "https://example.com/roundup" in str(excinfo.value)
