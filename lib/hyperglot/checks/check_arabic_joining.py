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
        if SupportLevel.AUX.value in options["check"]:
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
    def check_joining(self, unicode: int, shaper: Shaper) -> bool:
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

        # FIXME: This is _odd_. As such, we don't really have to confirm the
        # input unicode, as the coverage check will already have failed, so
        # for now it may be acceptable to just skip this.
        # What is interesting is that this glyph_id == 0 correctly works,
        # except for webfonts. So a font certainly will have a given unicode,
        # but the shaping and accessing of the shaped font codepoint from the
        # harfbuzz buffer will return 0, yielding a false positive.
        # There is tests.test_cli.test_cli_formats that has a confirmation for
        # this.
        #
        # glyph_info = shaper.get_glyph_infos(string)
        # glyph_id = glyph_info[0].codepoint
        # # The glyph is not in the font at all.
        # if glyph_id == 0:
        #     return False

        # It would be _nice_ to be able to check specifically if the base glyph
        # transforms into a init/medi/fina form, but this assumption is not
        # 100% reliable across all fonts, so we just check if the shaping
        # differs just generally.
        for i in range(0, len(plain)):

            # Get the buffer info of the sequence, and compare the codepoints.
            # Note those are font GIDs not, unicodes!
            codes_plain = [g.codepoint for g in shaper.get_glyph_infos(plain[i])]
            codes_joined = [g.codepoint for g in shaper.get_glyph_infos(zwj[i])]

            # If this sequence failed to be shaped different we can abort.
            if not codes_plain != codes_joined:
                return False

        # All shape.
        return True
