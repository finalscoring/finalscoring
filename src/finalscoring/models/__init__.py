"""Public re-exports for all SQLModel table models.

Construction note: SQLModel table models bypass Pydantic's __init__, so field
validators (ge, le, gt, @field_validator) only fire when using model_validate():

    review = Review.model_validate(scraped_dict)   # validators run ✓
    review = Review(**scraped_dict)                 # validators skipped ✗

Always use model_validate() in ingestion and scoring code.
"""

from finalscoring.models.critic import Critic as Critic
from finalscoring.models.game import Game as Game
from finalscoring.models.game_aggregate import GameAggregate as GameAggregate
from finalscoring.models.outlet import Outlet as Outlet
from finalscoring.models.review import Review as Review

__all__ = ["Critic", "Game", "GameAggregate", "Outlet", "Review"]
