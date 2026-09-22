"""Tests for the title -> BGG id resolution cascade (D1)."""

from pathlib import Path

import pytest

from finalscoring.extraction.schema import ExtractedGame
from finalscoring.resolution.game_index import GameIndex
from finalscoring.resolution.resolve import ResolutionReason, resolve_game

FIXTURE = Path(__file__).parent / "bgg_GameItem_fixture.jl"


@pytest.fixture
def index():
    return GameIndex.load(FIXTURE)


def test_bgg_url_settles_it_outright(index):
    # A title that wouldn't itself match anything in the index — the url wins.
    game = ExtractedGame(
        title="Not The Real Title", bgg_url="https://boardgamegeek.com/boardgame/174430/gloomhaven"
    )
    result = resolve_game(game, index)
    assert result.bgg_id == 174430
    assert result.reason is ResolutionReason.bgg_url
    assert result.candidate_count == 0


def test_bgg_url_wins_over_a_conflicting_title(index):
    game = ExtractedGame(
        title="Apiary", bgg_url="https://boardgamegeek.com/boardgame/174430/gloomhaven"
    )
    result = resolve_game(game, index)
    assert result.bgg_id == 174430
    assert result.reason is ResolutionReason.bgg_url


def test_bgg_url_trusted_even_when_id_not_in_index(index):
    # A stale/incomplete local snapshot must not downgrade a good url match.
    game = ExtractedGame(title="Some Game", bgg_url="https://boardgamegeek.com/boardgame/9999999")
    result = resolve_game(game, index)
    assert result.bgg_id == 9999999
    assert result.reason is ResolutionReason.bgg_url


def test_unique_title_resolves(index):
    game = ExtractedGame(title="Apiary")
    result = resolve_game(game, index)
    assert result.bgg_id == 400314
    assert result.reason is ResolutionReason.unique_title


def test_alt_name_resolves_unique_title(index):
    game = ExtractedGame(title="Astrobienen")
    result = resolve_game(game, index)
    assert result.bgg_id == 400314
    assert result.reason is ResolutionReason.unique_title


def test_ambiguous_title_disambiguated_by_year(index):
    game = ExtractedGame(title="Coup", year_published=2020)
    result = resolve_game(game, index)
    assert result.bgg_id == 500003
    assert result.reason is ResolutionReason.disambiguated_by_year


def test_ambiguous_title_and_year_disambiguated_by_designer(index):
    game = ExtractedGame(title="Coup", year_published=2012, designers=["Rikki Tahta"])
    result = resolve_game(game, index)
    assert result.bgg_id == 131357
    assert result.reason is ResolutionReason.disambiguated_by_credits


def test_ambiguous_title_stays_unresolved_without_disambiguators(index):
    game = ExtractedGame(title="Coup")
    result = resolve_game(game, index)
    assert result.bgg_id is None
    assert result.reason is ResolutionReason.unresolved_ambiguous
    assert result.candidate_count == 3


def test_unknown_title_is_unresolved(index):
    game = ExtractedGame(title="Not A Real Game Title")
    result = resolve_game(game, index)
    assert result.bgg_id is None
    assert result.reason is ResolutionReason.unresolved_no_candidates
