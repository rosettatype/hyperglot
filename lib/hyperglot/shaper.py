from functools import lru_cache
from typing import Iterable
import logging
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

    def glyphname_for_unicode(self, char: str) -> Union[str | None]:
        try:
            cp = self.font.get_glyph(ord(char))
            return self.font.get_glyph_name(cp)
        except Exception as e:
            return None


    # def font_has_mark_lookup_for(self, char:str, mark:str) -> bool:
    #     """
    #     Note: Not super useful right now, but may be needed at some point. Also
    #     Need to account for the aliases still to work.

    #     For a pair of two characters (base + mark, liga + mark, mark + mark)
    #     check if a mark positioning entry exists in the font.
    #     """
    #     char_name = self.glyphname_for_unicode(char)
    #     mark_name = self.glyphname_for_unicode(mark)

    #     if not char_name or not mark_name:
    #         return False

    #     if "GPOS" not in self.ttf:
    #         return False

    #     for l in self.ttf["GPOS"].table.LookupList.Lookup:
    #         # Mark to Base, Mark to Ligature, Mark to Mark
    #         if l.LookupType in (4, 5, 6):
    #             for s in l.SubTable:
    #                 # No need to check the actual values, as long as the
    #                 # coverage overlaps it's a match.
    #                 if char_name in s.BaseCoverage.glyphs and mark_name in s.MarkCoverage.glyphs:
    #                     return True
    #     return False
