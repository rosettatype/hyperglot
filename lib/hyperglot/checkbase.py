import logging

from hyperglot import SupportLevel, LanguageValidity
from hyperglot.shaper import Shaper


class CheckBase:

    VIRAMA = chr(0x094D)
    ZWJ = chr(0x200D)
    ZWNJ = chr(0x200C)
    DOTTED_CIRCLE = chr(0x25CC)
    BRAHMIC_CATEGORIES = {
        "+": [chr(0x094D)],
        "V": [
            chr(c)
            for c in list(range(0x0904, 0x0914 + 1))
            + [0x0960, 0x0961]
            + list(range(0x0973, 0x0977 + 1))
        ],
        "C": [
            chr(c)
            for c in list(range(0x0915, 0x0939 + 1))
            + list(range(0x0958, 0x095F + 1))
            + list(range(0x0978, 0x097F + 1))
        ],
        "D": [
            chr(c)
            for c in [0x093A, 0x093B]
            + list(range(0x093E, 0x094C + 1))
            + [0x094E, 0x094F]
            + [0x0955, 0x0956, 0x0957]
            + [0x0962, 0x0963]
        ],
        "M": [chr(0x093C)],
        "m": [chr(c) for c in list(range(0x0900, 0x0903 + 1))],
        "P": [chr(c) for c in [0x093D, 0x0964, 0x0965]],
        "Z": [chr(0x200C)],
        "z": [chr(0x200D)],
    }

    conditions = {
        "script": "Devanagari",
        "attributes": ("combinations",),
    }
    requires_font = False
    priority = 999
    logger = logging.getLogger("hyperglot.reporting.errors")

    def __init__(self):
        # Use any module logger to output code issues, append to self.logs
        # reporting entries that should get output "higher" up in the check run.
        self.logs = []

    def check(self):
        raise NotImplementedError("Checks need to implement check method!")

    def check_all_render(self, input: str, shaper: Shaper) -> bool:
        """
        Check an input string renders in the font without leaving any notdef or
        dotted circles. As a fairly general check this may be useful in multiple
        check implementations.
        """
        dotted_circle_cp = shaper.font.get_nominal_glyph(ord(self.DOTTED_CIRCLE))

        gdata = shaper.get_glyph_data(input)

        if dotted_circle_cp is not False:
            for glyphinfo in gdata:
                if glyphinfo[0].codepoint == dotted_circle_cp:
                    self.logger.debug(f"Shaper buffer contained dotted circle {input}")
                    return False

        for glyphinfo in gdata:
            # TODO TBD is notdef always CP 0 in harfbuzz fonts?
            if glyphinfo[0].codepoint == 0:
                self.logger.debug(f"Shaper buffer contained notdef for {input}")
                return False

        return True

    def _get_options(self, **kwargs):
        """
        Helper to use inside self.check() to default all passed in kwargs with
        these defaults, unless they are set.
        """
        options = {
            "check": [SupportLevel.BASE.value],
            "validity": LanguageValidity.DRAFT.value,
            "decomposed": False,
            "marks": False,
            "report_missing": -1,
            "report_marks": -1,
            "report_joining": -1,
        }

        # Update from call arguments
        options.update(kwargs)

        return options

    def _get_category(self, input: str) -> str:
        if len(input) != 1:
            raise ValueError(f"Cannot get category for '{input}'")

        for category, codepoints in self.BRAHMIC_CATEGORIES.items():
            if input in codepoints:
                return category

        return None
