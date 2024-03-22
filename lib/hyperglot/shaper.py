from functools import lru_cache
from typing import Iterable
import logging
import unicodedata2 as uni
from typing import List
import uharfbuzz as hb
from hyperglot.parse import join_variants, parse_chars

log = logging.getLogger(__name__)
log.setLevel(logging.WARNING)


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

        features = {
            # Explicitly opt into these
            "kern": True,
            "mark": True,
            "mkmk": True,

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
        return [self.font.get_glyph_name(m) for m in codepoints]

    @lru_cache
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

        glyph_info = self.get_glyph_infos(string)
        glyph_id = glyph_info[0].codepoint

        # The glyph is not in the font at all.
        if glyph_id == 0:
            return False

        # The plain/zwj are arrays of sequences of the unicode in question
        # joined based on its unicode joining_type flags; check through all
        # possible join sequences to confirm all are supported in the font.
        for i in range(0, len(plain)):
            # Get the buffer info of the sequence.
            buffer_glyph_info_plain = self.get_glyph_infos(plain[i])
            buffer_glyph_info_zwj = self.get_glyph_infos(zwj[i])
            differs = False

            # This presumes one to one transformations with same length overall
            # sequences. Afaik init/medi/fina/isol should always be one to one.
            if len(buffer_glyph_info_plain) != len(buffer_glyph_info_zwj):
                log.debug(
                    f"Test sequences for {string} / {unicode}: {plain} "
                    f"(buffer length {len(buffer_glyph_info_plain)}) vs "
                    f"{zwj} (buffer length {len(buffer_glyph_info_zwj)})"
                )
                raise ValueError(
                    "Joining shaping results in multiple glyph substitution."
                )

            for c in range(0, len(buffer_glyph_info_plain)):
                plain_codepoint = buffer_glyph_info_plain[c].codepoint
                zwj_codepoint = buffer_glyph_info_zwj[c].codepoint

                # We are only interested in that point in the sequence that has
                # our char (in the plain version).
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
                # shaping has been applied in the buffer.
                if plain_codepoint != zwj_codepoint:
                    differs = True

            # If this sequence failed to be shaped different we can abort.
            if not differs:
                return False

        # All shape.
        return True

    @lru_cache
    def check_mark_attachment(self, input: str) -> bool:
        """
        Check if the input string, usually a single character or character
        plus n marks, has correct shaping from mark attachements by
        checking if all mark glyphs are positioned.
        """

        # Compose, then fully decompose the input.
        input = uni.normalize("NFC", input)
        chars = parse_chars(input, decompose=True, retain_decomposed=False)

        # Get a harfbuzz buffer's info to inspect shaping.
        data = self.get_glyph_data("".join(chars))

        if len(input) == 1 and len(chars) == 1:
            return True

        if len([mark for mark in chars if uni.category(mark).startswith("M")]) == 0:
            log.debug(f"No marks in the input sequence '{input}', passes")
            return True

        if len(input) == 1 and len(chars) == 2:
            # An character with natural composition to single codepoint was
            # passed. If the font supports this composition, the buffer
            # sequence will be the single composed codepoint.

            # TBD not sure if harfbuzz can be made to not make this
            # normalization so we could explicitly check for the components'
            # positioning.

            if len(data) == 1:
                return True

        non_marks = {
            self.font.get_nominal_glyph(ord(c)): c
            for c in chars
            if not uni.category(c).startswith("M")
        }

        missing_from_font = []
        missing_positioning = []
        for glyph_info, glyph_position in data:
            if glyph_info.codepoint in non_marks.keys():
                continue

            # No such glyph in the font.
            # For regular check runs this should never trigger, since character
            # sets are checked first.
            # TODO maybe this should even be a raised Exception?
            if glyph_info.codepoint == 0:
                missing_from_font.append(glyph_info.codepoint)
                continue

            # This appears to be a unpositioned mark!
            if glyph_position.x_offset == 0 and glyph_position.y_offset == 0:
                missing_positioning.append(glyph_info.codepoint)
                continue

        if missing_from_font != []:
            names = ", ".join(self.names_for_codepoints(missing_from_font))
            log.debug(
                f"Mark shaping for '{input}' is missing for font glyph names '{names}'"
            )
            return False

        if missing_positioning != []:
            names = ", ".join(self.names_for_codepoints(missing_positioning))
            log.debug(
                f"Mark positioning for '{input}' failed for font glyph names '{names}'"
            )
            return False

        return True
