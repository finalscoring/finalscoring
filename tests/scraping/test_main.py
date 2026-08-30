"""Tests for the hand-run entry point."""

import pytest

from finalscoring.scraping.__main__ import SPIDERS, main, spider_args


def test_spider_args_parses_key_value_pairs():
    assert spider_args(["files=a.jl"]) == {"files": "a.jl"}
    assert spider_args(["-a", "files=a.jl", "-a", "url_column=link"]) == {
        "files": "a.jl",
        "url_column": "link",
    }
    assert spider_args([]) == {}


def test_spider_args_keeps_an_equals_sign_in_the_value():
    assert spider_args(["files=a.jl,b.jl", "note=x=y"]) == {"files": "a.jl,b.jl", "note": "x=y"}


def test_spider_args_rejects_a_bare_token():
    with pytest.raises(ValueError, match="key=value"):
        spider_args(["files"])


def test_luding_is_registered():
    assert "luding" in SPIDERS


@pytest.mark.parametrize("argv", [[], ["not-a-spider"], ["luding", "files"]])
def test_main_rejects_bad_invocation(argv):
    assert main(argv) == 2
