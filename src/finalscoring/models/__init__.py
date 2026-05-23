"""Public re-exports for all SQLModel table models."""

from finalscoring.models.critic import Critic as Critic
from finalscoring.models.game import Game as Game
from finalscoring.models.game_aggregate import GameAggregate as GameAggregate
from finalscoring.models.outlet import Outlet as Outlet
from finalscoring.models.review import Review as Review

__all__ = ["Critic", "Game", "GameAggregate", "Outlet", "Review"]
