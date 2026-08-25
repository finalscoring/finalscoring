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


def test_footnote_markers_are_bracketed():
    """A bare digit glued to a sentence reads as a typo, not a citation."""
    html = (
        '<p>sagt er.<sup class="fn" data-fn="abc-123">'
        '<a id="abc-123-link" href="#abc-123">5</a></sup></p>'
    )

    assert html_to_text(html) == "sagt er. [5]"


def test_multiple_footnote_markers_in_one_sentence():
    html = (
        '<p>Meinungen<sup data-fn="a"><a href="#a">1</a></sup> gehen'
        ' auseinander<sup data-fn="b"><a href="#b">2</a></sup>.</p>'
    )

    assert html_to_text(html) == "Meinungen [1] gehen auseinander [2]."


def test_plain_superscript_is_not_bracketed():
    """A footnote and an exponent both use <sup> — only data-fn is a citation."""
    assert html_to_text("<p>10<sup>2</sup> Punkte</p>") == "102 Punkte"
