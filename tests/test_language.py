"""
Basic Language support checks
"""
from hyperglot.languages import Languages
from hyperglot.language import Language


def test_language_has_support():
    Langs = Languages()

    # A Language object with the 'fin' data
    fin = Language(Langs["fin"], "fin")

    # These "chars" represent a font with supposedly those codepoints in it
    fin_chars_missing_a = "bcdefghijklmnopqrstuvwxyzäöå"
    fin_chars_base = "abcdefghijklmnopqrstuvwxyzäöå ̈ ̊"
    fin_chars_aux = "abcdefghijklmnopqrstuvwxyzäöåæõøüšž ̈ ̊ ̃ ̌"
    fin_chars_no_precomposed = "abcdefghijklmnopqrstuvwxyz ̈ ̊"

    # This is what has_support should look like if it determines 'fin' is
    # supported
    fin_matched = {"Latin": ["fin"]}

    matches = fin.has_support(fin_chars_base, pruneOrthographies=False)
    assert matches == fin_matched

    no_matches = fin.has_support(fin_chars_base, level="aux",
                                 pruneOrthographies=False)
    assert no_matches == {}

    matches = fin.has_support(fin_chars_aux, level="aux",
                              pruneOrthographies=False)
    assert matches == fin_matched

    no_matches = fin.has_support(fin_chars_base, level="aux",
                                 pruneOrthographies=False)
    assert no_matches == {}

    no_matches = fin.has_support(fin_chars_missing_a, pruneOrthographies=False)
    assert no_matches == {}

    matches = fin.has_support(fin_chars_no_precomposed,
                              pruneOrthographies=False)
    assert matches == fin_matched


def test_language_inherit():
    Langs = Languages(inherit=True)

    # aae inherits aln orthography
    aae = Language(Langs["aae"], "aae")
    aln = Language(Langs["aln"], "aln")
    assert aae.get_orthography()["base"] == aln.get_orthography()["base"]

    # without inheritance aae's only orthography should not have any base chars
    Langs = Languages(inherit=False)
    aae = Language(Langs["aae"], "aae")
    assert "base" not in aae.get_orthography()


def test_language_preferred_name():
    Langs = Languages()
    bal = Language(Langs["bal"], "bal")
    #   name: Baluchi
    #   preferred_name: Balochi
    assert bal.get_name() == "Balochi"


def test_language_get_autonym():
    Langs = Languages()
    bal = Language(Langs["bal"], "bal")
    #   name: Baluchi
    #   - autonym: بلۏچی
    #     script: Arabic
    #   preferred_name: Balochi

    # For Arabic it should return the correct autonym, without script False
    assert bal.get_autonym(script="Arabic") == "بلۏچی"
    assert bal.get_autonym() is False
