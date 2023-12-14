import os
from hyperglot.shaper import Shaper

plex_arabic = os.path.abspath("tests/plex-4.0.2/IBM-Plex-Sans-Arabic/fonts/complete/otf/IBMPlexSansArabic-Regular.otf")  # noqa
plex_arabic_without_medi_fina = os.path.abspath("tests/plex-4.0.2/IBM-Plex-Sans-Arabic/fonts/complete/otf/IBMPlexSansArabic-Regular-without-medi-fina.otf")  # noqa
eczar = os.path.abspath("tests/Eczar-v1.004/otf/Eczar-Regular.otf")
testfont = os.path.abspath("tests/HyperglotTestFont-Regular.ttf")

def test_shaper():
    plex_shaper = Shaper(plex_arabic)
    # A basic Arabic character should have joining shaping
    assert plex_shaper.check_joining(ord("ب")) is True
    
    # A basic Latin character requires no joining shaping
    assert plex_shaper.check_joining(ord("A")) is True

    # A basic Georgian character requires no joining shaping, even if not in 
    # the font
    assert plex_shaper.check_joining(ord("ა")) is True

    eczar_shaper = Shaper(eczar)
    # Eczar has no Arabic but the character requires it
    assert eczar_shaper.check_joining(ord("ب")) is False

    arabic_missing_features_shaper = Shaper(plex_arabic_without_medi_fina)
    # The same Arabic character should be missing shaping if there is no medi 
    # or fina feature in the font
    assert arabic_missing_features_shaper.check_joining(ord("ب")) is False

    test_shaper = Shaper(testfont)
    # Font with beh and beh.medi is missing beh.init and beh.fina, so it should
    # not pass
    assert test_shaper.check_joining(ord("ب")) is False
