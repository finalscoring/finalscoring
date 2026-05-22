"""LLM extraction pipeline.

Takes raw scraped review payloads and produces structured ``ExtractedReview``
records validated against a Pydantic schema. Uses an OpenAI-compatible
client so it can talk to a local model (vLLM, Ollama) or a hosted endpoint
interchangeably.
"""

from final_scoring.pipeline.extraction import (
    ExtractedReview,
    ExtractedReviewList,
    LLMExtractionPipeline,
)
from final_scoring.pipeline.prompts import load_prompt

__all__ = [
    "ExtractedReview",
    "ExtractedReviewList",
    "LLMExtractionPipeline",
    "load_prompt",
]
