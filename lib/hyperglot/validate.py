"""
A CLI script to check hyperglot.yaml is well-formed, called with:
$ hyperglot-validate
Note that the python library itself is tested with pytest, whereas this is more
of a check for the data files to be used when entering and saving data. This
also saves the data in canonical order and formatting in order to keep it
changes reliable in source control.
"""
import os
import re
import yaml
import click
import logging
import pprint
import colorlog
import unicodedata as uni
from typing import Tuple

from hyperglot.language import Language
from hyperglot.languages import Languages
from hyperglot.orthography import Orthography
from hyperglot.loader import load_scripts_data
from hyperglot.parse import parse_chars
from hyperglot import (
    __version__, 
    LanguageStatus, 
    LanguageValidity, 
    OrthographyStatus,
)

handler = colorlog.StreamHandler()
handler.setFormatter(colorlog.ColoredFormatter('%(log_color)s%(message)s'))
log = colorlog.getLogger(__name__)
log.setLevel(logging.WARNING)
log.addHandler(handler)


UNICODE_CONFUSABLES = {
    # Revise as needed

    "Latin": ["а", "с", "ԁ", "е", "һ", "і", "ј", "ʝ", "κ", "ӏ", "ո", "о", "ο", 
              "օ", "р", "զ", "ʂ", "т", "υ", "ս", "ν", "ѵ", "х", "у", "ʐ",
              "А", "В", "Е", "К", "М", "Н", "О", "Р", "С", "Т", "У", "Х"
              ],

    "Cyrillic": ["a", "c", "d", "e", "h", "j" "k", "K", "o", "u", "y",
                 "A", "B", "E", "K", "M", "H", "O", "P", "C", "T", "Y", "X"],
                 
    # TODO Greek maybe less prevailant because less Greek script languages are
    # added, but large potential for confusion with all sorts of math symbols
}

def is_yaml_list_str(input:str) -> bool:
    if type(input) != str:
        return False
    
    return input.startswith("['") and input.endswith("']")

def check_yaml():
    log.debug("YAML file structure ok and can be read")
    return Languages(validity=LanguageValidity.TODO.value)


def check_types(Langs:Languages) -> None:
    for iso, lang in Langs.items():
        if iso == "default":
            continue

        if "includes" in lang:
            if not check_is_yaml_list(lang["includes"]):
                log.error(f"'{iso}' has invalid list 'includes'")

        if "sources" not in lang or lang["sources"] is None or lang["sources"] == []:
           log.error(f"'{iso}' is missing 'sources'") 
        else:
            if not check_is_yaml_list(lang["sources"]):
                log.error(f"'{iso}' has invalid list 'sources'")

        if "contributors" in lang:
            if lang["contributors"] is None:
                log.warning(f"'{iso}' is without 'contributors'")
            else:
                if not check_is_yaml_list(lang["contributors"]):
                    log.error(f"'{iso}' has invalid list 'contributors'")

        if "reviewers" in lang:
            # Reviewers is optional
            if lang["reviewers"] is not None:
                if not check_is_yaml_list(lang["reviewers"]):
                    log.error(f"'{iso}' has invalid list 'reviewers'")

        if "orthographies" in lang:
            if not check_is_yaml_list(lang["orthographies"]):
                log.error(f"'{iso}' has invalid list 'orthographies'")

            preferred_as_group = [o for o in lang["orthographies"] 
                                  if "preferred_as_group" in o and o["preferred_as_group"] is True]
            if len(preferred_as_group) == 1:
                log.error(
                    "'%s': Cannot set sole orthography as 'preferred_as_group', only two or " 
                    "more orthographies can be treated as group."
                    % iso
                )

            for o in lang["orthographies"]:
                if "script" not in o:
                    log.error(f"Orthography in '{iso}' is missing 'script'")

                if "base" in o:
                    if not check_is_valid_glyph_string(o["base"], iso):
                        log.error("'%s' has invalid 'base' glyph list: '%s'"
                                  % (iso, o["base"]))

                if "auxiliary" in o:
                    if not check_is_valid_glyph_string(o["auxiliary"], iso):
                        log.error("'%s' has invalid 'auxiliary' glyph list"
                                  % iso)

                allowed = ["autonym", "script", "base", "marks",
                           "auxiliary", "status", "note",
                           "numerals", "punctuation", "currency",
                           "preferred_as_group",
                           "design_requirements", "design_alternates",
                           "script_iso"]
                invalid = [k for k in o.keys() if k not in allowed]
                if len(invalid):
                    log.warning("'%s' has invalid orthography keys: '%s'" %
                                (iso, "', '".join(invalid)))

                if "design_requirements" in o and \
                        type(o["design_requirements"]) is not list and \
                            not is_yaml_list_str(o["design_requirements"]):
                    log.error("'%s' has a 'design_requirements' which is not "
                              "a list: %s" % (iso, o["design_requirements"]))

                if "status" not in o:
                    log.error("'%s' has an orthography (script '%s') that is "
                              "missing 'status'" % (iso, o["script"]))
                else:
                    if o["status"] not in OrthographyStatus.values() \
                        and o["status"] is not None:
                        log.error("'%s' has an orthography status '%s' which "
                                  "is invalid, should be one of %s" %
                                  (iso, o["status"],
                                   ", ".join(OrthographyStatus.values())))
                
                if "preferred_as_group" in o:
                    if type(o["preferred_as_group"]) != bool:
                        log.error(
                            "'%s' has an orthography with 'preferred_as_group'"
                            " which is not boolean: '%s'." %
                            (iso, o["preferred_as_group"])
                        )

            primary_orthography = [o for o in lang["orthographies"]
                                   if "status" in o and
                                   o["status"] == "primary"]
            
            if len(primary_orthography) == 0 and \
                lang["status"] == LanguageStatus.LIVING.value:
                log.error("'%s' has no primary orthography" % iso)

        if "name" not in lang and "preferred_name" not in lang:
            log.error("'%s' has neither 'name' nor 'preferred_name'" % iso)

        if "name" in lang and "preferred_name" in lang \
                and lang["name"] == lang["preferred_name"]:
            log.error("'%s' has 'name' and 'preferred_name', but they are "
                      "identical" % iso)
                
        if "status" in lang:
            if lang["status"] not in [s.value for s in LanguageStatus] \
                and lang["status"] is not None:
                log.error(
                    "'%s' has invalid 'status' '%s'" % (iso, lang["status"])
                )

        if "validity" not in lang:
            log.warning(f"'{iso}' is missing 'validity'")

        if "validity" in lang and lang["validity"] not in LanguageValidity.values():
            log.error(f"'{iso}' has invalid 'validity'")

        if "speakers" in lang and lang["speakers"] is not None:
            if (re.search(r"[^\d]", str(lang["speakers"]))):
                log.error("'%s' has invalid 'speakers' '%s' - only numbers "
                          "are allowed" %
                          (iso, lang["speakers"]))


def check_is_yaml_list(item) -> bool:
    """
    item should be a list and should not be empty
    """
    if type(item) is not list or len(item) < 1:
        return False

    return True


def check_is_valid_glyph_string(glyphs:str, iso:str=None) -> bool:
    """
    a string of glyphs like "a b c d e f" should be single-space separated
    single unicode characters
    """

    if re.findall(r"\n", glyphs):
        log.error("Glyph sequences should not contain line breaks")
        return False

    if re.findall(r" {2,}", glyphs):
        log.error("More than single space in '%s'" % glyphs)
        log.error(pprint.pformat([g for g in re.findall(r" {2,}", glyphs)]))
        return False
    
    if re.findall(r",+[^,]*,+", glyphs):
        log.error("Characters should be space separated, found commas: '%s'" %
                  glyphs)
        return False

    for c in glyphs:
        if uni.category(c) == "Sk":
            log.warning("'%s' contains modifier symbol '%s' in characters. It "
                        "is very likely this should be a combining mark "
                        "instead." % (iso, c))

    return True


def check_names(Langs:Languages, iso_data:dict) -> None:
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

                if o["script"] not in load_scripts_data():
                    log.error(
                        "'%s' has orthography with new/unknown/misspelled "
                        "script '%s' — add the script mapping to "
                        "lib/extra_data/script-names.yaml or fix the typo."
                        % (iso, o["script"])
                    )

                autonym_ok, chars, missing = check_autonym_spelling(o)
                if not autonym_ok:
                    all_chars = "".join(chars)
                    log.warning("'%s' has invalid autonym '%s' which cannot "
                                "be spelled with that orthography's charset - "
                                "missing '%s'" %
                                (iso, o["autonym"], "".join(missing)))

        if iso not in iso_data.keys():
            if iso != "default":
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


def check_inheritted(iso:str, script:str, Langs:Languages):
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

    return True


def check_macrolanguages(Langs:Languages, iso_data:dict):
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
                    log.error("'%s' includes language '%s' but it was "
                              "missing from the data" % (iso, i))


def check_includes(lang:Language ) -> bool:
    if "includes" not in lang:
        return False

    if type(lang["includes"]) is not list:
        return False

    if len("includes") < 1:
        return False

    return True


def check_autonym_spelling(ort:Orthography) -> Tuple[list, list, list]:
    all = " ".join(ort.base + ort.auxiliary + ort.base_marks + ort.auxiliary_marks)
    chars = parse_chars(all) + parse_chars(ort["marks"])
    chars = [c.lower() for c in chars]

    # Use lowercase no non-word-chars version of autonym
    if "autonym" not in ort or ort["autonym"] is None:
        return True, None, None
    autonym = ort["autonym"].lower()
    autonym = re.sub(r"\W", "", autonym)
    autonym_chars = parse_chars(autonym)
    autonym_chars = set(autonym_chars)

    missing = list(autonym_chars.difference(chars))

    return autonym_chars.issubset(chars), list(chars), missing


def check_script_characters(Langs:Languages) -> None:
    for iso in Langs.keys():
        Lang = Langs[iso]
        if "orthographies" not in Lang:
            continue
        for o in Lang["orthographies"]:
            o = Orthography(o)

            if o.script not in UNICODE_CONFUSABLES.keys():
                continue

            all = o.base_chars + o.auxiliary_chars
            for char in all:
                if char in UNICODE_CONFUSABLES[o.script]:
                    log.warning(
                        f"'{iso}' ({o.script}) has a unicode lookalike character: "
                        f"'{char}' ({hex(ord(char))} - {uni.name(char)}) "
                        "— confirm the character is of the right script!"
                    )

@click.command()
@click.option("-v", "--verbose", is_flag=True, default=False)
def validate(verbose):
    validate_data(verbose)

def validate_data(verbose:bool = False) -> None:

    log.setLevel(logging.WARNING)
    
    if verbose:
        log.setLevel(logging.DEBUG)
        logging.getLogger("hyperglot.languages").setLevel(logging.DEBUG)
        logging.getLogger("hyperglot.languagee").setLevel(logging.DEBUG)
        print("Hyperglot version: %s" % __version__)

    ISO_639_3 = "../../other/iso-639-3.yaml"
    try:
        iso_db = os.path.abspath(os.path.join(os.path.dirname(__file__),
                                              ISO_639_3))
        with open(iso_db) as f:
            iso_data = yaml.load(f, Loader=yaml.Loader)
    except Exception as e:
        log.error(e)
        log.error("hyperglot-save and hyperglot-validate are intended to be "
                  "run only if the package was install in editable mode with "
                  "pip -e")
        import sys
        sys.exit()

    print()
    log.debug("No color = FYI")
    log.info("Green = FYI, but worth reviewing")
    log.warning("Yellow = Might need fixing")
    log.error("Red = Requires fixing")

    print()
    log.debug("Loading iso-639-3.yaml for names and macro language checks")

    try:
        Langs = check_yaml()
    except KeyError as e:
        log.error(f"Issues in data files: {e}")
        return

    check_types(Langs)
    check_names(Langs, iso_data)
    check_macrolanguages(Langs, iso_data)
    check_script_characters(Langs)
