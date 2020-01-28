__doc__ = """
Script to combine language meta info (speakers and native language name) into
a single yaml file
"""

__copyright__ = "Copyright (c) 2019, Rosetta Type. All rights reserved."

__author__ = "Johannes Neumeier"

import os
import logging
import yaml
import re
import xml.etree.ElementTree as ET

NAMES = os.path.abspath(os.path.join(os.path.dirname(
    os.path.abspath(__file__)), "../data/other/language-names.yaml"))

SPEAKERS = os.path.abspath(os.path.join(os.path.dirname(
    os.path.abspath(__file__)), "../data/other/users.xml"))

ROSETTA_LANGS = os.path.abspath(os.path.join(os.path.dirname(
    os.path.abspath(__file__)), "../data/rosetta_new.yaml"))

# Where to store the parsed output
OUTPUT = os.path.abspath(os.path.join(os.path.dirname(
    os.path.abspath(__file__)), "../data/other/rosetta_new_meta.yaml"))


def get_language_names():
    with open(NAMES, "r") as stream:
        logging.debug("Fetching language names")
        try:
            return yaml.safe_load(stream)
        except yaml.YAMLError as exc:
            print(exc)
    return False


def get_language_speakers():
    tree = ET.parse(SPEAKERS)
    root = tree.getroot()
    speakers = {}
    for lang in root.findall("./item"):
        iso = lang.find("./lang")
        num = lang.find("./speakers")

        if iso is not None and num is not None:
            num_speakers = num.text
            if num_speakers == "None" or num_speakers is None:
                num_speakers = "unknown"
            speakers[iso.text] = num_speakers

    return speakers


def get_languages_raw():
    tree = ET.parse(SPEAKERS)
    root = tree.getroot()
    speakers_raw = {}
    for lang in root.findall("./item"):
        iso = lang.find("./lang")
        num = lang.find("./speakers_raw")

        if iso is not None and num is not None:
            num_speakers_raw = num.text
            if num_speakers_raw == "None" or num_speakers_raw is None:
                num_speakers_raw = "unknown"
            speakers_raw[iso.text] = num_speakers_raw

    return speakers_raw


def get_rosetta_isos():
    with open(NAMES, "r") as stream:
        logging.debug("Fetching language names")
        try:
            info = yaml.safe_load(stream)
            return list(info.keys())
        except yaml.YAMLError as exc:
            print(exc)
    return False


if __name__ == "__main__":
    speakers = get_language_speakers()
    names = get_language_names()
    db = get_rosetta_isos()

    # Get all keys
    isos = list(speakers.keys()) + list(names.keys())
    # sorted and unique
    isos = sorted(list(set(isos)))

    valid_iso = set(db).intersection(set(isos))

    meta = {}

    for iso in valid_iso:
        meta[iso] = {}

        speaker_keys = list(speakers.keys())
        if iso in speaker_keys:
            if speakers[iso] != "unknown":
                # Add speakers as number, if possible
                try:
                    meta[iso]["speakers"] = int(speakers[iso])
                except ValueError:
                    meta[iso]["speakers"] = speakers[iso]

        name_keys = list(names.keys())
        if iso in name_keys:
            meta[iso]["native_name"] = []
            lang_names = names[iso]
            # This is a dict of iso/territories with a list of dict with
            # entries of script/None: name
            for key, li in lang_names.items():
                for d in li:
                    n = list(d.values())[0]
                    if n not in meta[iso]["native_name"]:
                        meta[iso]["native_name"].append(n)

    with open(OUTPUT, "w") as out:
        yaml.dump(meta, out, default_flow_style=False, allow_unicode=True)
