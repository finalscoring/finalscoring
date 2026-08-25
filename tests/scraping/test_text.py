"""Tests for HTML to plain-text conversion."""

from finalscoring.scraping.text import html_to_text


def test_blocks_are_separated():
    """Without breaks the last word of one block fuses to the first of the next."""
    text = html_to_text("<p>Erster Absatz.</p><p>Zweiter Absatz.</p>")

    assert "Absatz.Zweiter" not in text
    assert text.splitlines() == ["Erster Absatz.", "Zweiter Absatz."]


def test_inline_markup_does_not_split_a_sentence():
    assert html_to_text("<p>Ein <em>wirklich</em> gutes Spiel.</p>") == (
        "Ein wirklich gutes Spiel."
    )


def test_entities_are_decoded():
    """Roundup citations are full of &amp;, umlauts and en dashes."""
    assert html_to_text("<p>Fux&amp;B&auml;r &#8211; Folge 73</p>") == (
        "Fux&B\u00e4r \u2013 Folge 73"
    )


def test_line_breaks_become_breaks():
    assert html_to_text("<p>Zeile eins<br>Zeile zwei</p>").splitlines() == [
        "Zeile eins",
        "Zeile zwei",
    ]


def test_list_items_are_separated():
    text = html_to_text("<ul><li>Erstens</li><li>Zweitens</li></ul>")

    assert text.splitlines() == ["Erstens", "Zweitens"]


def test_blank_runs_are_collapsed():
    text = html_to_text("<div><p>Eins</p></div>\n\n\n\n<div><p>Zwei</p></div>")

    assert "\n\n\n" not in text


def test_empty_html_gives_empty_text():
    assert html_to_text("") == ""
    assert html_to_text("<article></article>") == ""
