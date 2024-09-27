import re
import logging
from typing import List, Tuple

from hyperglot.checkbase import CheckBase
from hyperglot.orthography import Orthography
from hyperglot.shaper import Shaper

log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)


class Check(CheckBase):

    conditions = {
        "script": "Devanagari",
        "attributes": ("combinations",),
    }
    requires_font = True
    priority = 50
    logger = logging.getLogger("hyperglot.reporting.conjuncts")

    def check(self, orthography: Orthography, checker, **kwargs) -> bool:
        """
        the sequence of the consonant Ka, virama, and consonant Pa will result in a conjunct KPa
        Ka + virama + Pa → KPa


        but:

        Without ZWNJ, a conjunct should be rendered (if available):
        Ka + virama + Ka → KKa
        Zero-width non-joiner (ZWNJ, U+200C) ensures virama in the dead consonant is rendered visually:
        Ka + virama + ZWNJ + Ka → Ka + virama + Ka

        and:

        Without ZWJ, a conjunct should be rendered (if available):
        Ka + virama + Ka → KKa
        ZWJ ensures a half form is rendered instead:
        Ka + virama + ZWJ + Ka → K- + Ka

        """
        options = self._get_options(**kwargs)

        if not orthography.combinations:
            return True
        conjuncts = dict(
            filter(self.filter_conjuncts, orthography.combinations.items())
        )
        print("CONJUNCTS", conjuncts)
        if conjuncts == {}:
            return True

        # Iterate all syllables to provide reporting.
        # TODO exit early if no reporting is set

        fails_over_threshold = False

        for conjunct, frequency in conjuncts.items():
            fails = False
            # Ensure no .notdef are left over
            if not self.check_all_render(conjunct, checker.shaper):
                fails = True
                # continue
            if not self.check_conjunct(conjunct, checker.shaper):
                fails = True

            if fails:
                fmt_threshold = str(options["threshold"]).format(".5f")

                if frequency > options["threshold"]:
                    logging.error(
                        f"Conjunct '{conjunct} ({frequency:.5f}) does not shape and does not pass frequency threshold ({fmt_threshold})."
                    )
                    fails_over_threshold = True
                else:
                    logging.warning(
                        f"Conjunct '{conjunct} ({frequency:.5f}) does not shape, but passes threshold ({fmt_threshold})."
                    )

        return not fails_over_threshold

    def filter_conjuncts(self, cluster: Tuple) -> bool:
        """
        From a list of clusters (Orthography.combinations) extract those that
        we deem relevant for conjunct formation checks.
        At the very least this means:
        - contain virama
        - contain at least two consonants
        - the virama is between the consonants, but there may be other characters (marks, vowels)
        """
        cluster = list(cluster[0])
        expect_next = [
            self.BRAHMIC_CATEGORIES["C"],
            [self.VIRAMA],
            self.BRAHMIC_CATEGORIES["C"],
        ]

        # Go through the chars of cluster one by one. Mark if it matches the
        # type of character expected next (while ignoring irrelevant characters)
        # and look for the next. If all have been matched by the end of the
        # loop we have a consonant, followed by virama, followed by consonant.
        while len(cluster) > 0 and len(expect_next) > 0:
            char = cluster.pop(0)
            if char in expect_next[0]:
                expect_next.pop(0)

        return len(expect_next) == 0

    def check_conjunct(self, input: str, shaper: Shaper) -> bool:
        """
        Check for conjunct formation, ensure:
        - consonant + virama + consonant: require virama is consumed
        - consonant + virama + zwnj + consonant: require virama rendered after first consonant
        - consonant + virama + zwj + consonant: require virama is consumed, first consonant is transformed
        """

        input = input.strip()

        if self.VIRAMA not in input:
            log.warning(
                f"No Virama in conjunct '{input}' — this sequence should not be in 'conjuncts'."
            )
            return True

        if input.startswith(self.VIRAMA):
            log.warning(f"Virama found at beginning of cluster '{input}'")
            return True

        if input.endswith(self.VIRAMA):
            log.warning(f"Virama found at end of cluster '{input}'")
            return True

        virama_cp = shaper.font.get_nominal_glyph(0x094D)

        if virama_cp is None:
            log.debug("Font contains no Virama, cannot form cluster.")
            return False

        require_virama_consumed = False
        require_virama_remains = False

        if re.findall(self.VIRAMA + self.ZWNJ, input):
            require_virama_consumed = False
            require_virama_remains = True

        if re.findall(self.VIRAMA + self.ZWJ, input):
            require_virama_consumed = True
            require_virama_remains = False

        has_virama = False

        # Check if the rendered sequence still contains VIRAMA
        for glyphinfo in shaper.get_glyph_data(input):
            if glyphinfo[0].codepoint == virama_cp:
                has_virama = True

        if require_virama_consumed and has_virama:
            log.warning(
                f"C + Virama + ZWJ + C: Virama not consumed when it should have been, in '{input}' ("
                + " ".join(["%s %s" % (c, hex(ord(c))) for c in input])
                + ")"
            )
            return False

        if require_virama_remains and not has_virama:
            log.warning(
                f"C + Virama + ZWNJ + C: Virama not retained when it should have been, in '{input}' ("
                + " ".join(["%s %s" % (c, hex(ord(c))) for c in input])
                + ")"
            )
            return False

        if require_virama_remains and has_virama:
            return True

        if has_virama:
            log.warning(
                f"Conjunct still contains Virama, in '{input}' ("
                + " ".join(["%s %s" % (c, hex(ord(c))) for c in input])
                + ")"
            )
            return False

        return True
