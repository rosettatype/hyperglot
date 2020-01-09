import os
import yaml
import logging
import xml.etree.ElementTree as ET

# Path to a folder of xml files from the CLDR:
# https://github.com/unicode-org/cldr/tree/release-36/common/main
CLDR = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                    "cldr_v36_common_main")

# Where to store the parsed output
OUTPUT = os.path.abspath(os.path.join(os.path.dirname(
    os.path.abspath(__file__)), "../../data/language-names.yaml"))

# Where to find a yaml with iso-639 data
ISONAMES = os.path.abspath(os.path.join(os.path.dirname(
    os.path.abspath(__file__)), "../../data/iso-639-3.yaml"))

# Cache once the iso-639 data for finding language codes where needed
iso_yaml = None


logging.getLogger().setLevel(logging.DEBUG)


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
    """
    Using the CLDR data compile a list of native language names
    Returns a dict with iso-639-2 keys that in turn has dicts with keys for
    each "territory" variant of the language, which in turn has a key of
    "script" keys for each script the language has a native name for

    E.g.:
    eng: {
        en: {
            null: English
        },
        en_GB: {
            null: Canadian English
        }
    }
    ...
    uzb: {
        uz: {
            Arab: اوزبیک,
            Cyrl: ўзбекча,
            null: o'zbek
        }
    """
    language_names = {}
    files = os.listdir(CLDR)

    # Skip _-files if and only if the pre-underscore part makes up a file
    # E.g. for xog.xml and xog_UG.xml use only xog.xml, but
    # for when there is only ja_JP.xml us it
    for filename in files:
        path = os.path.join(CLDR, filename)
        tree = ET.parse(path)
        root = tree.getroot()

        script = None

        # We could assume this from the filename, but better to extract
        iso = root.find(".//identity/language").attrib["type"]
        if not iso:
            logging.warning("Could not extract iso code for %s" % filename)
            continue

        # "code" is the iso in 3 letter format as we use them in our data
        # NOTE for some reason some of those are in 2 letter, others in 3
        # letter format
        code = iso

        # If this file is a territory-specific alternate of the language see if
        # there is a name for this language with that territory, e.g. en_GB
        try:
            territory = root.find(".//identity/territory").attrib["type"]
            if territory:
                logging.debug("File '%s' appears to be territory file "
                              "('%s') of lang '%s', searching for localized "
                              "native name" % (filename, territory, iso))
                code = iso + "_" + territory
        except AttributeError:
            # If there is no "territory" in "identity" found
            pass

        # See if this is a alternative file for a language that is written with
        # several scripts, if so store the script for later use as dict key
        # when storing the language name (otherwise fall back to use null key)
        # NOTE Unfortunately the data does not straight give the script of the
        # _default_ file for a language
        try:
            script = root.find(".//identity/script").attrib["type"]
        except AttributeError:
            # No script specified
            pass

        name = root.find(
            ".//localeDisplayNames/languages/language[@type='" + code + "']")
        if name is None:
            logging.warning(
                "Could not find iso '%s' in languages of %s" %
                (code, filename))
            continue

        name = name.text

        # For whatever wise reason the language codes in the xml mix iso-639-2
        # and iso-639-3, so get the iso-639-3 always
        try:
            iso3 = get_iso_three_letter(iso)
        except ValueError:
            logging.error("Could not find a valid iso-639-3 code for %s" % iso)
            continue

        # This seems to be the convention for referring to a language name from
        # that equals the non-territory default name, so ignore it
        if name == "↑↑↑":
            logging.debug(
                "Skipping sub-category with '↑↑↑' native language name")
            continue

        if iso3 and code and name:
            if iso3 not in language_names.keys():
                language_names[iso3] = {}
            if code not in language_names[iso3]:
                language_names[iso3][code] = []

            language_names[iso3][code].append({script: name})

    return language_names


if __name__ == "__main__":
    langs = get_language_names()
    with open(OUTPUT, "w") as out:
        yaml.dump(langs, out, default_flow_style=False, allow_unicode=True)
