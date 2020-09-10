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

    # Obvisouly this will change if the test font ever gets updated
    assert len(supported["Latin"].keys()) == 201

    # Detected arbitrary language
    assert "zul" in supported["Latin"]
