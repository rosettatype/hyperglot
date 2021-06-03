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

logging.getLogger().setLevel(logging.INFO)


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

        # Get the en.xml and all language names defined in it
        names = {}
        en = ET.parse(os.path.join(main, "en.xml"))
        langs = en.getroot().findall(".//localDisplaynames/languages/language")
        for l in langs:
            names[l.attrib["type"]] = l.text

        cldr = {}
        # Loop through all xmls in common/main and get their character and
        # autonym info
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

                autonym_node = root.find(
                    ".//languages/language[@type='%s']" % lang)
                data["autonym"] = autonym_node.text if autonym_node is not None else "-"

                data["name"] = names[lang] if lang in names else "-"

                cldr[lang][locale] = data
            except Exception as e:
                logging.error("Error when parsing CLDR files: %s" % str(e))
        if cldr:
            self.update(cldr)

    def orthography(self, code, script="default", locale="default"):
        if code not in self:
            return {}

        # if script != "default":
        #     for

        # TODO not sure if we can/will target the CLDR locale variants in the
        # comparison

        return self[code][locale]

    def alternative_orthographies(self, code):
        if code not in self:
            return {}

        non_default = {loc: o for loc,
                       o in self[code].items() if loc != "default"}
        return non_default


if __name__ == "__main__":
    cldr = CLDRData()
    hyperglot = Languages()

    def row(lang, locale="default"):

        cl = cldr.orthography(lang, locale)
        loc = "" if locale == "default" else locale
        script = "" if "script" not in cl or cl["script"] == "default" else cl["script"]

        # try:
        hg = False
        if lang in hyperglot:
            lng = Language(hyperglot[lang], lang)
            lng_name = lng.get_name()
            lng_autonym = lng.get_autonym()
            if lng:
                o = lng.get_orthography()
                if o:
                    hg = Orthography(o)
        else:
            lng = False
            lng_name = "-"
            lng_autonym = "-"

        name = "%s / %s" % (lng_name if lng_name else "-",
                            cl["name"] if "name" in cl else "-")
        autonym = "%s / %s" % (lng_autonym if lng_autonym else "-",
                               cl["autonym"] if "autonym" in cl else "-")

        if lang not in hyperglot or not hg:
            return "<tr><td>%s</td><td>%s</td><td>%s</td><td class='center'>%s</td><td class='center'>%s</td><td colspan='2'><span class='red'>Language not in Hyperglot</td></tr>" % \
                (lang, loc, script, name, autonym)

        if lang not in cldr:
            return "<tr><td>%s</td><td>%s</td><td>%s</td><td class='center'>%s</td><td class='center'>%s</td><td colspan='2'><span class='green'>Language not in CLDR</td></tr>" % \
                (lang, loc, script, name, autonym)

        if not hg.base and "base" not in cl:
            base_str = ""
        elif not hg.base:
            base_str = "<span class='red'>%s</span>" % "".join(
                sorted(cl["base"]))
        elif "base" not in cl:
            base_str = "<span class='green'>%s</span>" % "".join(
                sorted(hg.base))
        else:
            base_marks = hg.base_marks
            if not base_marks:
                base_marks = []
            hg_base = "".join(sorted(hg.base + base_marks))
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
            aux_str = "<span class='red'>%s</span>" % "".join(
                sorted(cl["auxiliary"]))
        elif "auxiliary" not in cl:
            aux_str = "<span class='green'>%s</span>" % "".join(
                sorted(hg.auxiliary))
        else:
            aux_marks = hg.auxiliary_marks
            if not aux_marks:
                aux_marks = []
            hg_aux = "".join(sorted(hg.auxiliary + aux_marks))
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

        # Append any local variants CLDR has
        alt_rows = []
        alts = cldr.alternative_orthographies(lang)
        if len(alts) > 0 and locale == "default":
            for a in alts:
                logging.info("Get alternative locale %s for %s" %
                             (a, lang))
                alt_rows.append(row(lang, a))

        return "<tr><td>%s</td><td>%s</td><td>%s</td><td class='center'>%s</td><td class='center'>%s</td><td><div>%s</div></td><td><div>%s</div></td></tr>" % \
            (lang, loc, script, name, autonym,
             base_str, aux_str) + "\n".join(alt_rows)
        # except Exception as e:
        #     print(str(e))
        #     return False

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
            border-collapse: collapse;
            width: 100%%;
        }
        tr:nth-child(even) {
            background: #eee;
        }
        tr td { 
            border-top: 1px solid lightgrey;
            border-right: 1px dotted lightgray;
            vertical-align: top;
            max-width: 33vw;
            padding: 0.1em 0.5em;
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
        .center { 
            text-align: center;
        }
        </style>
        <head>
        <body>
        <h1>Generated comparison between Hyperglot (0.3.3) and CLDR (v40.0)</h1>
        <h2>Disclaimers/Comments:</h2>
        <ul>
        <li>Some language tag mappings might not be correct or do not match between the two DBs, particularly for macrolanguages or tags that have been discontinued and differ in both DBs (e.g. est/et/ekk)</li>
        <li>Hyperglot has Lating/Cyrillic/Greek cases letters, whereas CLDR will always only have lowercase</li>
        <li>The diff comparison of base + aux comparse the base/aux respectively, not their combination. E.g. one DB might have some char in base, the other in aux, but show as a diff in both attributes</li>
        <li>The reference Hyperglot orthography is always the "default" one</li>
        <li>CLDR regional "locale" sets do not seem to have different script for the same language, ever</li>
        </ul>
        <table>
        <thead>
        <tr>
        <th>Tag</th>
        <th>Locale (CLDR)</th>
        <th>Script (CLDR)</th>
        <th>Name (EN) <nobr>Hyperglot / CLDR</nobr></th>
        <th>Autonym <nobr>Hyperglot / CLDR</nobr></th>
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
