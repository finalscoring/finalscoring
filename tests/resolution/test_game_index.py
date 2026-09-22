"""Tests for the BGG game data index (D1)."""

from pathlib import Path

from finalscoring.resolution.game_index import GameIndex, normalize_title

FIXTURE = Path(__file__).parent / "bgg_GameItem_fixture.jl"


def test_load_indexes_by_id():
    index = GameIndex.load(FIXTURE)
    assert index.by_id[400314].name == "Apiary"
    assert index.by_id[400314].designers == ["Connie Vogelmann"]


def test_load_strips_designer_id_suffix():
    index = GameIndex.load(FIXTURE)
    assert index.by_id[174430].designers == ["Isaac Childres"]
    assert index.by_id[174430].publishers == ["Cephalofair Games"]


def test_candidates_dedupes_when_alt_name_repeats_name():
    # Real bgg_GameItem.jl records list the canonical name again inside
    # alt_name; a game must still show up once, not once per repeated title.
    index = GameIndex.load(FIXTURE)
    assert [c.bgg_id for c in index.candidates("Gloomhaven")] == [174430]


def test_candidates_matches_alt_name():
    index = GameIndex.load(FIXTURE)
    # German edition title, only present in alt_name — extraction/schema.py's
    # motivating example for why title alone must not be the sole key.
    candidates = index.candidates("Astrobienen")
    assert [c.bgg_id for c in candidates] == [400314]


def test_candidates_is_case_and_accent_insensitive():
    index = GameIndex.load(FIXTURE)
    assert [c.bgg_id for c in index.candidates("astrobienen")] == [400314]
    assert [c.bgg_id for c in index.candidates("VCELIN")] == [400314]


def test_candidates_returns_all_title_collisions():
    index = GameIndex.load(FIXTURE)
    assert {c.bgg_id for c in index.candidates("Coup")} == {131357, 500002, 500003}


def test_candidates_empty_for_unknown_title():
    index = GameIndex.load(FIXTURE)
    assert index.candidates("Not A Real Game Title") == []


def test_normalize_title_folds_accents_and_case():
    assert normalize_title("Die Mächer") == "die macher"
    assert normalize_title("Coup") == normalize_title("  COUP  ")
