import logging

from hyperglot.checkbase import CheckBase


class Check(CheckBase):

    conditions = {
        "script": "Devanagari",
        "attributes": ("combinations",),
    }
    requires_font = True
    priority = 50
    logger = logging.getLogger("hyperglot.reporting.halfforms")

    def check(self, orthography, checker, **kwargs):
        print("Run Brahmi halfforms check")
        return True
