from functools import cache
import logging
from typing import List
from hyperglot.parse import join_variants
import uharfbuzz as hb

log = logging.getLogger(__name__)


class Shaper:
    """
    Helper class to check harfbuzz shaping of a font.
    """

    def __init__(self, fontpath):
        blob = hb.Blob.from_file_path(fontpath)
        face = hb.Face(blob)
        self.font = hb.Font(face)

    def shape(self, text):
        """
        Set up a harfbuzz buffer, shape some text, return the buffer for
        inspection.
        """
        buffer = hb.Buffer()
        buffer.add_str(text)
        buffer.guess_segment_properties()

        features = {"kern": True, "liga": True}

        hb.shape(self.font, buffer, features)

        return buffer

    @cache
    def get_glyph_infos(self, text: str) -> List:
        """
        Shape a text in a new buffer and return the buffer's glyph infos.
        """
        buffer = self.shape(text)
        return buffer.glyph_infos

    @cache
    def check_joining(self, unicode: int) -> bool:
        """
        Check if the string exhibits joining behaviour (shaping differs) by
        comparing its plain version to a version joined with zero width joiners.

        Return True if the shaping differs or the glyph requires no shaping.
        Return False if the shaping remains unchanged but requires joining
        behaviour.

        @param unicode (int): A single unicode to check for all required
            joining variants.
        @return bool
        """

        string = chr(unicode)

        # Use the helper to generate one sequence of given string joined by
        # spaces not causing joining behaviour, and one joined by zero width
        # joiner causing joining behaviour. We can then compare if they differ
        # to deduct working joining behaviour.
        plain = join_variants(string, " ")
        zwj = join_variants(string)

        if plain == []:
            return True

        glyph_id = self.get_glyph_infos(string)[0].codepoint

        # The glyph is not in the font at all
        if glyph_id == 0:
            return False

        # The plain/zwj are arrays of sequences of the unicode in question
        # joined based on its unicode joining_type flags; check through all
        # possible join sequences to confirm all are supported in the font.
        for i in range(0, len(plain)):
            # Get the buffer info of the sequence
            buffer_glyph_info_plain = self.get_glyph_infos(plain[i])
            buffer_glyph_info_zwj = self.get_glyph_infos(zwj[i])
            differs = False

            # This presumes one to one transformations with same length overall
            # sequences. Afaik init/medi/fina/isol should always be one to one.
            if len(buffer_glyph_info_plain) != len(buffer_glyph_info_zwj):
                raise ValueError(
                    "Joining shaping results in multiple glyph substitution."
                )

            for c in range(0, len(buffer_glyph_info_plain)):
                plain_codepoint = buffer_glyph_info_plain[c].codepoint
                zwj_codepoint = buffer_glyph_info_zwj[c].codepoint

                # We are only interested in that point in the sequence that has
                # our char (in the plain version)
                if not plain_codepoint == glyph_id:
                    continue

                log.debug(
                    f"Codepoints at {c} in sequence {i}: {plain_codepoint} "
                    f"({self.font.get_glyph_name(plain_codepoint)}) vs "
                    f"{zwj_codepoint} ({self.font.get_glyph_name(zwj_codepoint)})"
                )

                # If the glyph in the sequence is the glyph we are interested
                # in compare their codepoint (meaning glyph id, not unicode!)
                # to confirm it is different because of automatic script based
                # shaping has been applied in the buffer
                if plain_codepoint != zwj_codepoint:
                    differs = True

            # If this sequence failed to be shaped different we can abort
            if not differs:
                return False

        # All shape
        return True
