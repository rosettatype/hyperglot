"""
Test the individual lib/hyperglot/checks and their components.
"""
import os

from hyperglot.checks.check_coverage import Check as CheckCoverage
from hyperglot.checks.check_mark_attachment import Check as CheckMarkAttachment
from hyperglot.checks.check_arabic_joining import Check as CheckArabicJoining
from hyperglot.language import Language
from hyperglot.checker import CharsetChecker
from hyperglot.shaper import Shaper

plex_arabic = os.path.abspath(
    "tests/plex-4.0.2/IBM-Plex-Sans-Arabic/fonts/complete/otf/IBMPlexSansArabic-Regular.otf"
)  # noqa
plex_arabic_without_medi_fina = os.path.abspath(
    "tests/plex-4.0.2/IBM-Plex-Sans-Arabic/fonts/complete/otf/IBMPlexSansArabic-Regular-without-medi-fina.otf"
)  # noqa
eczar = os.path.abspath("tests/Eczar-v1.004/otf/Eczar-Regular.otf")
eczar_marks_ccmp = os.path.abspath("tests/Eczar-marks/EczarCCMP-Regular.otf")
eczar_marks_mk = os.path.abspath("tests/Eczar-marks/EczarMarks-Regular.otf")
noto_deva = os.path.abspath(
    "tests/Noto_Sans_Devanagari/static/NotoSansDevanagari_Condensed-Regular.ttf"
)
testfont = os.path.abspath("tests/HyperglotTestFont-Regular.ttf")


def test_check_coverage():
    coverage_check = CheckCoverage()
    eng = Language("eng").get_orthography()
    fin = Language("fin").get_orthography()

    assert coverage_check.check(eng, CharsetChecker(eng.base_chars)) is True
    assert coverage_check.check(fin, CharsetChecker(eng.base_chars)) is False

    # Note: Coverage is extensively checked with Checker tests.


def test_check_marks():
    mark_check = CheckMarkAttachment()
    eczar_shaper = Shaper(eczar)

    # When the input is an encoded single character, ...
    assert mark_check.check_mark_attachment("Ä", eczar_shaper)

    # Input A + combining diaresis.
    assert mark_check.check_mark_attachment("A" + chr(0x0308), eczar_shaper)

    # 'mah' has unencoded combination M + ogonekcomb — this is a good test case
    # to check if the mark gets attached as many fonts won't have the required
    # bottom anchors in M.
    # Eczar has both M and ogonekcomb (U+0328), but not the required anchor in M.
    assert mark_check.check_mark_attachment("M" + chr(0x0328), eczar_shaper) is False

    # Check multiple marks, e.g. stacking vietnamese.
    assert mark_check.check_mark_attachment("Ẫ", eczar_shaper) is False
    assert (
        mark_check.check_mark_attachment("A" + chr(0x0302) + chr(0x0303), eczar_shaper)
        is False
    )

    # Sanity check single, double char, single mark.
    assert mark_check.check_mark_attachment("A", eczar_shaper) is True
    assert mark_check.check_mark_attachment("AA", eczar_shaper) is True
    assert mark_check.check_mark_attachment(chr(0x0308), eczar_shaper) is True

    test_shaper = Shaper(testfont)

    # Test font has A + combining diaresis but no precomposed Ä U+00C4.
    assert mark_check.check_mark_attachment("A" + chr(0x0308), test_shaper) is True

    # Test font with missing base.
    assert mark_check.check_mark_attachment("B" + chr(0x0308), test_shaper) is False

    # Test font with missing mark.
    assert mark_check.check_mark_attachment("B" + chr(0x0360), test_shaper) is False

    # Check multiple marks, e.g. stacking vietnamese. Test font does not have
    # encoded version, but has base + marks with anchors
    mark_check.check_mark_attachment("Ẫ", test_shaper)
    mark_check.check_mark_attachment("A" + chr(0x0302) + chr(0x0303), test_shaper)

    # Different ways of handling s ogonek:
    # With mark code
    eczar_marks_shaper = Shaper(eczar_marks_mk)
    assert (
        mark_check.check_mark_attachment("s" + chr(0x0328), eczar_marks_shaper) is True
    )
    # With ccmp replacement
    eczar_ccmp_shaper = Shaper(eczar_marks_ccmp)
    assert (
        mark_check.check_mark_attachment("s" + chr(0x0328), eczar_ccmp_shaper) is True
    )


def test_check_joining():
    joining_check = CheckArabicJoining()

    plex_shaper = Shaper(plex_arabic)
    # A basic Arabic character should have joining shaping.
    assert joining_check.check_joining(ord("ب"), plex_shaper) is True

    # A basic Latin character requires no joining shaping.
    assert joining_check.check_joining(ord("A"), plex_shaper) is True

    # A basic Georgian character requires no joining shaping, even if not in
    # the font.
    assert joining_check.check_joining(ord("ა"), plex_shaper) is True

    eczar_shaper = Shaper(eczar)
    # Eczar has no Arabic but the character requires it.
    assert joining_check.check_joining(ord("ب"), eczar_shaper) is False

    arabic_missing_features_shaper = Shaper(plex_arabic_without_medi_fina)
    # The same Arabic character should be missing shaping if there is no medi
    # or fina feature in the font.
    assert (
        joining_check.check_joining(ord("ب"), arabic_missing_features_shaper) is False
    )

    test_shaper = Shaper(testfont)
    # Font with beh and beh.medi is missing beh.init and beh.fina, so it should
    # not pass.
    assert joining_check.check_joining(ord("ب"), test_shaper) is False


# WIP
# def test_conjunct_shaping():
#     logging.getLogger("hyperglot.shaper").setLevel(logging.DEBUG)
#     eczar_shaper = Shaper(eczar)
#     # conjuncts = ["भि‍", "स्‍‍", "म़ि", "वै्", "दृ‍", "लै‍", "यो्", "जा्", "चोः", "दॄ", "डो़", "ढी़", "या‌", "ख़ां", "बि्", "शा्", "पो्", "ग़ं", "तॉ", "थाँ", "थे्", "यॉँ", "मा‍", "नि्", "चू्", "णीः", "धाः",]
#     conjuncts = ["र", "क", "न", "स", "त", "के", "य", "प", "का", "म", "में", "र्", "या", "ल", "व", "अ", "ग", "है", "ए", "स्", "प्", "ह", "ने", "की", "से", "रा", "ता", "त्", "क्", "ब", "उ", "इ", "औ"]
#     for s in conjuncts:
#         assert eczar_shaper.check_conjuncts(s) is True

#     # C+
#     assert eczar_shaper.check_conjuncts("र्") is True
#     # CM+
#     assert eczar_shaper.check_conjuncts("ख़्") is True

#     # CD+, shapes but without consuming virama
#     assert eczar_shaper.check_conjuncts("टि्") is True


#     # Has no codepoints for this shaping
#     plex_shaper = Shaper(plex_arabic)
#     assert plex_shaper.check_conjuncts("ख़्") is False

#     test_shaper = Shaper(testfont)
#     assert test_shaper.check_conjuncts("ख़्") is False

#     assert eczar_shaper.check_conjuncts("ल्पि") is True


# def test_conjunct_marks():

#     eczar_shaper = Shaper(eczar)
#     noto_shaper = Shaper(noto_deva)

#     logging.getLogger("hyperglot.shaper").setLevel(logging.DEBUG)
#     # Mark attachment
#     assert eczar_shaper.check_mark_attachment("ग़ं") is True

#     # Eczar actually misses this one, but Noto does not
#     assert eczar_shaper.check_mark_attachment("म़ि") is False
#     assert noto_shaper.check_mark_attachment("म़ि") is True

#     # Eczar actually misses this one, but Noto does not
#     assert eczar_shaper.check_mark_attachment("डो़") is False
#     assert noto_shaper.check_mark_attachment("डो़") is True

#     conjuncts = ["भि‍", "स्‍‍", "वै्", "दृ‍", "लै‍", "यो्", "जा्", "चोः", "दॄ", "डो़", "ढी़", "या‌", "ख़ां", "बि्", "शा्", "पो्", "ग़ं", "तॉ", "थाँ", "थे्", "यॉँ", "मा‍", "नि्", "चू्", "णीः", "धाः",]
#     # conjuncts = ["र", "क", "न", "स", "त", "के", "य", "प", "का", "म", "में", "र्", "या", "ल", "व", "अ", "ग", "है", "ए", "स्", "प्", "ह", "ने", "की", "से", "रा", "ता", "त्", "क्", "ब", "उ", "इ", "औ"]
#     for s in conjuncts:
#         assert eczar_shaper.check_mark_attachment(s) is True
