from functools import cache
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

        features = {"kern": True, "liga": True}

        hb.shape(self.font, buffer, features)

        return buffer

    @cache
    def get_glyph_data(self, text: str) -> List:
        """
        Shape a text in a new buffer and return the buffer's glyph infos.
        """
        buffer = self.shape(text)
        return buffer.glyph_infos, buffer.glyph_positions

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

        glyph_info, _ = self.get_glyph_data(string)
        glyph_id = glyph_info[0].codepoint

        # The glyph is not in the font at all.
        if glyph_id == 0:
            return False

        # The plain/zwj are arrays of sequences of the unicode in question
        # joined based on its unicode joining_type flags; check through all
        # possible join sequences to confirm all are supported in the font.
        for i in range(0, len(plain)):
            # Get the buffer info of the sequence.
            buffer_glyph_info_plain, _ = self.get_glyph_data(plain[i])
            buffer_glyph_info_zwj, _ = self.get_glyph_data(zwj[i])
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
                # shaping has been applied in the buffer
                if plain_codepoint != zwj_codepoint:
                    differs = True

            # If this sequence failed to be shaped different we can abort
            if not differs:
                return False

        # All shape
        return True

    @cache
    def check_mark_attachment(self, input: str) -> bool:
        """
        Check if the input string, usually a single character or character
        plus n marks, has correct shaping from mark attachements by
        checking if all mark glyphs are positioned.
        """

        # Decompose the input, get a harfbuzz buffer's info to inspect
        chars = parse_chars(input, decompose=True, retain_decomposed=False)
        infos, positions = self.get_glyph_data("".join(chars))

        input_info = {}
        # For gathering unicode info about all input sequence memebers use
        # the retain_decomposed as this will set the data (such as font
        # codepoint) also for the normalized, not-decomposed, input
        for c in parse_chars(input, decompose=True, retain_decomposed=True):
            char_info, _ = self.get_glyph_data(c)
            input_info[char_info[0].codepoint] = (c, uni.category(c))

        if len([mark for mark in chars if uni.category(mark).startswith("M")]) == 0:
            log.debug(f"No marks in the input sequence '{input}', passes")
            return True

        if len(input) == 1 and len(chars) == 1:
            log.debug(
                f"Cannot check mark positioning of single character input "
                f"sequence '{input}', passes"
            )
            return True

        if len(input) == 1 and len(chars) == 2:
            # An character with natural composition to single codepoint was
            # passed. If the font supports this composition, the buffer
            # sequence will be the single composed codepoint.

            # TBD not sure if harfbuzz can be made to not make this
            # normalization so we could explicitly check for the components'
            # positioning.
            if len(positions) == 1:
                return True

        missing_from_font = []
        missing_positioning = []
        for i in range(0, len(infos)):
            glyph_info = infos[i]
            glyph_positions = positions[i]

            # No such glyph in the font

            # TODO maybe this should even be a raised Exception?
            if glyph_info.codepoint == 0:
                missing_from_font.append(input_info[glyph_info.codepoint])
                continue

            # For font codepoint get unicode ([0]) and category ([1])
            ref = input_info[glyph_info.codepoint]
            is_mark = ref[1].startswith("M")

            # This appears to be a unpositioned mark
            if is_mark and glyph_positions.position == (0, 0, 0, 0):
                missing_positioning.append(ref[0])
                continue

        if missing_from_font != []:
            log.debug(f"Mark shaping for '{input}' is missing '{missing_from_font}'")
            return False

        if missing_positioning != []:
            log.debug(
                f"Mark positioning for '{input}' failed for '{missing_positioning}'"
            )
            return False

        return True
