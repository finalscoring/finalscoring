"""Database schema as SQLModel definitions.

The schema is materialized at build time into a SQLite file that is then
baked into the Docker image. There are no migrations in the traditional
sense — every deploy creates a fresh database from sources.

For the rationale behind this architecture, see ``docs/architecture.md``.
"""

from final_scoring.schema.models import (
    Aggregate,
    Critic,
    CriticAlias,
    Game,
    GameMatchOverride,
    Review,
    SourceRun,
)

__all__ = [
    "Aggregate",
    "Critic",
    "CriticAlias",
    "Game",
    "GameMatchOverride",
    "Review",
    "SourceRun",
]
