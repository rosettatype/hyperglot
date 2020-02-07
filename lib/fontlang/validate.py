"""
A CLI script to check rosetta.yaml is well-formed
"""
import logging
import yaml
import os
import re
from .languages import Languages, parse_combinations

# VALID_TODOS = ["done", "weak", "todo", "strong"]

# note that "secondary" as status is also used, but on orthographies!
VALID_STATUS = ["historical", "constructed"]

ISO_639_3 = "../../data/iso-639-3.yaml"
logging.info("Loading iso-639-3.yaml for names and macro language checks")
try:
    iso_db = os.path.abspath(os.path.join(os.path.dirname(__file__),
                                          ISO_639_3))
    with open(iso_db) as f:
        iso_data = yaml.load(f, Loader=yaml.Loader)
except Exception as e:
    logging.error(e)
    import sys
    sys.exit()


def check_yaml():
    logging.info("Checking yaml structure...")

    try:
        return Languages()
    except yaml.scanner.ScannerError as e:
        logging.error("Malformed yaml:")
        print(e)
    except yaml.parser.ParserError as e:
        logging.error("Malformed yaml:")
        print(e)


def check_types(Langs):
    for iso, lang in Langs.items():
        if "includes" in lang:
            if not check_is_valid_list(lang["includes"]):
                logging.error("'%s' has invalid list 'includes'" % iso)

        if "source" in lang:
            if not check_is_valid_list(lang["source"]):
                logging.error("'%s' has invalid list 'source'" % iso)

        if "orthographies" in lang:
            if not check_is_valid_list(lang["orthographies"]):
                logging.error("'%s' has invalid list 'orthographies'" % iso)

            for o in lang["orthographies"]:
                if "base" in o:
                    if not check_is_valid_glyph_string(o["base"]):
                        logging.error("'%s' has invalid 'base' glyph list"
                                      % iso)

                if "combinations" in o:
                    if not check_is_valid_combation_string(o["combinations"]):
                        logging.error("'%s' has invalid 'combination' string"
                                      % iso)

        if "name" not in lang and "preferred_name" not in lang:
            logging.error("'%s' has neither 'name' nor 'preferred_name'" % iso)

        if "name" in lang and "preferred_name" in lang and \
                lang["name"] == lang["preferred_name"]:
            logging.error("'%s' has 'name' and 'preferred_name', but they are "
                          "identical" % iso)

        # if "todo_status" in lang and lang["todo_status"] not in VALID_TODOS:
        #     logging.error("'%s' has an invalid 'todo_status'" % iso)

        if "status" in lang and lang["status"] not in VALID_STATUS:
            logging.error("'%s' has an invalid 'status'" % iso)


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
        return False

    if re.findall(r" {2,}", glyphs):
        logging.error("More than single space in '%s'" % glyphs)
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
        logging.error("'combination' may not contain white space")
        return False

    # Remove beginning {, ending }, or pairs of }{ — if any { or } remain,
    # there was a "syntax" error in the data
    removed = re.sub(r"(^\{)|(\}\{)|(\}$)", "", combos)
    if re.findall(r"\{|\}", removed):
        logging.error("'combination' has invalid pattern of curly braces")
        return False

    return True


def check_names(Langs):
    for iso, lang in Langs.items():
        if "orthographies" in lang:
            for o in lang["orthographies"]:
                if "base" not in o and "inherit" not in o:
                    logging.error("'%s' has an orthography which is missing a "
                                  "'base' attribute" % iso)
                    continue

                if "autonym" not in o:
                    continue

                if "script" not in o:
                    logging.error("'%s' has no 'script' attribute" % iso)
                    continue

                if "inherit" in o:
                    if not check_inheritted(o["inherit"], o["script"], Langs):
                        logging.error("'%s' has an orthography which inherits "
                                      "from '%s', but that is not a valid or "
                                      "existing language" %
                                      (iso, o["inherit"]))
                    continue

                autonym_ok, chars, missing = check_autonym_spelling(o)
                if not autonym_ok:
                    logging.error("'%s' has invalid autonym '%s' which cannot "
                                  "be spelled with that orthography's charset "
                                  "'%s' - missing '%s'"
                                  % (iso, o["autonym"], "".join(chars),
                                     "".join(missing)))

        if iso not in iso_data.keys():
            logging.error("'%s' not found in iso data" % iso)
        else:
            if "names" in iso_data[iso]:
                if lang["name"] not in iso_data[iso]["names"]:
                    logging.warning("'%s' name ('%s') not found in iso data "
                                    "('%s')"
                                    % (iso, lang["name"],
                                       ", ".join(iso_data[iso]["names"])))
            else:
                logging.warning("'%s' has no 'names' attribute in iso data"
                                % iso)


def check_inheritted(iso, script, Langs):
    if len(iso) != 3:
        logging.warning("'%s' not a valid 3-letter iso code to inherit from" %
                        iso)
        return False
    if iso not in Langs.keys():
        logging.warning("'%s' not found in database" % iso)
        return False

    parent = Langs[iso]
    if "orthographies" not in parent:
        logging.warning(
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
    for iso, lang in iso_data.items():
        for name in lang["names"]:
            if "macrolanguage" in name:
                if iso not in Langs.keys():
                    logging.warning("'%s' is marked as macrolanguage in iso "
                                    "data, but does not existing in rosetta "
                                    "data" % iso)
                    continue
                if not check_includes(Langs[iso]):
                    logging.error("'%s' is marked as macrolanguage in the iso "
                                  "data, but has no 'includes'." % iso)

    # for iso, lang in Langs.items():
    #     if "includes" in lang:
    #         if not check_includes_are_valid(lang, Langs):
    #             logging.error("'%s' has invalid included languages" % iso)


# def check_includes_are_valid(lang, Langs):
#     keys = Langs.keys()
#     for l in lang["includes"]:
#         if l not in keys:
#             logging.error("Included language '%s' not found in data" % (l))
#             return False
#     return True


def check_includes(lang):
    if "includes" not in lang:
        return False

    if type(lang["includes"]) is not list:
        return False

    if len("includes") < 1:
        return False

    return True


def check_autonym_spelling(ort):
    chars = ort["base"]
    if "auxiliary" in ort:
        chars = chars + ort["auxiliary"]
    if "combinations" in ort:
        comb = parse_combinations(ort["combinations"])
        if comb:
            chars = chars + " ".join(comb)

    # It is implied, but force unique to be sure
    chars = set(chars)

    # Use the autonym in lowercase and without any "non-word" marks (hyphens,
    # apostrophes, etc.)
    ignore_punctuation = re.compile("|".join(["\W", "ʼ", "ʻ"]))  # noqa
    autonym = ort["autonym"].lower()
    autonym = ignore_punctuation.sub("", autonym)

    autonym = set(autonym)
    missing = list(autonym.difference(chars))

    return autonym.issubset(chars), list(chars), missing


def validate():
    logging.getLogger().setLevel(logging.DEBUG)
    Langs = check_yaml()
    check_types(Langs)
    check_names(Langs)
    check_macrolanguages(Langs)
