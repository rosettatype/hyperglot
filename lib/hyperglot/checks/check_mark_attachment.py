from functools import lru_cache
import logging
import unicodedata2 as uni

from hyperglot import SupportLevel
from hyperglot.checkbase import CheckBase
from hyperglot.orthography import Orthography
from hyperglot.checker import Checker
from hyperglot.shaper import Shaper
from hyperglot.parse import parse_chars

log = logging.getLogger(__name__)
log.setLevel(logging.WARNING)


class Check(CheckBase):

    conditions = {
        "attributes": ("base", "auxiliary", "mark"),
    }
    requires_font = True
    priority = 30
    logger = logging.getLogger("hyperglot.reporting.marks")

    def check(self, orthography: Orthography, checker: Checker, **kwargs) -> bool:
        """
        Check the mark attachment for the orthography.
        """

        options = self._get_options(**kwargs)

        check_attachment = []

        chars = orthography.base
        if options["supportlevel"] == SupportLevel.AUX.value:
            chars.extend(orthography.auxiliary)

        # Mark positioning needs to at least work for all unencoded
        # base + mark base characters.
        check_attachment.extend([c for c in chars if len(c) > 1])

        # If checking against decomposed characters also base + mark combinations
        # that do not exist precomposed in the characters need to be checked.
        if options["decomposed"]:
            check_attachment.extend([c for c in chars if c not in checker.characters])

        missing_positioning = []

        for c in chars:
            if self.check_mark_attachment(c, checker.shaper) is False:
                missing_positioning.append(c)

        if missing_positioning != []:
            self.logs.append(
                (
                    self.logger,
                    logging.WARNING,
                    len(missing_positioning),
                    "missing mark attachment for: %s" % ", ".join(missing_positioning),
                )
            )
            return False

        return True

    @lru_cache
    def check_mark_attachment(self, input: str, shaper: Shaper) -> bool:
        """
        Check if the input string, usually a single character or character
        plus n marks, has correct shaping from mark attachements by
        checking if all mark glyphs are positioned.
        """

        # Compose, then fully decompose the input.
        input = uni.normalize("NFC", input)
        chars = parse_chars(input, decompose=True, retain_decomposed=False)

        # Get a harfbuzz buffer's info to inspect shaping.
        data = shaper.get_glyph_data("".join(chars))

        if len(input) == 1 and len(chars) == 1:
            return True

        if len([mark for mark in chars if uni.category(mark).startswith("Mn")]) == 0:
            log.debug(f"No non-spacing marks in the input sequence '{input}', passes")
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

        if len(input) > 1 and len(data) == 1:
            # A sequence was entered which resulted in substitution to a single
            # glyph output, like a ccmp transforming a base + mark to a single
            # glyph. We trust this is intentional by the vendor and constitutes
            # a shaped mark.
            return True

        non_marks = {
            shaper.font.get_nominal_glyph(ord(c)): c
            for c in chars
            if not uni.category(c).startswith("Mn")
        }
        marks = {
            shaper.font.get_nominal_glyph(ord(c)): c
            for c in chars
            if uni.category(c).startswith("Mn")
        }

        missing_from_font = 0
        missing_positioning = []
        for glyph_info, glyph_position in data:

            # No such glyph in the font.
            if (
                glyph_info.codepoint == 0
                or shaper.font.get_glyph_name(glyph_info.codepoint) is None
            ):
                missing_from_font = missing_from_font + 1
                continue

            # If the buffer codepoint is no mark
            if glyph_info.codepoint in non_marks.keys():
                continue

            # If the buffer codepoint is not in marks
            if glyph_info.codepoint not in marks.keys():
                continue

            # This appears to be a unpositioned mark!
            if glyph_position.x_offset == 0 and glyph_position.y_offset == 0:
                missing_positioning.append(glyph_info.codepoint)

        if missing_from_font != 0:
            log.debug(
                f"Mark shaping for '{input}' failed, "
                "missing %d %s"
                % (
                    missing_from_font,
                    "glyphs" if missing_from_font > 1 else "glyph",
                )
            )
            return False

        if missing_positioning != []:
            names = ", ".join(shaper.names_for_codepoints(missing_positioning))
            log.debug(
                f"Mark positioning for '{input}' failed, glyphs missing mark positioning: '{names}'"
            )
            return False

        return True
