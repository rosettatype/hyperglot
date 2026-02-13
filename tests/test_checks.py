"""
Test the individual lib/hyperglot/checks and their components.
"""

import os
import logging

from hyperglot.checks.check_coverage import Check as CheckCoverage
from hyperglot.checks.check_mark_attachment import Check as CheckMarkAttachment
from hyperglot.checks.check_arabic_joining import Check as CheckArabicJoining
from hyperglot.checks.check_brahmi_conjuncts import Check as CheckBrahmiConjuncts
from hyperglot.checks.check_brahmi_halfforms import Check as CheckBrahmiHalfforms
from hyperglot.checks.check_combination_marks import Check as CheckCombinationMarks
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
yantramanav = os.path.abspath("tests/Yantramanav/Yantramanav-Medium.ttf")
testfont = os.path.abspath("tests/HyperglotTestFont-Regular.ttf")
noto_arabic = os.path.abspath(
    "tests/Noto_Sans_Arabic/NotoSansArabic[wdth,wght].ttf"
)  # noqa


def test_check_coverage():

    coverage_check = CheckCoverage()
    eng = Language("eng").get_orthography()
    fin = Language("fin").get_orthography()

    assert coverage_check.check(eng, CharsetChecker(eng.base_chars)) is True
    assert len(coverage_check.logs) == 0

    assert coverage_check.check(fin, CharsetChecker(eng.base_chars)) is False
    assert len(coverage_check.logs) == 1
    assert (
        "missing characters for 'base': Ä, Å, Ö, ä, å, ö" in coverage_check.logs[0][3]
    )

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

    noto_shaper = Shaper(noto_arabic)
    assert joining_check.check_joining(ord("ب"), noto_shaper) is True

    # A case where the output sequence will be longer than the input sequence
    # for this font, this should still pass!
    assert joining_check.check_joining(ord("ی"), noto_shaper) is True


def test_check_conjuncts(caplog):
    conjuncts_check = CheckBrahmiConjuncts()
    plex_shaper = Shaper(plex_arabic)
    eczar_shaper = Shaper(eczar)
    yantramanav_shaper = Shaper(yantramanav)

    # Plex Arabic has no Virama:
    logging.getLogger("hyperglot.checks.check_brahmi_conjuncts").setLevel(logging.DEBUG)
    assert conjuncts_check.check_conjunct("स्व", plex_shaper) is False
    assert "Font contains no Virama" in caplog.records[-1].message

    # Check a basic conjunct with a supporting fonts
    assert conjuncts_check.check_all_render("स्व", eczar_shaper) is True
    assert conjuncts_check.check_conjunct("स्व", eczar_shaper) is True
    assert conjuncts_check.check_conjunct("स्व", yantramanav_shaper) is True

    # Check a basic conjunct with ZWJ (consumes virama)
    assert conjuncts_check.check_all_render("स्‍व", eczar_shaper) is True
    assert conjuncts_check.check_conjunct("स्‍व", eczar_shaper) is True
    assert conjuncts_check.check_conjunct("न्‍", eczar_shaper) is True
    assert conjuncts_check.check_conjunct("स्‍", eczar_shaper) is True
    assert conjuncts_check.check_conjunct("क्‍", eczar_shaper) is True

    # Check a basic conjunct with ZWNJ (retains virama)
    assert conjuncts_check.check_all_render("स्‌व", eczar_shaper) is True
    assert conjuncts_check.check_conjunct("स्‌व", eczar_shaper) is True
    assert conjuncts_check.check_conjunct("न्‌", eczar_shaper) is True
    assert conjuncts_check.check_conjunct("त्‌", eczar_shaper) is True

    # A non-sense conjunct should trigger a warning, but pass
    assert conjuncts_check.check_conjunct("ABC", eczar_shaper) is True
    assert "No Virama in conjunct" in caplog.records[-1].message

    # A sample of simple, valid consonant-virama-consonant (+x) conjuncts that
    # should render
    for s in ["स्त", "त्त", "र्म", "ध्य", "क्ति", "स्थि"]:
        assert conjuncts_check.check_all_render(s, eczar_shaper) is True
        assert conjuncts_check.check_conjunct(s, eczar_shaper) is True

    # A sample of longer, multi-consonant conjuncts that should render
    for s in [
        "फ़्ग़ा",
        "ज़्ज़ा",
        "फ़्फ़",
        "फ़्रां",
        "फ़्रैं",
        "फ़्रें",
        "फ़्राँ",
        "ज़्या",
        "फ़्री",
        "फ़्रा",
        "ख़्या",
        "फ़्लै",
        "ख़्तू",
        "ख़्वा",
        "फ़्रि",
        "फ़्ता",
        "ज़्यू",
        "ज़्बे",
        "फ़्ते",
        "ज़्मा",
        "फ़्ती",
        "ज़्टे",
        "फ़्रे",
        "फ़्यू",
    ]:
        assert conjuncts_check.check_conjunct(s, eczar_shaper) is True


def test_check_conjuncts_filter():

    conjuncts_check = CheckBrahmiConjuncts()

    # Sanity checks
    assert conjuncts_check.filter_conjuncts("A") is False
    assert conjuncts_check.filter_conjuncts("ABC") is False

    # Just virama is not enough
    assert conjuncts_check.filter_conjuncts(chr(0x094D)) is False

    # Consonant + virama also not enough
    halfforms = ["न्", "त्", "द्", "म्", "प्", "ह्"]
    for h in halfforms:
        assert conjuncts_check.filter_conjuncts(h) is False

    # Halfform + x should be a conjunct
    for h in halfforms:
        assert conjuncts_check.filter_conjuncts(h + "क") is True

    # Test some actual conjuncts with vowels and marks
    for c in [
        "स्ट",
        "ग्र",
        "द्र",
        "क्स",
        "र्मा",
        "त्रि",
        "श्चि",
        "श्य",
        "र्श",
        "ष्ट",
        "ख्य",
        "ष्ट्री",
        "न्त",
        "र्ड",
        "त्म",
        "म्ब",
        "द्या",
        "त्रा",
        "स्तु",
        "ब्द",
        "त्रों",
        "स्प",
        "ग्रा",
        "प्रे",
        "न्या",
        "स्कृ",
        "ब्रि",
    ]:
        assert conjuncts_check.filter_conjuncts(c) is True

    # Test some clusters with single consonant
    for c in ["के", "का", "में", "हैं", "हीं", "रों", "ड़े", "हिं"]:
        assert conjuncts_check.filter_conjuncts(c) is False

    # A combination of C + C + Virama should fail
    assert conjuncts_check.filter_conjuncts("कक" + chr(0x094D)) is False
    # A combination of Virama + C + C should fail
    assert conjuncts_check.filter_conjuncts(chr(0x094D) + "कक") is False


def test_halfforms_filter():
    logging.getLogger("hyperglot.checks.check_brahmi_halfforms").setLevel(logging.DEBUG)
    halfforms_check = CheckBrahmiHalfforms()

    # Sanity checks
    assert halfforms_check.filter_halfforms("A") is False
    assert halfforms_check.filter_halfforms("A" + chr(0x094D)) is False

    # Basically check all common halfforms
    for h in [
        "न्",
        "त्",
        "म्",
        "प्",
        "ह्",
        "स्",
        "क्",
        "र्",
        "ल्",
        "व्",
        "च्",
        "ख्",
        "श्",
        "फ्",
        "ग्",
        "ज्",
        "ण्",
        "ऩ्",
        "य्",
        "ध्",
        "ळ्",
        "ष्",
        "भ्",
        "ञ्",
        "छ्",
    ]:
        assert halfforms_check.filter_halfforms(h) is True

    # Random assortment of non-halfform looking clusters
    for c in ["त", "का", "में", "ए", "यों", "स्था", "फ"]:
        assert halfforms_check.filter_halfforms(c) is False


def test_halfforms_check(caplog):
    halfforms_check = CheckBrahmiHalfforms()

    plex_shaper = Shaper(plex_arabic)
    eczar_shaper = Shaper(eczar)

    # Plex Arabic has no Virama:
    assert halfforms_check.check_halfform("स्व", plex_shaper) is False
    assert "Font contains no Virama" in caplog.records[-1].message

    # All common halfforms pass:
    for h in [
        "न्",
        "त्",
        "म्",
        "प्",
        "ह्",
        "स्",
        "क्",
        "र्",
        "ल्",
        "व्",
        "च्",
        "ख्",
        "श्",
        "फ्",
        "ग्",
        "ज्",
        "ण्",
        "ऩ्",
        "य्",
        "ध्",
        "ळ्",
        "ष्",
        "भ्",
        "ञ्",
    ]:
        assert halfforms_check.check_halfform(h, eczar_shaper) is True


def test_combination_marks():

    logging.getLogger("hyperglot.checks.check_mark_attachment").setLevel(logging.DEBUG)

    mark_check = CheckCombinationMarks()

    eczar_shaper = Shaper(eczar)
    noto_shaper = Shaper(noto_deva)

    # Mark attachment
    assert mark_check.check_cluster_mark_attachment("ग़ं", eczar_shaper) is True

    # Eczar actually misses this one, but Noto does not
    # assert mark_check.check_cluster_mark_attachment("म़ि", eczar_shaper) is False # see below
    assert mark_check.check_cluster_mark_attachment("म़ि", noto_shaper) is True

    # # Eczar actually misses this one, but Noto does not
    # assert mark_check.check_cluster_mark_attachment("डो़", eczar_shaper) is False # see below
    assert mark_check.check_cluster_mark_attachment("डो़", noto_shaper) is True

    assert mark_check.check_cluster_mark_attachment("क्सिं", eczar_shaper) is True
    assert mark_check.check_cluster_mark_attachment("प्लू", eczar_shaper) is True
    assert mark_check.check_cluster_mark_attachment("ड्भु", eczar_shaper) is True

    # Eczar actually positions this mark
    assert mark_check.check_cluster_mark_attachment("वृ", eczar_shaper) is True

    # Whereas Noto the mark is positioned in such a way that does not result in
    # an offset (failsafe design)
    # TODO How on earth to confirm the shapes make sense without any explicit
    # technical data to confirm this?
    # assert mark_check.check_cluster_mark_attachment("वृ", noto_shaper) is False


def test_cluster_mark_logs(caplog):
    logging.getLogger("hyperglot.checks.check_mark_attachment").setLevel(logging.DEBUG)
    logging.getLogger("hyperglot.checks.check_combination_marks").setLevel(
        logging.DEBUG
    )

    mark_check = CheckCombinationMarks()
    yantramanav_shaper = Shaper(yantramanav)
    eczar_shaper = Shaper(eczar)

    # Passes
    assert mark_check.check_cluster_mark_attachment("के", yantramanav_shaper) is True

    # nonsense combinations with virama
    assert mark_check.check_cluster_mark_attachment("A्A", yantramanav_shaper) is True

    # For Yantramanav harfbuzz fails to return the glyph names, but the cluster warning is emitted
    assert mark_check.check_cluster_mark_attachment("φ्φ", yantramanav_shaper) is False
    assert "Mark shaping for cluster" in caplog.records[-1].message
    assert "missing 2 glyphs" in caplog.records[-1].message

    # For other fonts the actual culprit is listed in the warning
    assert mark_check.check_cluster_mark_attachment("φ्φ", eczar_shaper) is False
    assert "Mark shaping for cluster" in caplog.records[-1].message
    assert "missing 2 glyphs" in caplog.records[-1].message
