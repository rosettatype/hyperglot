import os
from hyperglot.shaper import Shaper

plex_arabic = os.path.abspath("tests/plex-4.0.2/IBM-Plex-Sans-Arabic/fonts/complete/otf/IBMPlexSansArabic-Regular.otf")  # noqa
plex_arabic_without_medi_fina = os.path.abspath("tests/plex-4.0.2/IBM-Plex-Sans-Arabic/fonts/complete/otf/IBMPlexSansArabic-Regular-without-medi-fina.otf")  # noqa
eczar = os.path.abspath("tests/Eczar-v1.004/otf/Eczar-Regular.otf")
testfont = os.path.abspath("tests/HyperglotTestFont-Regular.ttf")

def test_shaper_joining():
    plex_shaper = Shaper(plex_arabic)
    # A basic Arabic character should have joining shaping.
    assert plex_shaper.check_joining(ord("ب")) is True
    
    # A basic Latin character requires no joining shaping.
    assert plex_shaper.check_joining(ord("A")) is True

    # A basic Georgian character requires no joining shaping, even if not in 
    # the font.
    assert plex_shaper.check_joining(ord("ა")) is True

    eczar_shaper = Shaper(eczar)
    # Eczar has no Arabic but the character requires it.
    assert eczar_shaper.check_joining(ord("ب")) is False

    arabic_missing_features_shaper = Shaper(plex_arabic_without_medi_fina)
    # The same Arabic character should be missing shaping if there is no medi 
    # or fina feature in the font.
    assert arabic_missing_features_shaper.check_joining(ord("ب")) is False

    test_shaper = Shaper(testfont)
    # Font with beh and beh.medi is missing beh.init and beh.fina, so it should
    # not pass.
    assert test_shaper.check_joining(ord("ب")) is False


def test_shaper_marks():

    eczar_shaper = Shaper(eczar)
    
    # When the input is an encoded single character, ...
    assert eczar_shaper.check_mark_attachment("Ä")

    # Input A + combining diaresis.
    assert eczar_shaper.check_mark_attachment("A" + chr(0x0308))

    # 'mah' has unencoded combination M + ogonekcomb — this is a good test case
    # to check if the mark gets attached as many fonts won't have the required
    # bottom anchors in M.
    # Eczar has both M and ogonekcomb (U+0328), but not the required anchor in M.
    assert eczar_shaper.check_mark_attachment("M" + chr(0x0328)) is False

    # Check multiple marks, e.g. stacking vietnamese.
    assert eczar_shaper.check_mark_attachment("Ẫ") is False
    assert eczar_shaper.check_mark_attachment("A" + chr(0x0302) + chr(0x0303)) is False

    # Sanity check single, double char, single mark.
    assert eczar_shaper.check_mark_attachment("A") is True
    assert eczar_shaper.check_mark_attachment("AA") is True
    assert eczar_shaper.check_mark_attachment(chr(0x0308)) is True

    test_shaper = Shaper(testfont)

    # Test font has A + combining diaresis but no precomposed Ä U+00C4.
    assert test_shaper.check_mark_attachment("A" + chr(0x0308)) is True

    # Test font with missing base.
    assert test_shaper.check_mark_attachment("B" + chr(0x0308)) is False

    # Test font with missing mark.
    assert test_shaper.check_mark_attachment("B" + chr(0x0360)) is False

    # Check multiple marks, e.g. stacking vietnamese. Test font does not have
    # encoded version, but has base + marks with anchors
    test_shaper.check_mark_attachment("Ẫ")
    test_shaper.check_mark_attachment("A" + chr(0x0302) + chr(0x0303))
