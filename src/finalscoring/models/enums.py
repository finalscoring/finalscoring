"""Vocabulary shared by the tables and the ingestion schema.

These live here rather than on the table that first needed them: a medium
describes a review, not the outlet that published it, and both the extraction
schema and the tables have to agree on the values.
"""

from enum import StrEnum


class Medium(StrEnum):
    text = "text"
    video = "video"
    podcast = "podcast"
    print_ = "print"
    social = "social"


class Sentiment(StrEnum):
    negative = "negative"
    mixed_negative = "mixed_negative"
    neutral = "neutral"
    mixed_positive = "mixed_positive"
    positive = "positive"
