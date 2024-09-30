import logging
import unicodedata2 as uni

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
    priority = 75
    logger = logging.getLogger("hyperglot.reporting.marks")

    def check(self, orthography, checker, **kwargs):
        if not orthography.combinations:
            return True

        for c in orthography.combinations.keys():
            if not self.check_cluster_mark_attachment(c, checker.shaper):
                return False
        return True

    def check_cluster_mark_attachment(self, cluster: str, shaper: Shaper) -> bool:

        missing_from_font = [m for m in cluster if shaper.font.get_nominal_glyph(ord(m)) is None]
        if missing_from_font != []:
            log.debug(
                f"Mark shaping for cluster '{cluster}' failed, "
                "missing %d %s"
                % (
                    len(missing_from_font),
                    "glyphs" if len(missing_from_font) > 1 else "glyph",
                )
            )
            return False

        data = shaper.get_glyph_data(cluster)
        chars = list(cluster)

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

        missing_positioning = []
        for glyph_info, glyph_position in data:

            # If the buffer codepoint is no mark
            if glyph_info.codepoint in non_marks.keys():
                continue

            # If the buffer codepoint is not in marks
            if glyph_info.codepoint not in marks.keys():
                continue

            # This appears to be a unpositioned mark!
            if glyph_position.x_offset == 0 and glyph_position.y_offset == 0:
                missing_positioning.append(glyph_info.codepoint)

        if missing_positioning != []:
            missing = [shaper.font.get_glyph_name(m) for m in missing_positioning]
            missing = [m for m in missing if m is not None]
            msg = f"Mark positioning for cluster '{cluster}' failed."
            if len(missing) > 0:
                msg += " Unpositioned marks: " + ", ".join(missing)
            
            log.info(msg)

            # For now this yields too many false positives for base + mark where
            # the two are not linked by anchors, but the mark simply renders
            # without offset "in the right" place shifted by its negative LSB.

            # return False

        return True
