"""
A CLI script to check hyperglot.yaml is well-formed, called with:
$ hyperglot-validate
"""
import logging
import colorlog
import yaml
import os
import re
import unicodedata2
from .languages import Languages
from .parse import (parse_chars, prune_superflous_marks)
from . import (STATUSES, VALIDITYLEVELS)

handler = colorlog.StreamHandler()
handler.setFormatter(colorlog.ColoredFormatter('%(log_color)s%(message)s'))
log = colorlog.getLogger(__name__)
log.setLevel(logging.DEBUG)
log.addHandler(handler)

print()
print("No color = FYI")
print("Green = FYI, but worth reviewing")
print("Yellow = Might need fixing")
print("Red = Requires fixing")
print()

ISO_639_3 = "../../other/iso-639-3.yaml"
log.debug("Loading iso-639-3.yaml for names and macro language checks")
try:
    iso_db = os.path.abspath(os.path.join(os.path.dirname(__file__),
                                          ISO_639_3))
    with open(iso_db) as f:
        iso_data = yaml.load(f, Loader=yaml.Loader)
except Exception as e:
    log.error(e)
    import sys
    sys.exit()


def check_yaml():

    try:
        log.debug("yaml structure ok")
        # Use prune=False to validate the orthographies raw
        return Languages(prune=False, validity=VALIDITYLEVELS[0])
    except yaml.scanner.ScannerError as e:
        log.error("Malformed yaml:")
        print(e)
    except yaml.parser.ParserError as e:
        log.error("Malformed yaml:")
        print(e)


def check_types(Langs):
    for iso, lang in Langs.items():
        if "includes" in lang:
            if not check_is_valid_list(lang["includes"]):
                log.error("'%s' has invalid list 'includes'" % iso)

        if "source" in lang:
            if not check_is_valid_list(lang["source"]):
                log.error("'%s' has invalid list 'source'" % iso)

        if "orthographies" in lang:
            if not check_is_valid_list(lang["orthographies"]):
                log.error("'%s' has invalid list 'orthographies'" % iso)

            for o in lang["orthographies"]:
                if "base" in o:
                    if iso == "arg":
                        chars = list(o["base"].replace(" ", ""))
                        for i, c in enumerate(chars):
                            if unicodedata2.category(c).startswith("Z"):
                                log.error("'%s' has invalid whitespace "
                                          "characters '%s' at %d" %
                                          (iso, unicodedata2.name(c), i))

                    if not check_is_valid_glyph_string(o["base"]):
                        log.error("'%s' has invalid 'base' glyph list"
                                  % iso)

                if "auxiliary" in o:
                    if not check_is_valid_glyph_string(o["auxiliary"]):
                        log.error("'%s' has invalid 'auxiliary' glyph list"
                                  % iso)

                allowed = ["autonym", "inherit", "script", "base",
                           "auxiliary", "numerals", "status", "note",
                           "preferred_as_group"]
                invalid = [k for k in o.keys() if k not in allowed]
                if len(invalid):
                    log.warn("'%s' has invalid orthography keys: '%s'" %
                             (iso, "', '".join(invalid)))

            primary_orthography = [o for o in lang["orthographies"]
                                   if "status" in o and
                                   o["status"] == "primary"]
            if len(primary_orthography) == 0:
                log.error("'%s' has no primary orthography" % iso)

        if "name" not in lang and "preferred_name" not in lang:
            log.error("'%s' has neither 'name' nor 'preferred_name'" % iso)

        if "name" in lang and "preferred_name" in lang and \
                lang["name"] == lang["preferred_name"]:
            log.error("'%s' has 'name' and 'preferred_name', but they are "
                      "identical" % iso)

        if "status" in lang and lang["status"] not in STATUSES:
            log.error("'%s' has an invalid 'status'" % iso)

        if "validity" not in lang:
            log.warn("'%s' is missing 'validity'" % iso)

        if "validity" in lang and lang["validity"] not in VALIDITYLEVELS:
            log.error("'%s' has invalid 'validity'" % iso)


def check_is_valid_list(item):
    """
    item should be a list and should not be empty
    """
    if type(item) is not list or len(item) < 1:
        return False

    return True


def check_is_valid_glyph_string(glyphs):
    """
    a string of glyphs like "a b c d e f" should be single-space separated
    single unicode characters
    """
    if type(glyphs) is not str or len(glyphs) < 1:
        log.error("Do not use empty glyph sequences")
        return False

    if re.findall(r"\n", glyphs):
        log.error("Glyph sequences should not contain line breaks")
        return False

    if re.findall(r" {2,}", glyphs):
        log.error("More than single space in '%s'" % glyphs)
        return False

    pruned, removed = prune_superflous_marks(glyphs)
    if len(removed) > 0:
        log.error("Superflous marks that are implicitly extracted via "
                  "decomposition: '%s'" % "','".join(removed))
        return False

    return True


def check_is_valid_combation_string(combos):
    """
    combinations should be quote-wrapped and each glyph wrapped in {}

    @example: '{а̄}{е̄}{ә̄}{о̄}{ы̄}'
    """
    if type(combos) is not str or len(combos) == 0:
        return False

    if re.findall(r"\s", combos):
        log.error("'combination' may not contain white space")
        return False

    # Remove beginning {, ending }, or pairs of }{ — if any { or } remain,
    # there was a "syntax" error in the data
    removed = re.sub(r"(^\{)|(\}\{)|(\}$)", "", combos)
    if re.findall(r"\{|\}", removed):
        log.error("'combination' has invalid pattern of curly braces")
        return False

    return True


def check_names(Langs):
    for iso, lang in Langs.items():
        if "orthographies" in lang:
            for o in lang["orthographies"]:
                if "base" not in o and "inherit" not in o:
                    log.error("'%s' has an orthography which is missing a "
                              "'base' attribute" % iso)
                    continue

                if "autonym" not in o:
                    continue

                if "script" not in o:
                    log.error("'%s' has no 'script' attribute" % iso)
                    continue

                if "inherit" in o:
                    if not check_inheritted(o["inherit"], o["script"], Langs):
                        log.error("'%s' has an orthography which inherits "
                                  "from '%s', but that is not a valid or "
                                  "existing language" %
                                  (iso, o["inherit"]))
                    continue
                autonym_ok, chars, missing = check_autonym_spelling(o)
                if not autonym_ok:
                    log.warn("'%s' has invalid autonym '%s' which cannot "
                             "be spelled with that orthography's charset "
                             "(base + auxiliary) '%s' - missing '%s'"
                             % (iso, o["autonym"], "".join(chars),
                                 "".join(missing)))

        if iso not in iso_data.keys():
            log.error("'%s' not found in iso data" % iso)
        else:
            if "names" in iso_data[iso]:
                if lang["name"] not in iso_data[iso]["names"]:
                    log.info("'%s' name ('%s') differs from iso data ('%s')"
                             % (iso, lang["name"],
                                ", ".join(iso_data[iso]["names"])))
            else:
                log.warning("'%s' has no 'names' attribute in iso data"
                            % iso)


def check_inheritted(iso, script, Langs):
    if len(iso) != 3:
        log.warning("'%s' not a valid 3-letter iso code to inherit from" %
                    iso)
        return False
    if iso not in Langs.keys():
        log.warning("'%s' not found in database" % iso)
        return False

    parent = Langs[iso]
    if "orthographies" not in parent:
        log.warning(
            "Cannot inherit from '%s' — has no orthographies" % parent)
        return False

        has_valid_orthography = False
        for o in "orthographies":
            if "base" in o and "script" in o and o["script"] == script:
                has_valid_orthography = True
        if not has_valid_orthography:
            return False

    return True


def check_macrolanguages(Langs):
    # Compare with ISO data
    for iso, lang in iso_data.items():
        for name in lang["names"]:
            if "macrolanguage" in name:
                if iso not in Langs.keys():
                    log.info("'%s' is marked as macrolanguage in iso "
                             "data, but does not exist in hyperglot "
                             "data" % iso)
                    continue
                if not check_includes(Langs[iso]):
                    log.error("'%s' is marked as macrolanguage in the iso "
                              "data, but has no 'includes'." % iso)

    for iso, lang in Langs.items():
        if "includes" in lang:
            # Skip checking included languages if this language is preferred as
            # individual language
            if "preferred_as_individual" not in lang:
                continue

            if lang["preferred_as_individual"] is True:
                continue

            for i in lang["includes"]:
                if i not in Langs.keys():
                    logging.error("'%s' includes language '%s' but it was "
                                  "missing from the data" % (iso, i))


def check_includes(lang):
    if "includes" not in lang:
        return False

    if type(lang["includes"]) is not list:
        return False

    if len("includes") < 1:
        return False

    return True


def check_autonym_spelling(ort):
    chars = parse_chars(ort["base"])
    if "auxiliary" in ort:
        chars = chars + parse_chars(ort["auxiliary"])
    chars = set(chars)

    # Use lowercase no non-word-chars version of autonym
    autonym = ort["autonym"].lower()
    autonym = re.sub(r"\W", "", autonym)
    autonym_chars = parse_chars(autonym)
    autonym_chars = set(autonym_chars)

    missing = list(autonym_chars.difference(chars))

    return autonym_chars.issubset(chars), list(chars), missing


def validate():
    Langs = check_yaml()
    check_types(Langs)
    check_names(Langs)
    check_macrolanguages(Langs)
