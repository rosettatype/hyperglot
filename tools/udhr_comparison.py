"""
This is a helper script to compare all available translations of the Universal
Declaration of Human Rights with our database to detect discrepacies between
listed and actually used charsets.

To locally install the required UDHR data run:

git clone https://github.com/unicode-org/udhr.git tools/udhr
"""
import os
import sys
import logging
import re
import xml.etree.ElementTree as ET

logging.getLogger().setLevel(logging.DEBUG)

TEXTDIR = "udhr/data/udhr"


def get_udhr_paths(iso=None):
    """
    Find all xml files that match an iso in their file name and return a dict
    with iso keys and lists of all (possibly several) files for that iso
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
    print(chars)
    return chars
    # speakers = {}
    # for lang in root.findall("./item"):
    pass


def check_lang(iso):
    if len(iso) != 3:
        logging.error("'%s' not a valid iso-639-3 code")
        return
    logging.info("Checking '%s'" % iso)

    pass


def check_all_langs():
    logging.info("Checking all UDHR languages")
    paths = get_udhr_paths()
    chars = {}
    for iso, files in paths.items():
        print(iso, files)
        chars[iso] = []
        for f in files:
            chars[iso] = sorted(set(chars[iso] + get_chars_from_udhr(f)))

        # print(chars)
        return
    pass


if __name__ == "__main__":
    if len(sys.argv) == 1:
        check_all_langs()

    else:
        for iso in sys.argv:
            check_lang(iso)
