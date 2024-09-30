from functools import lru_cache
from typing import Iterable
import logging
import unicodedata as uni
from typing import List, Union
import uharfbuzz as hb
from fontTools.ttLib import TTFont

log = logging.getLogger(__name__)
log.setLevel(logging.WARNING)


class Shaper:
    """
    Helper class to check harfbuzz shaping of a font. Provides shaping buffer
    information to checks, so they can implement their logic.
    """

    def __init__(self, fontpath):
        blob = hb.Blob.from_file_path(fontpath)
        face = hb.Face(blob)
        self.font = hb.Font(face)
        self.ttf = TTFont(fontpath)

    def shape(self, text):
        """
        Set up a harfbuzz buffer, shape some text, return the buffer for
        inspection.
        """
        buffer = hb.Buffer()
        buffer.add_str(text)
        buffer.guess_segment_properties()

        features = {
            # Explicitly opt into these
            "kern": True,
            "mark": True,
            "mkmk": True,
            "ccmp": True,
            "abvm": True,
            "blwm": True,
            "dist": True,
            # Explicitly opt out of these so they do not interfere with basic
            # shaping/joining
            "liga": False,
            "rlig": False,
            "rclt": False,
            "calt": False,
            "salt": False,
            # Others should get detected by script of the input, e.g. for
            # Arabic or Indic, so we do not explicitly opt in
        }

        hb.shape(self.font, buffer, features)

        return buffer

    @lru_cache
    def get_glyph_data(self, text: str) -> List:
        """
        Shape a text in a new buffer and return the buffer's glyph infos and
        positions.
        """
        buffer = self.shape(text)
        return list(zip(buffer.glyph_infos, buffer.glyph_positions))

    @lru_cache
    def get_glyph_infos(self, text: str) -> List:
        """
        Shape a text in a new buffer and return the buffer's glyph infos.
        """
        buffer = self.shape(text)
        return buffer.glyph_infos

    def names_for_codepoints(self, codepoints: Iterable[int]) -> List:
        """
        Helper for better debug messages with font glyph names instead of gids.
        """
        return [str(self.font.get_glyph_name(m)) for m in codepoints]

    @lru_cache
    def _get_font_cp(self, char: str) -> Union[int | bool]:
        """
        Render character in the buffer to get the font codepoint for it.
        """

        cmap = {v: k for k, v in self.ttf["cmap"].getBestCmap().items()}

        for d in self.get_glyph_data(char):
            glyphname = self.font.get_glyph_name(d[0].codepoint)
            try:
                if (cmap[glyphname]) == ord(char):
                    return d[0].codepoint
            except KeyError as e:
                log.debug(f"Failed to get font codepoint for '{char}': {e}")

        return False
