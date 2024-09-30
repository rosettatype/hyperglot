import os
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
testfont = os.path.abspath("tests/HyperglotTestFont-Regular.ttf")
noto_arabic = os.path.abspath(
    "tests/Noto_Sans_Arabic/NotoSansArabic[wdth,wght].ttf"
)  # noqa
yantramanav = os.path.abspath("tests/Yantramanav/Yantramanav-Medium.ttf")


def test_shaper():
    # Not really too much sense in these, more of a functional check.

    eczar_shaper = Shaper(eczar)
    assert eczar_shaper.shape("A").glyph_positions[0].position == (0, 0, 696, 0)

    # Font glyph ID (=codepoint)
    assert eczar_shaper.get_glyph_infos("A")[0].codepoint == 40
    assert eczar_shaper.names_for_codepoints([40]) == ["A"]

    plex_shaper = Shaper(plex_arabic)

    # no offsets, just x advanced
    assert plex_shaper.shape("ت").glyph_positions[0].position == (0, 0, 839, 0)

    # first in buffer is positioned mark
    assert plex_shaper.shape("تً").glyph_positions[0].position == (294, 181, 0, 0)
    # second is same as un-mark'ed character
    assert (
        plex_shaper.shape("تً").glyph_positions[1].position
        == plex_shaper.shape("ت").glyph_positions[0].position
    )
