import os
from hyperglot.parse import parse_font_chars
from hyperglot.languages import Languages


def test_languages_basic():
    path = os.path.abspath("tests/Eczar-v1.004/otf/Eczar-Regular.otf")

    chars = parse_font_chars(path)

    Langs = Languages()
    supported = Langs.get_support_from_chars(chars)

    # Detected scripts
    assert "Latin" in supported.keys()
    assert "Arabic" not in supported.keys()

    # Detected arbitrary language
    assert "zul" in supported["Latin"]


def test_languages_validity():
    path = os.path.abspath("tests/Eczar-v1.004/otf/Eczar-Regular.otf")

    chars = parse_font_chars(path)

    # Compared to basic, raised validity should have less hits
    Langs = Languages(validity="preliminary")
    supported = Langs.get_support_from_chars(chars)
    isos = supported["Latin"].keys()

    # 'lue' (Luvale) is currently 'todo', so it should not be in this
    assert "lue" not in isos

    # 'fin' (Finnish) is currently 'perliminary', so it should be listed
    assert "fin" in isos

    # 'deu' (German) is currently 'verified', which is "more complete" than
    # 'preliminary', so should be listed
    assert "deu" in isos
