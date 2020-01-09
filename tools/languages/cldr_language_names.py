import os
import yaml
import logging
import xml.etree.ElementTree as ET

# Path to a folder of xml files from the CLDR:
# https://github.com/unicode-org/cldr/tree/release-36/common/main
CLDR = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                    "cldr_v36_common_main")
OUTPUT = os.path.abspath(os.path.join(os.path.dirname(
    os.path.abspath(__file__)), "../../data/language-names.yaml"))
ISONAMES = os.path.abspath(os.path.join(os.path.dirname(
    os.path.abspath(__file__)), "../../data/iso-639-3.yaml"))

logging.getLogger().setLevel(logging.DEBUG)

iso_yaml = None


def get_iso_three_letter(code):
    """
    A helper to find three letter iso-639-3 codes for possible 2 letter 
    iso-639-2 codes
    """
    global iso_yaml

    code = code.strip()

    if len(code) < 2 or len(code) > 3:
        raise ValueError(
            "get_iso_three_letter expects a two or three character string")

    if iso_yaml is None:
        with open(ISONAMES, "r") as stream:
            logging.debug("Fetching ISO language codes")
            try:
                iso_yaml = yaml.safe_load(stream)
            except yaml.YAMLError as exc:
                print(exc)

    # If three letter confirm it exists
    if len(code) == 3:
        if code in list(iso_yaml.keys()):
            return code

        raise ValueError("3-letter ISO %s not found" % code)

    # If two letter code, try find 3 letter variant
    if len(code) == 2:
        for iso, info in iso_yaml.items():
            shorter = info["639-1"]
            if shorter is not None and shorter == code:
                return iso

    raise ValueError("Iso %s not found" % code)


def get_language_names():
    language_names = {}
    files = os.listdir(CLDR)

    # Skip _-files if and only if the pre-underscore part makes up a file
    # E.g. for xog.xml and xog_UG.xml use only xog.xml, but
    # for when there is only ja_JP.xml us it
    for filename in files:
        path = os.path.join(CLDR, filename)
        if filename.find("_") != -1:
            parts = filename.split("_")
            plain = parts[0] + ".xml"
            if plain in files:
                logging.debug("Skipping sub-orthography file %s" % filename)
                continue

        tree = ET.parse(path)
        root = tree.getroot()

        # We could assume this from the filename, but better to extract
        iso = root.find(".//identity/language").attrib["type"]
        if not iso:
            logging.warning("Could not extract iso code for %s" % filename)
            continue

        name = root.find(
            ".//localeDisplayNames/languages/language[@type='" + iso + "']")
        if name is None:
            logging.warning(
                "Could not find iso '%s' in languages of %s" % (iso, filename))
            continue

        name = name.text
        # For whatever wise reason the language codes in the xml mix iso-639-2
        # and iso-639-3, so get the iso-639-3 always
        try:
            iso = get_iso_three_letter(iso)
        except ValueError as e:
            logging.error("Could not find a valid iso-639-3 code for %s" % iso)
            continue

        if iso and name:
            language_names[iso] = name

    return language_names


if __name__ == "__main__":
    langs = get_language_names()
    with open(OUTPUT, "w") as out:
        yaml.dump(langs, out, default_flow_style=False, allow_unicode=True)
