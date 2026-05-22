"""Score normalization, aggregation, and confidence intervals.

The scoring layer is the only place where critical reception is turned
into the numbers shown on game pages. It runs at build time, never at
request time. All inputs (per-critic z-scores, source tier weights) are
public and live in this repository.

The three layers:

1. :mod:`final_scoring.scoring.normalize` — per-critic z-score
   adjustment of raw scores onto a common 0–100 scale.
2. :mod:`final_scoring.scoring.aggregate` — tier-weighted aggregation
   into per-game scores.
3. :mod:`final_scoring.scoring.confidence` — bootstrap confidence
   intervals reflecting reviewer agreement and sample size.

The combined entry point :func:`compute_aggregates` runs all three and
writes ``Aggregate`` rows.
"""

from final_scoring.scoring.aggregate import compute_aggregates
from final_scoring.scoring.config import ScoringConfig, default_scoring_config

__all__ = ["ScoringConfig", "compute_aggregates", "default_scoring_config"]
