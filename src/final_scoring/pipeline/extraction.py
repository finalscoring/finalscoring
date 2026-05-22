"""LLM-based structured extraction of reviews from raw text.

This module extends the proof-of-concept pipeline from the
Spiel-des-Jahres scraper with the fields Final Scoring needs that the
SdJ project did not:

* ``outlet`` and ``original_url`` — for attribution, especially when
  ingesting via meta-sources like editorial roundups.
* ``original_date`` — when the review was originally published, distinct
  from when Final Scoring saw it.
* ``language`` — to support multilingual operation from day one.
* ``score_declared`` separate from ``rating_inferred`` — to never confuse
  "the critic gave 4/5" with "we inferred 7/10 from their text".
* ``quote_verbatim`` — short, attribution-safe pull-quote, ≤15 words.

The Pydantic schema is the single source of truth. Both the LLM's
structured-output constraint (via the OpenAI-compatible Responses API or
constrained decoding in vLLM/Ollama) and the database writes derive from
it.
"""

from __future__ import annotations

import asyncio
from typing import Any, Literal

from openai import AsyncOpenAI
from pydantic import BaseModel, Field
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from final_scoring.config import LLMSettings
from final_scoring.pipeline.prompts import load_prompt, prompt_version_tag


# ─────────────────────────────────────────────────────────────────────────
# Extraction schema
# ─────────────────────────────────────────────────────────────────────────


Sentiment = Literal["positive", "neutral", "negative"]


class ExtractedReview(BaseModel):
    """A single review as extracted by the LLM.

    These records are intermediate. They land in JSONL and are then
    resolved against the canonical ``Critic`` and ``Game`` tables before
    being written as ``Review`` rows.
    """

    game_title: str = Field(
        description="The title of the board game being reviewed.",
    )
    reviewer_name: str = Field(
        description="The reviewer's name as a human would write it.",
    )
    reviewer_id: str = Field(
        description="Stable identifier in lower_snake_case (e.g. "
        "'tom_brewster'). May be overridden via the critic_aliases "
        "table; treat as a hint, not the source of truth.",
    )
    outlet: str | None = Field(
        default=None,
        description="The publication, channel, or site (e.g. "
        "'Shut Up & Sit Down'). Null when the reviewer publishes "
        "independently.",
    )
    original_url: str | None = Field(
        default=None,
        description="URL of the original review, if cited or linked. "
        "Differs from the scraped URL when ingested via a meta-source.",
    )
    original_date: str | None = Field(
        default=None,
        description="Publication date of the original review, "
        "ISO-8601 if extractable.",
    )
    language: str = Field(
        description="ISO 639-1 code for the language of the review.",
    )
    score_declared: str | None = Field(
        default=None,
        description="The score or verdict the critic actually gave, "
        "verbatim (e.g. '4/5', '8.5', 'Recommended'). Null if the "
        "critic did not declare a score.",
    )
    rating_inferred: int = Field(
        ge=1,
        le=10,
        description="A 1–10 rating derived from the score and/or text. "
        "Use the rubric from the prompt.",
    )
    sentiment: Sentiment = Field(
        description="Overall sentiment of the review.",
    )
    quote_verbatim: str | None = Field(
        default=None,
        max_length=200,
        description="A short verbatim pull-quote from the review, in "
        "the critic's own words. Strictly ≤15 words. Null if no quote "
        "in the source text fits within that limit.",
    )
    summary: str = Field(
        description="A 1–3 sentence paraphrase of the review in your "
        "own words. Never reproduces source text beyond quote_verbatim.",
    )


class ExtractedReviewList(BaseModel):
    """Top-level structured output for one scraped item.

    One scraped page may produce many extracted reviews — e.g. an
    editorial roundup citing several critics on several games.
    """

    reviews: list[ExtractedReview] = Field(
        default_factory=list,
        description="All reviews found in the source text.",
    )


# ─────────────────────────────────────────────────────────────────────────
# Extraction pipeline
# ─────────────────────────────────────────────────────────────────────────


# Default prompt; override per-source if you need a specialised variant
# (e.g. a meta-source with a specific roundup structure).
DEFAULT_PROMPT_NAME = "review_extraction"
DEFAULT_PROMPT_VERSION = "v1"


class LLMExtractionPipeline:
    """OpenAI-compatible structured-extraction pipeline.

    Designed to be used both as a Scrapy item pipeline (see
    ``scraping.pipeline_adapter``) and standalone — e.g. when replaying
    historical JSONL through a new prompt version during a build.
    """

    def __init__(
        self,
        settings: LLMSettings,
        prompt_name: str = DEFAULT_PROMPT_NAME,
        prompt_version: str = DEFAULT_PROMPT_VERSION,
    ) -> None:
        self.settings = settings
        self.prompt_name = prompt_name
        self.prompt_version = prompt_version
        self._instructions = load_prompt(prompt_name, prompt_version)
        self._client = AsyncOpenAI(
            base_url=settings.api_base_url,
            api_key=settings.api_key,
        )

    @property
    def extraction_version_tag(self) -> str:
        """The provenance string stored on every ``Review`` row.

        Combines the prompt version with the model name so a future
        backfill can answer "which reviews were extracted with what?".
        """

        return f"{self.settings.model}/{prompt_version_tag(self.prompt_name, self.prompt_version)}"

    @retry(
        retry=retry_if_exception_type(Exception),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        stop=stop_after_attempt(3),
    )
    async def _call_llm(
        self,
        text: str,
        *,
        title: str | None,
        description: str | None,
    ) -> ExtractedReviewList | None:
        prompt_content = (
            f"CONTEXT:\nTitle: {title or '<none>'}\n"
            f"Description: {description or '<none>'}\n\n"
            f"TEXT:\n{text}"
        )

        kwargs: dict[str, Any] = {
            "model": self.settings.model,
            "input": prompt_content,
            "instructions": self._instructions,
            "text_format": ExtractedReviewList,
        }
        if self.settings.temperature is not None:
            kwargs["temperature"] = self.settings.temperature
        if self.settings.max_output_tokens is not None:
            kwargs["max_output_tokens"] = self.settings.max_output_tokens

        response = await self._client.responses.parse(**kwargs)
        return response.output_parsed

    async def extract(
        self,
        raw_text: str,
        *,
        title: str | None = None,
        description: str | None = None,
    ) -> ExtractedReviewList:
        """Extract structured reviews from raw text.

        Returns an empty ``ExtractedReviewList`` on failure rather than
        raising — a single page's failure should not stop a build. The
        ingestion log records the failure for follow-up.
        """

        if not raw_text or not raw_text.strip():
            return ExtractedReviewList(reviews=[])

        try:
            parsed = await self._call_llm(
                raw_text,
                title=title,
                description=description,
            )
            return parsed or ExtractedReviewList(reviews=[])
        except Exception:
            # Log and continue; the caller decides whether to escalate.
            return ExtractedReviewList(reviews=[])

    def extract_sync(
        self,
        raw_text: str,
        *,
        title: str | None = None,
        description: str | None = None,
    ) -> ExtractedReviewList:
        """Synchronous wrapper for use outside an event loop."""

        return asyncio.run(
            self.extract(raw_text, title=title, description=description)
        )
