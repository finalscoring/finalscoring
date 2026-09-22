"""Game-title -> canonical BGG id resolution (Phase D, D1)."""

from finalscoring.resolution.game_index import BggGame, GameIndex, normalize_title
from finalscoring.resolution.resolve import Resolution, ResolutionReason, resolve_game

__all__ = [
    "BggGame",
    "GameIndex",
    "Resolution",
    "ResolutionReason",
    "normalize_title",
    "resolve_game",
]
