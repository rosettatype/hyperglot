import logging
from functools import lru_cache

from hyperglot import SupportLevel
from hyperglot.checkbase import CheckBase
from hyperglot.orthography import Orthography
from hyperglot.checker import Checker
from hyperglot.shaper import Shaper
from hyperglot.parse import get_joining_type, join_variants

log = logging.getLogger(__name__)
log.setLevel(logging.WARNING)


class Check(CheckBase):
    """
    Check the joining behavior of all Arabic characters.
    """

    conditions = {
        "script": "Arabic",
        "attributes": (
            "base",
            "auxiliary",
        ),
    }
    requires_font = True
    priority = 40
    logger = logging.getLogger("hyperglot.reporting.joining")

    def check(self, orthography: Orthography, checker: Checker, **kwargs):
        options = self._get_options(**kwargs)

        chars = orthography.base
        if options["supportlevel"] == SupportLevel.AUX.value:
            chars.extend(orthography.auxiliary)

        require_shaping = [
            c for c in chars if get_joining_type(c) in ["D", "R", "L", "T"]
        ]
        if require_shaping == []:
            return True

        missing_shaping = []
        for char in require_shaping:
            if self.check_joining(ord(char), checker.shaper) is False:
                missing_shaping.append(char)

        if missing_shaping != []:
            self.logs.append(
                (
                    self.logger,
                    logging.WARNING,
                    len(missing_shaping),
                    "missing joining forms for: %s" % ", ".join(missing_shaping),
                )
            )
            return False

        return True
    
    @lru_cache
    def check_joining(self, unicode: int, shaper:Shaper) -> bool:
        """
        Check if the string exhibits joining behaviour (shaping differs) by
        comparing its plain version to a version joined with zero width joiners.

        Return True if the shaping differs or the glyph requires no shaping.
        Return False if the shaping remains unchanged but requires joining
        behaviour.
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

        glyph_info = shaper.get_glyph_infos(string)
        glyph_id = glyph_info[0].codepoint

        # The glyph is not in the font at all.
        if glyph_id == 0:
            return False

        # The plain/zwj are arrays of sequences of the unicode in question
        # joined based on its unicode joining_type flags; check through all
        # possible join sequences to confirm all are supported in the font.
        for i in range(0, len(plain)):
            # Get the buffer info of the sequence.
            buffer_glyph_info_plain = shaper.get_glyph_infos(plain[i])
            buffer_glyph_info_zwj = shaper.get_glyph_infos(zwj[i])
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
                    f"({shaper.font.get_glyph_name(plain_codepoint)}) vs "
                    f"{zwj_codepoint} ({shaper.font.get_glyph_name(zwj_codepoint)})"
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
