"""
This is a helper script to compare all available translations of the Universal
Declaration of Human Rights with our database to detect discrepacies between
listed and actually used charsets.

To locally download the required UDHR data run:

git clone https://github.com/unicode-org/udhr.git tools/udhr
"""
import os
import logging
import re
import yaml
import xml.etree.ElementTree as ET
import unicodedata2 as ud
from hyperglot.languages import Languages
from hyperglot.parse import parse_chars

logging.getLogger().setLevel(logging.DEBUG)

TEXTDIR = "udhr/data/udhr"


def get_udhr_paths(iso=None):
    """
    Find all xml files that match an iso in their file name and return a dict
    with iso keys and lists of all (possibly several) files for that iso
    # NOTE: All xml files in the udhr have an additional iso code on their root
    # element which is the actual truth about the language. However, to just
    # get a reasonable list of files for each iso without opening hundreds of
    # files we are happy with matching the iso from the file name
    """
    paths = {}
    pattern = re.compile("udhr_([a-z]{3}).*\.xml$")
    base = os.path.dirname(os.path.abspath(__file__))
    path = os.path.join(base, TEXTDIR)
    try:
        files = os.listdir(path)
    except FileNotFoundError:
        logging.error("Data directory '%s' not found. Did you install the "
                      "UDHR git repo by running: \n"
                      "git clone https://github.com/unicode-org/udhr.git tools/udhr"  # noqa
                      % path)

    for f in files:
        hits = pattern.findall(f)
        if hits:
            key = hits[0]
            if iso is not None and key != iso:
                continue

            if key not in paths:
                paths[key] = []
            paths[key].append(os.path.join(path, f))

    return paths


def get_chars_from_udhr(path):
    logging.info("Loading UDHR text from '%s'" % path)

    tree = ET.parse(path)
    root = tree.getroot()
    text = "".join(root.itertext())
    chars = sorted(set(text))
    return chars
    # speakers = {}
    # for lang in root.findall("./item"):
    pass


def get_stats_from_chars(text_chars, db=None):

    report = {}

    uppercase = []
    numerals = []
    punctuation = []
    controlchars = []
    spaces = []
    other = []

    # Include decomposed forms
    for c in text_chars:
        decomposed = ud.normalize("NFKD", c)
        if len(decomposed) > 1:
            text_chars = text_chars + [d for d in decomposed]

    text_chars = set(text_chars)

    for c in text_chars:
        # print(c, ud.category(c))
        cat = ud.category(c)

        if cat == "Lu":
            uppercase.append(c)
        elif cat.startswith("N"):
            numerals.append(c)
        elif cat.startswith("P"):
            punctuation.append(c)
        elif cat.startswith("C") and len(c) > 1:
            controlchars.append(c)
        elif cat.startswith("Z"):
            spaces.append(c)
        else:
            other.append(c)

    # Remove all but "other" from chars, we don't care about them for diffing
    for remove in [uppercase, numerals, punctuation, controlchars, spaces,
                   ["\n", "\t"]]:
        text_chars = text_chars.difference(set(remove))

    report["iso_in_db"] = db is not None
    report["found_in_text"] = {
        "uppercase": sorted(uppercase),
        "numerals": sorted(numerals),
        "punctuation": sorted(punctuation),
        "chars": sorted(text_chars)
    }

    # Compare to orthographies
    if db is not None:
        db_chars = []
        if "orthographies" in db:
            for o in db["orthographies"]:
                if "base" in o:
                    db_chars = db_chars + parse_chars(o["base"])
                if "auxiliary" in o:
                    db_chars = db_chars + parse_chars(o["auxiliary"])

        db_chars = set(sorted(db_chars))

        not_in_db = text_chars.difference(db_chars)
        missing_from_text = db_chars.difference(text_chars)
        decomposed = set(parse_chars("".join(text_chars), decompose=True))

        # print("Listed in DB but not in text", missing_from_text)
        # print("Appears in text but not listed in DB", not_in_db)
        # print("Text can be written with DB characters",
        #       decomposed.issubset(db_chars))
        missing_from_db = ""
        for c in not_in_db:
            missing = ud.normalize("NFKD", c)
            missing_parts = ""
            for part in missing:
                if part not in db_chars:
                    missing_parts = missing_parts + part
            if missing_parts != []:
                missing_from_db = missing_from_db + missing_parts
        # print("missing from db", sorted(list(missing_from_db)))
        missing_from_db = sorted(list(set(missing_from_db)))

        report["not_in_text"] = sorted(missing_from_text)
        report["not_in_db"] = sorted(not_in_db)
        if missing_from_db:
            report["missing_from_db"] = missing_from_db
        report["db_chars_valid"] = decomposed.issubset(db_chars)

    return report


def check_all_langs(db):
    logging.info("Checking all UDHR languages")
    paths = get_udhr_paths()
    reports = {}
    for iso, files in paths.items():
        chars = []
        reports[iso] = {}
        for f in files:
            filename = os.path.basename(f)
            chars = sorted(set(chars + get_chars_from_udhr(f)))
            if iso in db:
                reports[iso][filename] = get_stats_from_chars(chars, db[iso])
            else:
                reports[iso][filename] = get_stats_from_chars(chars)

    return reports


def is_included_in_macrolanguage(Langs, iso):
    for lang, vals in Langs.items():
        if "includes" in vals:
            if iso in vals["includes"]:
                return True
    return False


if __name__ == "__main__":
    Langs = Languages()

    reports = check_all_langs(Langs)
    logging.info("Created reports for '%d' languages" % len(reports))
    for iso, files in reports.items():
        for file, report in files.items():
            for key, values in report.items():
                if type(values) in [set, list]:
                    reports[iso][file][key] = " ".join(values)
                if key == "found_in_text":
                    for k, v in report[key].items():
                        reports[iso][file][key][k] = " ".join(v)

        if reports[iso][file]["iso_in_db"] == False:
            reports[iso][file]["iso_in_db_macrolang"] = is_included_in_macrolanguage(
                Langs, iso)

    file = "tools/udhr_comparison.yaml"
    with open(file, "w") as out:
        yaml.dump(reports, out, encoding="utf-8",
                  default_flow_style=False, allow_unicode=True)
        logging.info("Written report to '%s'" % file)
