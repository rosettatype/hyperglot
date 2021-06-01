"""
Script to output a comparison table between:
- Hyperglot
- SIL Locale Data repository https://github.com/silnrsi/sldr
- Unicode CLDR https://github.com/unicode-org/cldr

Download the latest versions of those repositories to (those folders are
ignored by this git repository, but needed to run a new comparison):
- tools/sldr
- tools/cldr

Run this script in the terminal.
"""
import os
import re
import icu
import difflib
import logging
import xml.etree.ElementTree as ET

from readers import read_iso_639_3

from hyperglot.languages import Languages
from hyperglot.language import Language, Orthography


def get_langs():
    txt = os.path.join(DIR, "../other/iana/language-subtag-registry.txt")
    langs = {}
    with open(txt, "r") as file:
        defs = file.read().split("%%")
        for entry in defs:
            if "Type: language" in entry:
                tag = re.search(r"Subtag: (\S*)", entry)
                desc = re.findall(r"Description: (\S*)", entry)
                langs[tag.groups()[0]] = desc

    return langs


DIR = os.path.abspath(os.path.dirname(__file__))
CLDR = os.path.join(DIR, "cldr")
ISOS = read_iso_639_3(
    os.path.join(DIR, "../other/iso-639-3/iso-639-3_20190408.tab"))
LANGS = get_langs()


def get_country_code(lang):
    """
    Get the iso-639-3 for a -1 -2B -2T -3 entry
    """
    # Is -3
    if lang in ISOS.values():
        return lang

    for key, info in ISOS.items():
        if info["639-1"] == lang:
            return key
        elif info["639-2B"] == lang:
            return key
        elif info["639-2T"] == lang:
            return key

    # Not a iso code, try IANA list
    if lang in LANGS.keys():
        return lang

    raise ValueError("Unknown country code '%s'" % lang)


class CLDRData(dict):

    def __init__(self):
        """
        Get a dict of all cldr/common/main language files.
        They are named: iso-639-1/3(_Script)(_TERRITORY)
        """
        if not os.path.isdir(CLDR):
            raise FileNotFoundError(
                "Download the latest CLDR data into tools/cldr")

        main = os.path.join(CLDR, "common/main")
        cldr = {}
        for file in os.listdir(main):
            try:
                path = os.path.join(main, file)
                tree = ET.parse(path)
                root = tree.getroot()

                code = root.find(".//identity/language").attrib["type"]

                try:
                    locale = root.find(".//identity/territory").attrib["type"]
                except Exception:
                    locale = "default"

                try:
                    script = root.find(".//identity/script").attrib["type"]
                except Exception:
                    script = "default"

                lang = get_country_code(code)
                chars = root.findall(".//characters/exemplarCharacters")

                if lang not in cldr.keys():
                    cldr[lang] = {}

                if chars is None:
                    cldr[lang] = None
                    logging.info("CLDR has no character data for language %s /"
                                 " script %s / locale %s" %
                                 (lang, script, locale))
                    continue

                data = {
                    "script": script
                }

                # See https://github.com/unicode-org/cldr/blob/master/docs/ldml/tr35-general.md#31-exemplars
                for c in chars:
                    attr = "base"
                    if "type" in c.attrib:
                        attr = c.attrib["type"]

                    if attr in ["numbers", "punctuation", "index"]:
                        continue

                    try:
                        data[attr] = list(icu.UnicodeSet(c.text))
                    except icu.ICUError:
                        logging.error("Error when parsing Unicode Set '%s' "
                                      "(type %s) of %s" %
                                      (c.text, attr, lang))
                cldr[lang][locale] = data
            except Exception as e:
                logging.error("Error when parsing CLDR files: %s" % str(e))
        self.update(cldr)

    def orthography(self, code, script="default", locale="default"):
        if code not in self:
            return {}

        # if script != "default":
        #     for

        # TODO not sure if we can/will target the CLDR locale variants in the
        # comparison

        return self[code][locale]


if __name__ == "__main__":
    cldr = CLDRData()
    hyperglot = Languages()

    def row(lang):

        try:

            if lang not in hyperglot:
                return "<tr><td>%s</td><td colsan='2'><span class='red'>Language not in Hyperglot</td></tr>" % \
                    (lang)

            if lang not in cldr:
                return "<tr><td>%s</td><td colsan='2'><span class='green'>Language not in CLDR</td></tr>" % \
                    (lang)


            lng = Language(hyperglot[lang], lang)
            hg = Orthography(lng.get_orthography())
            cl = cldr.orthography(lang)

            if not hg.base and "base" not in cl:
                base_str = ""
            elif not hg.base:
                base_str = "<span class='red'>%s</span>" % "".join(sorted(cl["base"]))
            elif "base" not in cl:
                base_str = "<span class='green'>%s</span>" % "".join(sorted(hg.base))
            else:
                hg_base = "".join(sorted(hg.base))
                cl_base = "".join(sorted(cl["base"]))

                diff = difflib.ndiff(hg_base, cl_base)
                base = []
                for d in diff:
                    if d.startswith("+"):
                        base.append("<span class='red'>%s</span>" % d[2:])
                    elif d.startswith("-"):
                        base.append("<span class='green'>%s</span>" % d[2:])
                    else:
                        base.append(d[2:])
                base_str = "".join(base)

            if not hg.auxiliary and "auxiliary" not in cl:
                aux_str = ""
            elif not hg.auxiliary:
                aux_str = "<span class='red'>%s</span>" % "".join(sorted(cl["auxiliary"]))
            elif "auxiliary" not in cl:
                aux_str = "<span class='green'>%s</span>" % "".join(sorted(hg.auxiliary))
            else:
                hg_aux = "".join(sorted(hg.auxiliary))
                cl_aux = "".join(sorted(cl["auxiliary"]))
                diff = difflib.ndiff(hg_aux, cl_aux)
                aux = []
                for d in diff:
                    if d.startswith("+"):
                        aux.append("<span class='red'>%s</span>" % d[2:])
                    elif d.startswith("-"):
                        aux.append("<span class='green'>%s</span>" % d[2:])
                    else:
                        aux.append(d[2:])
                aux_str = "".join(aux)
                
            return "<tr><td>%s</td><td><div>%s</div></td><td><div>%s</div></td></tr>" % \
                (lang, base_str, aux_str)
        except Exception as e:
            print(e)
            return False

    table = []

    all_langs = set(list(cldr.keys()) + list(hyperglot.keys()))
    for lang in sorted(all_langs):
        r = row(lang)
        if r:
            table.append(r)

    cldr_comparison = os.path.join(DIR, "comparison_cldr.html")
    with open(cldr_comparison, "w") as f:
        html = """
        <html>
        <head>
        <meta charset="utf8">
        <style type="text/css">
        .red { color: red; }
        .green { color: green; }
        table {
            width: 100%%;
        }
        tr td { border-top: 1px solid lightgrey;
            vertical-align: top;
            max-width: 33vw;
            }
        tr td div {
            max-height: 10rem;
            overflow-y: scroll;
            word-break: break-all;
            }
        th, legend {
            position: sticky;
            background: lightgrey;
            padding: 1rem;
        }
        th {
            top: 0;
        }
        legend {
            bottom: 0;
        }
        </style>
        <head>
        <body>
        <table>
        <thead>
        <tr>
        <th>Tag</th>
        <th>CLDR Comparison (base)</th>
        <th>CLDR Comparison (aux)</th>
        </tr>
        </thead>
        <tbody>
        %s
        </tbody>
        </table>
        <legend>
            <span class='green'>Not in CLDR</span>
            <span class='red'>Not in HG</span>
            <span>in both</span>
        </legend>
        </body>
        </html>
        """

        f.write(html % "\n".join(table))
