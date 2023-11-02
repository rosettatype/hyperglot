import os
from hyperglot.parse import parse_font_chars
from hyperglot.languages import Languages


def test_languages_basic():
    path = os.path.abspath("tests/Eczar-v1.004/otf/Eczar-Regular.otf")

    chars = parse_font_chars(path)

    Langs = Languages()
    supported = Langs.supported(chars)

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
    supported = Langs.supported(chars)
    isos = supported["Latin"].keys()

    # 'lue' (Luvale) is currently 'todo', so it should not be in this
    assert "lue" not in isos

    # 'fin' (Finnish) is currently 'perliminary', so it should be listed
    assert "fin" in isos

    # 'deu' (German) is currently 'verified', which is "more complete" than
    # 'preliminary', so should be listed
    assert "deu" in isos


def test_languages_inherit():
    Langs = Languages(inherit=True)

    # Algerian Arabic arq has one orthography that inherits from Tunisian
    # Arabic aeb, which in turn inherits from Standard Arabic arb
    arq = Langs["arq"]["orthographies"][0]
    aeb = Langs["aeb"]["orthographies"][0]
    arb = Langs["arb"]["orthographies"][0]

    assert (arq["base"] == arb["base"])

    # Make sure the autonym did not get inherited
    assert (arq["autonym"] == "دارجة جزائرية")

    # Make sure arq and arb have same amount of attributes, e.g. everything
    # that can be inherited did get inherited (arq will have the 'inherit'
    # attribute, so for testing equality, add it to the list of attributes that
    # arb has)
    arq_attr = set(sorted(arq.keys()))
    aeb_attr = set(sorted(list(aeb.keys()) + ["inherit"]))
    arb_attr = set(sorted(list(arb.keys()) + ["inherit"]))
    assert arq_attr == aeb_attr == arb_attr


def test_languages_parsed_from_escaped_filenames():
    Langs = Languages()
    assert hasattr(Langs, "con")
    assert "con" in Langs
