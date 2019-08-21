"""
Read language data (codes and characters) from different sources.

When run as a script, convert all data to YAMLs.
"""

import csv
import glob
import logging
import os
import re
import unicodedata
import xml.etree.ElementTree as ET
from collections import OrderedDict
from custom_yaml import save_yaml


def parse_unicode_set(s):
    """
    Parse UnicodeSet record used in Unicode CLDR.
    Needs more work, but should be fine to use for most scripts
    except Chinese, Japanese, and other that use ranges.

    Processes escape sequences, assumes XML entities have been
    dealt with when reading the XML. Removes enclosing [].

    Returns a string with sorted characters and separated string
    with character combinations (originally enclosed in {})
    in the main string. Combinations may not be sorted.
    """

    def repl(m):
        return chr(int(m.group(1), 16))

    KNOWN_ESCAPES = OrderedDict([
        ("\\\"", "\""),
        ("\\[", "["),
        ("\\]", "]"),
        ("\\{", "{"),
        ("\\}", "}"),
        ("\\&", "&"),
        ("\\:", ":"),
        ("\\-", "-"),
        ("\\\\", "\\"),
    ])

    # strip brackets
    s = s.lstrip("[").rstrip("]")
    # unicode codepoint escapes - todo (some are done automatically)
    s = re.sub(r"\\U(........)", repl, s)
    s = re.sub(r"\\u(....)", repl, s)
    s = re.sub(r"\\x(..)", repl, s)

    # ranges - todo (currently only used for Chinese, Japanese etc.)

    # escapes
    for k, v in KNOWN_ESCAPES.items():
        s = s.replace(k, v)
    # braces (get a list of required combinations)
    combinations = re.findall(r"\{[^\}]+\}", s)
    # convert to list, ignore braces and spaces
    s = [c for c in list(s) if c not in "{ }"]
    # remove possible duplicates and sort
    s = sorted(list(set(s)))
    # join back into strings
    s = " ".join(s)
    c = " ".join(combinations)
    return s, c


def to_lc(mix, script="Latn"):
    """
    Save only LC versions of glyphs, add the default set for a script.
    """

    az = set("abcdefghijklmnopqrstuvwxyz")
    aya = set("абвгдежзийклмнопрстуфхцчшщъыьэюя")

    lc = []
    for c in mix.replace(" ", ""):
        if c.islower():
            lc += [c]
        elif c == "İ":
            # Account for Idotaccent
            lc += [c]
        elif c.isupper():
            pass
        else:
            lc += [c]
    lc = set(lc)
    # add basic characters
    if script == "Latn":
        lc = lc.union(az)
    elif script == "Cyrl":
        lc = lc.union(aya)
    return " ".join(sorted(list(lc)))


def read_iso_639_3(path):
    """
    Read .tab file for ISO 639-3 and return a dict
    with the ISO 639-3 3-letter language codes as keys.
    """

    d = OrderedDict()
    with open(path, "r", encoding="utf-8") as csvinput:
        reader = csv.DictReader(csvinput, delimiter="\t")
        for row in reader:
            code = row["Id"]
            if code not in d:
                lang = OrderedDict()
                lang["names"] = [row["Ref_Name"]]
                lang["639-2B"] = row["Part2T"]
                lang["639-2T"] = row["Part2B"]
                lang["639-1"] = row["Part1"]
                lang["scope"] = row["Scope"]
                lang["type"] = row["Language_Type"]
                lang["comment"] = row["Comment"]
                d[code] = lang
            else:
                d[code]["names"].append(row["Ref_Name"])
        return d


def read_iso_639_3_retirements(path):
    """
    Read .tab file for ISO 639-3 retirements and return a list
    of the ISO 639-3 3-letter language codes.
    """

    r = []
    with open(path, "r", encoding="utf-8") as csvinput:
        reader = csv.DictReader(csvinput, delimiter="\t")
        for row in reader:
            r.append(row["Id"])
        return r


def read_latin_plus(path):
    """
    Read data from Underwares’s Latin Plus and account for non-iso-639-3
    languages (no code), languages with retired code, and bad formatting.

    Notes:
    - the lists of required characters assume A–Z as default and distinguish
      between uppercase and lowercase.
    - the language names often differ from those in ISO 639-3.
    """

    def get_mapping(txt):
        """
        Get mapping between glyph names and Unicode codepoints.
        """

        mapping = {}
        # line by line, ignore the first
        for li in txt.split("\n")[1:]:
            if li.strip().startswith("#"):
                pass
            elif li.strip() == "":
                pass
            else:
                recs = li.split("\t")
                gn = recs[1]
                u = recs[2]
                # avoid PUA used for ijacute glyph
                if gn.lower() == "ijacute":
                    mapping[gn] = ""
                # convert a unicode string to a character
                if u != "" and len(u) == 4:
                    mapping[gn] = chr(int(u, 16))
        return mapping

    def get_language_info(txt, mapping):
        """
        Read the required glyph names for each language, convert to Unicode
        characters, and return a dict index by correct ISO 639-3 code.

        Ignores:
        Latino sine Flexione (no iso code),
        Slovio (no iso code),
        Folkspraak (no iso code).

        Fixes code for:
        Occidental/Interlingue (occ -> ile)
        """

        records = OrderedDict()
        # line by line
        for li in txt.split("\n"):
            if li.strip().startswith("#"):
                pass
            elif li.strip() == "":
                pass
            else:
                recs = li.split("\t")
                if len(recs) == 3:
                    name = recs[0]
                    code = recs[1]
                    gns = recs[2]
                elif len(recs) == 2:
                    name = recs[0]
                    recs2 = recs[1].split(" ")
                    if len(recs2) == 2:
                        code, gns = recs2
                    else:
                        logging.warning("Unknown format: %s" % li)
                        continue
                else:
                    logging.warning("Unknown format: %s" % li)
                    continue
                if code.strip() == "":
                    logging.warning("No ISO 639-2/3 code for: %s" % name)
                    continue
                chars = []
                for gn in gns.split(","):
                    gn = gn.strip()
                    if gn == "":
                        pass
                    elif gn in mapping:
                        chars.append(mapping[gn])
                    else:
                        logging.warning("Glyph '%s' is does not have Unicode "
                                        "codepoint specified." % gn)
                # fix codes
                remap_codes = {
                    "occ": "ile",  # Occidental aka Interlingue (retired code)
                    "azj": "aze",  # North Azerbaijani -> Azerbaijani
                    "gaz": "orm",  # Oromo
                    "swa": "swh",  # Swahili (macrolanguage) -> Swahili language
                }
                if code in remap_codes:
                    code = remap_codes[code]
                records[code] = OrderedDict()
                records[code]["name"] = name
                records[code]["characters"] = OrderedDict()
                # add a–z, make all lower case and sort
                records[code]["characters"]["base"] = to_lc("".join(chars))
        return records

    with open(path, "r", encoding="utf-8") as f:
        txt = f.read()
        chars_txt, mapping_txt = txt.split("# Character set:")
        mapping = get_mapping(mapping_txt)
        return(get_language_info(chars_txt, mapping))


def read_cldr(path, iso_639_3):
    """
    Read information about exemplar characters from
    the Unicode CLDR XML files. There is one file for
    some combinations of language + script + region.

    Combines draft records into one entry to keep the
    structure simple, the order is base, auxiliary, numbers,
    punctuation.

    todo: when loading "regional" files, check if they actually
    add anything new on top of the main data.
    """

    def read_cldr_file(path, code):
        tree = ET.parse(path)
        lang = OrderedDict()
        lang["characters"] = OrderedDict()
        for t in ["base", "auxiliary", "numbers", "punctuation", "combinations"]:
            lang["characters"][t] = ""
        all_chars = ""
        draft = []
        script = None
        for ldml in tree.getroot():
            for ec in ldml.iter("exemplarCharacters"):
                if "type" in ec.attrib:
                    if ec.attrib["type"] in ["auxiliary", "numbers", "punctuation"]:
                        t = ec.attrib["type"]
                        s, c = parse_unicode_set(ec.text)
                        lang["characters"][t] = s
                        if c:
                            if not (t + "_combinations") in lang["characters"]:
                                lang["characters"][t + "_combinations"] = ""
                            lang["characters"][t + "_combinations"] += c
                else:
                    s, c = parse_unicode_set(ec.text)
                    lang["characters"]["base"] = s
                    lang["characters"]["combinations"] += c
                all_chars += ec.text
                if "draft" in ec.attrib:
                    draft.append(ec.attrib["draft"])
                else:
                    draft.append("done")
        if list(set(all_chars)) != []:
            codes = code.split("-")
            if len(codes) > 1:
                if len(codes[1]) == 4:
                    script = codes[1]
            lang["draft"] = ", ".join(draft)
            if not script:
                # guess script, todo: can be done better
                c_ = lang["characters"]["base"].replace(" ", "")
                if c_:
                    c_ = c_[0]
                    if "latin" in unicodedata.name(c_).lower():
                        script = "Latn"
                    elif "cyrillic" in unicodedata.name(c_).lower():
                        script = "Cyrl"
                    elif "greek" in unicodedata.name(c_).lower():
                        script = "Grek"
                    elif "arabic" in unicodedata.name(c_).lower():
                        script = "Arab"
                    elif "armenian" in unicodedata.name(c_).lower():
                        script = "Armn"
                    else:
                        script = ""
                else:
                    script = ""
            lang["script"] = script

            return lang

    cldr = OrderedDict()
    paths = os.path.join(path, "*.xml")
    main_paths = []
    regi_paths = []
    for path in glob.glob(paths):
        code, _ = os.path.splitext(os.path.basename(path))
        code = code.replace("_", "-")  # to use the proper delimiter
        if "-" not in code:
            main_paths.append((path, code))
        else:
            regi_paths.append((path, code))
    # process the main paths first
    for path, code in main_paths + regi_paths:
        lang = read_cldr_file(path, code)
        if lang:
            cldr[code] = lang
    # normalize default language and add language names from ISO
    if "root" in cldr:
        cldr["und"] = cldr["root"]
        del cldr["root"]
    # get ISO 639-3 code and name
    code_ = code.split("-")[0]
    iso = None
    if code_ in iso_639_3:
        iso = code
    else:
        for r in iso_639_3.values():
            if code_ in r["639-2B"]:
                iso = r["639-2B"]
            elif code_ in r["639-2T"]:
                iso = r["639-2T"]
            elif code_ in r["639-1"]:
                iso = r["639-1"]
    if code in cldr:
        if iso is not None:
            cldr[code]["iso-639-3"] = iso
            cldr[code]["name"] = iso_639_3[iso]["names"][0]
        else:
            logging.error("Could not find ISO 639-3 code for CLDR code %s"
                          % code)
    return cldr


def read_rosetta(path, iso_639_3={}):
    """
    Read Rosetta XML file with old language support.
    Override the names used with ISO 639-3 names
    and drop the OpenType language tag (we can add that
    later).
    """

    tree = ET.parse(path)
    rstt = OrderedDict()
    for lr in tree.getroot():
        lang = OrderedDict()
        code = lr.attrib["iso-639-3"]
        lang["name"] = iso_639_3[code]["names"][0]
        if "script" in lr.attrib:
            script = lr.attrib["script"]
        else:
            logging.warning("Script not specified for %s. Setting to 'Latn'." % lang["name"])
            script = "Latn"
        lang["script"] = script
        if script not in rstt:
            rstt[script] = OrderedDict()
        for chars in lr.iter("characters"):
            if "characters" not in lang:
                lang["characters"] = OrderedDict()
            if chars.attrib["type"] == "required":
                if chars.text:
                    lang["characters"]["base"] = to_lc(chars.text, script)
                else:
                    lang["characters"]["base"] = to_lc("", script)
            else:
                # no need for conversion to LC here
                lang["characters"][chars.attrib["type"]] = chars.text
        if "status" in lr.attrib:
            lang["status"] = lr.attrib["status"]
        rstt[script][code] = lang
    return rstt


if __name__ == '__main__':
    # Save ISO 639-3 to YAML
    path = os.path.join("data", "iso-639-3", "iso-639-3_20190408.tab")
    iso_639_3 = read_iso_639_3(path)
    save_yaml(iso_639_3, os.path.join("data", "iso-639-3.yaml"))

    # Save ISO 639-3 retirements to YAML
    path = os.path.join("data", "iso-639-3",
                        "iso-639-3_Retirements_20190408.tab")
    iso_639_3_retirements = read_iso_639_3_retirements(path)
    save_yaml(iso_639_3_retirements, os.path.join("data", "iso-639-3_retirements.yaml"))

    # Save Latin Plus to YAML
    path = os.path.join("data", "latin-plus",
                        "underware-latin-plus-data_1.txt")
    latin_plus = read_latin_plus(path)
    save_yaml(latin_plus, os.path.join("data", "latin-plus.yaml"))

    # Save CLDR to YAML
    path = os.path.join("data", "cldr", "common", "main")
    cldr = read_cldr(path, iso_639_3)
    save_yaml(cldr, os.path.join("data", "cldr.yaml"))

    # Save Rosetta old XML to YAML
    path = os.path.join("data", "rosetta", "rosetta-language-support_old.xml")
    rstt = read_rosetta(path, iso_639_3)
    save_yaml(rstt, os.path.join("data", "rosetta_old.yaml"))
