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
from copy import copy
from custom_yaml import save_yaml


SCRIPT_TAGS = OrderedDict([
    ("arabic", "Arab"),
    ("armenian", "Armn"),
    ("bengali", "Beng"),
    ("chakma", "Cakm"),
    ("cherokee", "Cher"),
    ("cyrillic", "Cyrl"),
    ("devanagari", "Deva"),
    ("ethiopic", "Ethi"),
    ("georgian", "Geor"),
    ("greek", "Grek"),
    ("gujarati", "Gujr"),
    ("gurmukhi", "Guru"),
    ("hangul", "Hang"),
    ("hebrew", "Hebr"),
    ("kannada", "Knda"),
    ("khmer", "Khmr"),
    ("lao", "Laoo"),
    ("latin", "Latn"),
    ("malayalam", "Mlym"),
    ("myanmar", "Mymr"),
    ("oriya", "Orya"),
    ("sinhala", "Sinh"),
    ("tamil", "Taml"),
    ("telugu", "Telu"),
    ("thai", "Thai"),
    ("tibetan", "Tibt"),
    ("tifinagh", "Tfng"),
    ("vai", "Vaii"),
    ("yi", "Yiii"),
])

def guess_script(code, chars):
    """
    Guess the script based on characters’ Unicode description.
    Should be done more rigorously, but for the purpose of
    completing the info from CLDR, it seems sufficient.
    """

    # derive from language
    if code == "ja":  # Japanese
        return "Jpan"
    elif code == "yue":  # Yue Chinese
        return "Hani"
    elif code == "zh":  # Chinese
        return "Hani"
    # derive from character descriptions
    if chars.strip():
        for c in chars:
            # find letters in the string of characters
            if unicodedata.category(c)[0] == "L":
                for name, tag in SCRIPT_TAGS.items():
                    if name in unicodedata.name(c).lower():
                        return tag
    # return undetermined script otherwise
    return "Zyyy"


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
    # unicode codepoint escapes
    s = re.sub(r"\\U(........)", repl, s)
    s = re.sub(r"\\u(....)", repl, s)
    s = re.sub(r"\\x(..)", repl, s)

    # ranges
    s_ = ""
    for i, c in enumerate(s):
        if c == "-":
            prv = s[i - 1]
            nxt = s[i + 1]
            if prv not in " \\" and nxt != " ":
                # exclude the border characters
                # include only the characters in between
                for x in range(ord(prv) + 1, ord(nxt)):
                    s_ += chr(x)
            else:
                s_ += c
        else:
            s_ += c
    s = s_

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
    combinations = " ".join(combinations)
    return s, combinations


def to_lc(mix, script="Latn", append=True):
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
        elif c.isupper() and c.lower() in mix:
            pass
        elif c.isupper():
            lc += [c.lower()]
        else:
            lc += [c]
    lc = set(lc)
    # add basic characters
    if append:
        if script == "Latn":
            lc = lc.union(az)
        elif script == "Cyrl":
            lc = lc.union(aya)
    return " ".join(sorted(list(lc)))


def iso_from_cldr(code, iso_639_3):
    """
    Get ISO 639-3 code for a corresponding CLDR code.
    """

    code_ = code.split("-")[0]
    if code_ in iso_639_3.keys():
        return code_
    else:
        for iso, r in iso_639_3.items():
            if code_ == r["639-2B"]:
                return iso
            elif code_ == r["639-2T"]:
                return iso
            elif code_ == r["639-1"]:
                return iso

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
                script = guess_script(code, lang["characters"]["base"])
            lang["script"] = script

            return lang, script
        else:
            return None, None

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
        lang, script = read_cldr_file(path, code)
        if lang:
            # convert the default language "root" to "und"
            if code == "root":
                code = "und"
            codes = code.split("-")
            if script not in cldr:
                cldr[script] = OrderedDict()
            iso = iso_from_cldr(code, iso_639_3)
            lang["cldr_codes"] = [code]
            lang["name"] = iso_639_3[iso]["names"][0]
            if iso:
                if len(codes) == 1 or (len(codes) == 2 and len(codes[1]) == 4):
                    # store the main variant
                    cldr[script][iso] = lang
                else:
                    # the main variant has been already stored
                    # now adding code and characters from the
                    # regional variants to it
                    if iso in cldr:
                        cldr[script][iso]["cldr_codes"] += [code]
                        for k, v in lang["characters"].items():
                            v_ = v.replace(" ", "")
                            if v_ != "":
                                if k in cldr[script][iso]["characters"]:
                                    c1 = set(cldr[script][iso]["characters"][k].replace(" ", ""))
                                    c2 = set(v_)
                                    both = " ".join(sorted(list(c1.union(c2))))
                                    cldr[script][iso]["characters"][k] = both
                                else:
                                    cldr[script][iso]["characters"][k] = v
                    else:
                        cldr[script][iso] = lang
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
            if lr.attrib["status"] in ["todo", "beta"]:
                lang["status"] = "todo"
            else:
                lang["status"] = "done"
        rstt[script][code] = lang
    return rstt


def read_alvestrand(path, iso_639_3={}):
    """
    Read Alvestrand’s draft document in txt/plain
    and save “required” characters to “base” and
    “important” characters to “auxiliary”.
    Some guesswork involved in getting the characters
    that did not seem to have name/codepoint at the time
    when he wrote it (see functin get_char and get_iso_code).
    """

    def get_char(ln):
        """
        Convert a line record to a unicode-string character
        """

        splt = ln.split("    ")
        if len(splt) < 2:
            # hard to parse lines are either guessed
            # or ignored (not important lines)
            if ln == "e` -":  # in Norwegian (Nynorsk)
                return "è"
            elif ln == "E` -":  # in Norwegian (Nynorsk)
                return "È"
            elif ln == "o` -":  # in Norwegian (Nynorsk)
                return "ò"
            elif ln == "O` -":  # in Norwegian (Nynorsk)
                return "Ò"
            elif ln == "KK -":  # in Greenlandic (capital Kra)
                return None
            elif ln == "-A -":  # in Spanish (capital feminine ordinal)
                return None
            elif ln == "-O -":  # in Spanish (capital masculine ordinal)
                return None
            else:
                return None
        else:
            _, code = splt
            code = code.strip()[:4]
            return chr(int(code, 16))

    def get_iso_code(name, code, iso_639_3):
        """
        Get iso 639-3 code.
        """

        for k, v in iso_639_3.items():
            if name.title() in v["names"]:
                return k
            elif code in v["639-1"]:
                return k
            elif name == "Sami":
                # Northern Sami
                return "sme"
            elif name == "Gaelic":
                # Scottish Gaelic
                return "gla"
            elif name == "Sorbian":
                # Upper Sorbian
                return "hsb"
            elif name == "Cyrillic":
                # the Cyrillic script
                # deleted after use, in the end
                return "cyr"
    i = 1  # chapter counter
    langs = OrderedDict()
    required = False
    important = False
    comment = False
    with open(path, "r", encoding="utf-8") as f:
        content_ = [ln.strip() for ln in f.readlines()]
        content = []
        for ln in content_:
            if "name not known" in ln:
                content += ln.split("name not known")
            else:
                content += [ln]
    for ln in content:
            ln = ln.strip()
            if ln.startswith("3.%d" % i):
                if i <= 48:
                    _, code, name = ln.replace("  ", " ").split(" ")
                    code = get_iso_code(name.strip(), code.strip(), iso_639_3)
                    langs[code] = OrderedDict()
                    langs[code]["characters"] = OrderedDict()
                    langs[code]["characters"]["base"] = ""
                    langs[code]["characters"]["auxiliary"] = ""
                    langs[code]["comment"] = ""
                    langs[code]["chapter"] = float("3.%d" % i)
                    required = False
                    important = False
                    comment = False
                    i += 1
                else:
                    break
            elif ln.startswith("Required characters"):
                required = True
                important = False
                comment = False
            elif ln.startswith("Important characters"):
                required = False
                important = True
                comment = False
            elif ln.startswith("Comments"):
                required = False
                important = False
                comment = True
            elif ln.startswith("Character sets"):
                required = False
                important = False
                comment = False
            elif ln.startswith("Alvestrand") or \
                 ln.startswith("draft") or \
                 ln.startswith("This language has no known character set"):
                pass
            elif ln.startswith("Based on script listed as"):
                ln = ln.replace("Based on script listed as", "").strip()
                if ln.lower() == "latin":
                    langs[code]["script"] = "Latn"
                elif ln.lower() == "cyrillic":
                    langs[code]["script"] = "Cyrl"
            elif ln.startswith("4.  Other languages"):
                break
            elif required and ln != "":
                c = get_char(ln)
                if c:
                    langs[code]["characters"]["base"] += c
            elif important and ln != "":
                c = get_char(ln)
                if c:
                    langs[code]["characters"]["auxiliary"] += get_char(ln)
            elif comment and ln != "":
                langs[code]["comment"] += ln + " "
    # normalize character sets and structure
    avst = OrderedDict()
    avst["Latn"] = OrderedDict()
    avst["Cyrl"] = OrderedDict()
    for code, l in langs.items():
        if "script" in l:
            script = l["script"]
            if script == "Latn":
                l["characters"]["base"] += langs["lat"]["characters"]["base"]
            if script == "Cyrl":
                l["characters"]["base"] += langs["cyr"]["characters"]["base"]
            del l["script"]
        elif code == "lat":
            # Latin language/scritp record
            # -> add as language to the Latin script
            script = "Latn"
        elif code == "deu":
            # fix uppercase SS
            l["characters"]["base"] = l["characters"]["base"].replace("", "SS")
        if l["comment"] == "":
            del l["comment"]
        l["characters"]["base"] = to_lc(l["characters"]["base"])
        l["characters"]["auxiliary"] = to_lc(l["characters"]["auxiliary"], append=False)
        # copy language under script
        # ignore Cyrillic script record (cyr)
        if code != "cyr":
            avst[script][code] = l
    # copy Upper Sorbian to Lower Sorbian
    avst["Latn"]["dsb"] = copy(avst["Latn"]["hsb"])

    return avst


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

    # Save CLDR to YAML
    path = os.path.join("data", "cldr", "common", "main")
    cldr = read_cldr(path, iso_639_3)
    save_yaml(cldr, os.path.join("data", "cldr.yaml"))

    # Save Latin Plus to YAML
    path = os.path.join("data", "other", "latin-plus",
                        "underware-latin-plus-data_1.txt")
    latin_plus = read_latin_plus(path)
    save_yaml(latin_plus, os.path.join("data", "other", "latin-plus.yaml"))

    # Save Rosetta old XML to YAML
    path = os.path.join("data", "other", "rosetta", "rosetta-language-support_old.xml")
    rstt = read_rosetta(path, iso_639_3)
    save_yaml(rstt, os.path.join("data", "rosetta_old.yaml"))

    # Save Alvestrand’s TXT draft to YAML
    path = os.path.join("data", "alvestrand", "draft-alvestrand-lang-char-03.txt")
    avst = read_alvestrand(path, iso_639_3)
    save_yaml(avst, os.path.join("data", "alvestrand.yaml"))
