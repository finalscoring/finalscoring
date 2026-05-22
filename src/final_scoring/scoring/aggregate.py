"""Compute per-game aggregates from normalized reviews.

Entry point for the scoring stage of a build. Reads ``Review`` rows,
applies per-critic z-score normalization, computes tier-weighted
aggregates with bootstrap CIs, and writes ``Aggregate`` rows.
"""

from __future__ import annotations

import json
import logging
from collections import defaultdict
from pathlib import Path

from sqlmodel import Session, delete, select

from final_scoring.schema import Aggregate, Critic, Review
from final_scoring.schema.init_db import make_engine
from final_scoring.scoring.confidence import bootstrap_ci, weighted_mean
from final_scoring.scoring.config import ScoringConfig, default_scoring_config
from final_scoring.scoring.normalize import (
    apply_z_score,
    compute_critic_stats,
    global_score_stats,
    raw_to_scale,
)

logger = logging.getLogger(__name__)


def compute_aggregates(
    db_path: Path,
    config: ScoringConfig | None = None,
) -> int:
    """Recompute every game's aggregate from current review data.

    Args:
        db_path: Path to the SQLite database to read and write.
        config: Optional scoring config override. Defaults to
            :func:`default_scoring_config`.

    Returns:
        Number of aggregates written.
    """

    cfg = config or default_scoring_config()
    engine = make_engine(db_path)

    with Session(engine) as session:
        # 1. Load all reviews and the critic table.
        reviews = list(session.exec(select(Review)).all())
        critics = {c.id: c for c in session.exec(select(Critic)).all()}

        if not reviews:
            logger.info("No reviews in database; nothing to aggregate.")
            return 0

        # 2. Map each review to its base 0–100 score from rating_inferred.
        #    score_normalized is computed below and then written back to
        #    the review row.
        base_scores: dict[int, float] = {}
        for r in reviews:
            assert r.id is not None
            base_scores[r.id] = raw_to_scale(r.rating_inferred)

        # 3. Per-critic stats for z-score normalization.
        per_critic: dict[int, list[float]] = defaultdict(list)
        for r in reviews:
            assert r.id is not None
            per_critic[r.critic_id].append(base_scores[r.id])

        critic_stats = {
            critic_id: compute_critic_stats(scores)
            for critic_id, scores in per_critic.items()
            if len(scores) >= cfg.min_reviews_for_z_score
        }

        # Critics below the z-score threshold use the global stats as
        # their reference distribution.
        global_stats = global_score_stats(list(base_scores.values()))

        # 4. Normalize each review and persist to the row.
        for r in reviews:
            assert r.id is not None
            normalized = apply_z_score(
                base_scores[r.id],
                critic_stats.get(r.critic_id),
                global_stats,
            )
            r.score_normalized = normalized
            session.add(r)

        session.commit()

        # 5. Group reviews by game, compute aggregate + CI, write
        #    Aggregate rows. Skip games below the min-reviews threshold.
        by_game: dict[int, list[Review]] = defaultdict(list)
        for r in reviews:
            by_game[r.game_bgg_id].append(r)

        # Drop any pre-existing aggregates; we rebuild fully each time.
        session.exec(delete(Aggregate))  # type: ignore[call-overload]

        written = 0
        for game_id, game_reviews in by_game.items():
            if len(game_reviews) < cfg.min_reviews_for_aggregate:
                continue

            scores = [
                r.score_normalized
                for r in game_reviews
                if r.score_normalized is not None
            ]
            weights = [
                _critic_weight(critics, r.critic_id, cfg)
                for r in game_reviews
                if r.score_normalized is not None
            ]
            if not scores:
                continue

            import numpy as np

            score = weighted_mean(
                np.asarray(scores), np.asarray(weights)
            )
            ci_low, ci_high = bootstrap_ci(
                scores,
                weights,
                iterations=cfg.bootstrap_iterations,
                percentile_low=cfg.ci_percentile_low,
                percentile_high=cfg.ci_percentile_high,
            )

            session.add(
                Aggregate(
                    game_bgg_id=game_id,
                    score=score,
                    score_ci_low=ci_low,
                    score_ci_high=ci_high,
                    review_count=len(game_reviews),
                    distribution_json=json.dumps(sorted(scores)),
                    methodology_version=cfg.version,
                )
            )
            written += 1

        session.commit()
        logger.info("Wrote %d aggregates.", written)
        return written


def _critic_weight(
    critics: dict[int | None, Critic],
    critic_id: int,
    cfg: ScoringConfig,
) -> float:
    """Return the source-tier weight for a critic, with validation."""

    critic = critics.get(critic_id)
    if critic is None:
        # Should not happen if the database is consistent.
        logger.warning("Review references unknown critic_id=%d", critic_id)
        return 0.0
    if critic.source_tier not in cfg.valid_tiers:
        raise ValueError(
            f"Critic {critic.slug} has invalid source_tier "
            f"{critic.source_tier}; allowed: {cfg.valid_tiers}"
        )
    return critic.source_tier
