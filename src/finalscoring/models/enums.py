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


class RatingSystem(StrEnum):
    """Which of a source's rating mechanisms a `SourceRating` came from.

    One page can state several — games-we-play shows a primary graphic, a
    schema.org number and a signature line at once — so the load step needs to
    know which is which before it decides one is the declared score.
    """

    editorial = "editorial"  # the source's own primary score
    overall = "overall"  # a score rolled up across sub-scores
    axis = "axis"  # one sub-dimension of a multi-axis score
    star_label = "star_label"  # a star rating, often paired with a word
    schema_org = "schema_org"  # schema.org / JSON-LD Rating microdata
    signature = "signature"  # a scored sign-off line
