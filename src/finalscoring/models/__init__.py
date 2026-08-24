"""Public re-exports for the SQLModel table models, plus the vocabulary the
ingestion and scoring layers share with them — the enums and the quote cap.
Import those from here rather than from the module that happens to define
them, so they can be moved without touching callers.

Construction note: SQLModel table models bypass Pydantic's __init__, so field
validators (ge, le, gt, @field_validator) only fire when using model_validate():

    review = Review.model_validate(scraped_dict)   # validators run ✓
    review = Review(**scraped_dict)                 # validators skipped ✗

Always use model_validate() in ingestion and scoring code.
"""

from finalscoring.models.critic import Critic
from finalscoring.models.enums import Medium, Sentiment
from finalscoring.models.game import Game
from finalscoring.models.game_aggregate import GameAggregate
from finalscoring.models.outlet import Outlet
from finalscoring.models.review import QUOTE_MAX_LENGTH, Review

__all__ = [
    "QUOTE_MAX_LENGTH",
    "Critic",
    "Game",
    "GameAggregate",
    "Medium",
    "Outlet",
    "Review",
    "Sentiment",
]
