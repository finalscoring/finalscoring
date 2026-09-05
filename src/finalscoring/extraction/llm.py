"""The extraction call: a raw item in, a validated ExtractionRecord out.

Written against /v1/chat/completions rather than /v1/responses because every
OpenAI-compatible server implements it, which is what keeps the model and the
machine a config choice rather than a code change.

The JSON schema is sent with the request, but pydantic validation is the
actual guarantee: a server with weak or absent constrained decoding degrades
into more retries, never into silently wrong data.
"""

import json
import logging
import re
from typing import Any

from openai import (
    APIConnectionError,
    InternalServerError,
    OpenAI,
    OpenAIError,
    RateLimitError,
)
from pydantic import ValidationError
from tenacity import (
    RetryError,
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)
from tenacity.wait import wait_base

from finalscoring.extraction.context import build_context
from finalscoring.extraction.record import ExtractionRecord, prompt_sha
from finalscoring.extraction.schema import PROMPT, PROMPT_VERSION, ExtractionResult
from finalscoring.scraping.item import RawItem
from finalscoring.settings import Settings, load_settings

LOGGER = logging.getLogger(__name__)

# Not strict: pydantic's schema uses defaults and anyOf-null for optional
# fields, which strict mode rejects outright. The schema is guidance here;
# ExtractionResult.model_validate is what actually enforces the shape.
_RESPONSE_FORMAT: dict[str, Any] = {
    "type": "json_schema",
    "json_schema": {
        "name": "extraction_result",
        "strict": False,
        "schema": ExtractionResult.model_json_schema(),
    },
}


# Worth another attempt: a bad shape, an unreadable answer, a server that was
# briefly unreachable or busy. A 404 for a missing model or a 401 is not here —
# retrying those just wastes three timeouts on a certainty.
_RETRYABLE = (
    ValidationError,
    ValueError,
    APIConnectionError,  # includes APITimeoutError
    RateLimitError,
    InternalServerError,
    OSError,
)


class ExtractionFailed(Exception):
    """Extraction did not produce a validated result."""


# Curly/straight quotes, the dash variants and nbsp all vary between the page
# and what a model echoes back; none of them change whether a quote is verbatim.
_QUOTE_NOISE = str.maketrans(
    {
        "\u2019": "'",
        "\u2018": "'",  # right / left single quote
        "\u201c": '"',
        "\u201d": '"',
        "\u201e": '"',  # left / right / low double quote
        "\u00ab": '"',
        "\u00bb": '"',  # guillemets
        "\u2013": "-",
        "\u2014": "-",  # en / em dash
        "\u00a0": " ",  # nbsp
    }
)
_WHITESPACE = re.compile(r"\s+")
_MARKUP = re.compile(r"<[^>]+>")


def _normalise_quote(text: str) -> str:
    # Markup is stripped so a prose quote still matches when the context it is
    # checked against kept its tags ("Vorgänger <a href=…>Kardinal</a> …").
    # Only the surrounding quote marks are removed — the prompt says not to
    # include them, but a model that does should not fail the check for it.
    bare = _WHITESPACE.sub(" ", _MARKUP.sub("", text).translate(_QUOTE_NOISE))
    return bare.strip().strip("'\"").strip().casefold()


def _drop_unverbatim_quotes(result: ExtractionResult, context: str, url: str) -> None:
    """Null any quote that is not a substring of the text the model was shown.

    The prompt asks for a character-for-character copy; smaller models paraphrase
    ("Das Spiel packt mich" -> "Es packt mich") or, worse, translate a fragment.
    A quote is optional, so a bad one is dropped rather than retried — losing the
    whole page over one field is the worse trade.
    """
    haystack = _normalise_quote(context)
    for review in result.reviews:
        if review.quote and _normalise_quote(review.quote) not in haystack:
            LOGGER.warning("discarding non-verbatim quote for %s: %r", url, review.quote)
            review.quote = None


class ReviewExtractor:
    def __init__(
        self,
        settings: Settings | None = None,
        client: OpenAI | None = None,
        wait: wait_base | None = None,
    ) -> None:
        self.settings = settings if settings is not None else load_settings()
        self.client = client if client is not None else self._build_client(self.settings)
        self.wait = wait if wait is not None else wait_exponential(multiplier=1, min=2, max=30)
        self.prompt = PROMPT
        self.prompt_version = PROMPT_VERSION
        self.prompt_sha = prompt_sha(self.prompt)

    @staticmethod
    def _build_client(settings: Settings) -> OpenAI:
        return OpenAI(
            base_url=settings.llm_base_url,
            api_key=settings.llm_api_key,
            timeout=settings.llm_timeout,
            max_retries=0,  # tenacity owns retrying, so it happens in one place
        )

    def extract(self, item: RawItem) -> ExtractionRecord:
        """Extract every review in one raw item. Raises ExtractionFailed."""
        try:
            context = build_context(item, markup=self.settings.llm_context == "html")
            result = self._call_with_retries(context)
            _drop_unverbatim_quotes(result, context, item.url)
        except RetryError as exc:
            message = (
                f"extraction failed for {item.url} after {self.settings.llm_max_attempts} attempts"
            )
            raise ExtractionFailed(message) from exc.last_attempt.exception()
        except OpenAIError as exc:
            # Nothing retryable — a missing model, a rejected key, a malformed
            # request. Still ours to report, not the SDK's to raise at callers.
            raise ExtractionFailed(f"extraction failed for {item.url}: {exc}") from exc

        return ExtractionRecord(
            source_url=item.url,
            model=self.settings.llm_model,
            prompt_version=self.prompt_version,
            prompt_sha=self.prompt_sha,
            result=result,
        )

    def _call_with_retries(self, context: str) -> ExtractionResult:
        retrying = retry(
            retry=retry_if_exception_type(_RETRYABLE),
            wait=self.wait,
            stop=stop_after_attempt(self.settings.llm_max_attempts),
            reraise=False,
        )
        return retrying(self._call)(context)

    def _call(self, context: str) -> ExtractionResult:
        completion = self.client.chat.completions.create(
            model=self.settings.llm_model,
            messages=[
                {"role": "system", "content": self.prompt},
                {"role": "user", "content": context},
            ],
            response_format=_RESPONSE_FORMAT,  # ty: ignore[invalid-argument-type]
        )
        content = completion.choices[0].message.content
        if not content:
            raise ValueError("model returned an empty response")

        return ExtractionResult.model_validate(json.loads(content))
