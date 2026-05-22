"""Public re-exports for all SQLModel table models."""

from finalscoring.models.critic import Critic as Critic
from finalscoring.models.game import Game as Game
from finalscoring.models.outlet import Outlet as Outlet

__all__ = ["Critic", "Game", "Outlet"]
