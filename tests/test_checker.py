"""
Basic Language support checks
"""
import os
import pytest
import unicodedata as uni
from hyperglot.parse import character_list_from_string, parse_font_chars
from hyperglot.checker import CharsetChecker, FontChecker

# These "chars" represent a font with supposedly those codepoints in it
fin_missing_a = character_list_from_string("bcdefghijklmnopqrstuvwxyzäöå")
fin_base = character_list_from_string(
    "ABCDEFGHIJKLMNOPQRSTUVWXYZÄÖÅabcdefghijklmnopqrstuvwxyzäöå"
)
fin_aux = character_list_from_string(
    "ABCDEFGHIJKLMNOPQRSTUVWXYZÄÖÅÆÕØÜŠŽabcdefghijklmnopqrstuvwxyzäöåæõøüšž"
)
# fin_chars_no_precomposed = character_list_from_string(
#     "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"
# )

rus_base = character_list_from_string(
    "АБВГДЕЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯЁабвгдежзийклмнопрстуфхцчшщъыьэюяё"
)
# rus_aux = "А́ Е́ И́ О́ У́ Ы́ Э́ ю́ я́ а́ е́ и́ о́ у́ ы́ э́ ю́ я́"
# rus_marks = "◌̆ ◌̈ ◌́"

def test_language_supported():
    

    # This is long
    matches = CharsetChecker(fin_base).get_supported_languages()
    assert "fin" in matches["Latin"].keys()

    # for shorter direct check
    assert CharsetChecker(fin_base).supports_language("fin")

    # Just base chars input won't support aux
    assert (
        CharsetChecker(fin_base).supports_language("fin", supportlevel="aux")
        is False
    )

    # But aux chars input will
    assert CharsetChecker(fin_aux).supports_language("fin", supportlevel="aux")

    # A Font without 'a' won't support this language
    assert CharsetChecker(fin_missing_a).supports_language("fin") is False

    # Just basic other language check
    assert CharsetChecker(rus_base).supports_language("rus", supportlevel="base")


def test_non_iso():
    # Nope for language names
    with pytest.raises(ValueError):
        assert CharsetChecker(fin_base).supports_language("German")

    # Nope for non existing iso codes
    with pytest.raises(ValueError):
        assert CharsetChecker(fin_base).supports_language("xxx")

    # Nope for misc other input
    with pytest.raises(ValueError):
        assert CharsetChecker(fin_base).supports_language(True)
    with pytest.raises(ValueError):
        assert CharsetChecker(fin_base).supports_language(123)




def test_supports_marks():
    eczar = os.path.abspath("tests/Eczar-v1.004/otf/Eczar-Regular.otf")
    chars = parse_font_chars(eczar)

    # Let's fake a font with no combining marks
    chars = [c for c in chars if not uni.category(c).startswith("M")]

    assert CharsetChecker(chars).supports_language("deu")

    # If all combining marks are required and the input has no combining marks
    # this should no longer match
    assert CharsetChecker(chars).supports_language("deu", marks=True) is False


def test_supports_decomposed_no_marks():
    eczar = os.path.abspath("tests/Eczar-v1.004/otf/Eczar-Regular.otf")
    chars = parse_font_chars(eczar)

    # Let's fake a font with no combining marks
    chars = [c for c in chars if not uni.category(c).startswith("M")]

    # The font which has no marks but all encoded characters should still match
    assert CharsetChecker(chars).supports_language("deu", decomposed=True)


def test_supports_decomposed():
    eczar = os.path.abspath("tests/Eczar-v1.004/otf/Eczar-Regular.otf")
    chars = parse_font_chars(eczar)

    # Let's fake a font with no encoded german umlauts
    chars = [c for c in chars if c not in ["Ä", "Ö", "Ü", "ä", "ö", "ü"]]

    # Base + marks are not enough, we want composed chars, and they are missing
    assert CharsetChecker(chars).supports_language("deu", decomposed=False) is False

    # Let's fake a font which has neither umlauts nor marks (the last is a dieresis comb)
    chars = parse_font_chars(eczar)
    chars = [c for c in chars if c not in ["Ä", "Ö", "Ü", "ä", "ö", "ü", "̈"]]
    # It should not be supporting deu either
    assert CharsetChecker(chars).supports_language("deu", decomposed=True) is False

    # Let's fake a font which is missing some umlauts, but has needed
    # base + marks
    chars = parse_font_chars(eczar)
    chars = [c for c in chars if c not in ["Ö", "Ü", "ö", "ü"]]
    # It should be supporting deu, because the missing A/a umlauts can be
    # composed from base + marks
    assert CharsetChecker(chars).supports_language("deu", decomposed=True)


def test_supports_font():
    eczar = os.path.abspath("tests/Eczar-v1.004/otf/Eczar-Regular.otf")

    assert FontChecker(eczar).supports_language("deu")
    assert FontChecker(eczar).supports_language("fin")
