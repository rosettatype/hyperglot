import logging

from hyperglot.checkbase import CheckBase
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
    logger = logging.getLogger("hyperglot.reporting.halfforms")

    def check(self, orthography, checker, **kwargs):
        for h in filter(self.filter_halfforms, orthography.combinations):
            if not self.check_halfform(h, checker.shaper):
                return False
        return True

    def check_halfform(self, input: str, shaper: Shaper) -> bool:
        """
        Check a provided halfform shapes by appending ZWJ and confirming Virama
        gets consumed.
        """

        virama_cp = shaper._get_font_cp(self.VIRAMA)

        if virama_cp is False:
            log.debug("Font contains no Virama, cannot form halfform.")
            return False

        # Check if the rendered sequence still contains VIRAMA
        for glyphinfo in shaper.get_glyph_data(input + self.ZWJ):
            if glyphinfo[0].codepoint == virama_cp:
                log.warning(f"Halfform does not shape, in '{input}'")
                return False

        return True

    def filter_halfforms(self, cluster: str) -> bool:
        return (
            len(cluster) == 2
            and cluster[0] in self.BRAHMIC_CATEGORIES["C"]
            and cluster[1] == self.VIRAMA
        )
