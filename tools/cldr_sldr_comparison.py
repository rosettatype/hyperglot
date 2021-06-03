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

logging.basicConfig()
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


def highlighted_diff(a, b,
                     wrapper_add="<span class='red'>%s</span>",
                     wrapper_del="<span class='green'>%s</span>"):
    diff = difflib.ndiff(a, b)
    base = []
    for d in diff:
        if d.startswith("+"):
            base.append(wrapper_add % d[2:])
        elif d.startswith("-"):
            base.append(wrapper_del % d[2:])
        else:
            base.append(d[2:])
    return "".join(base)


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


class UnicodeData(dict):
    """
    A general "parser" Class for SLDR/CLDR xml files.
    Init with different file indexing, but otherwise same API
    """

    def __init__(self):
        # A dict with EN names, subclasses need to implement parsing this
        self.names = {}
        self.get_names()
        pass

    def parse_file(self, path):
        cldr = {}
        try:
            tree = ET.parse(path)
            root = tree.getroot()

            code = root.find(".//identity/language").attrib["type"]

            try:
                locale = root.find(".//identity/territory").attrib["type"]
            except Exception:
                locale = "default"

            try:
                # script from XML
                script = root.find(".//identity/script").attrib["type"]
            except Exception:
                script = "default"

            lang = get_country_code(code)
            chars = root.findall(".//characters/exemplarCharacters")

            if lang not in self.keys():
                self[lang] = {}

            data = {
                "script": script,
                "locale": locale,
            }

            # See https://github.com/unicode-org/cldr/blob/master/docs/ldml/tr35-general.md#31-exemplars
            if chars:
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

            data["name"] = self.names[lang] if lang in self.names else "-"

            key = "default"
            if script != "default" or locale != "default":
                key = "%s_%s" % (script, locale)

            self[lang][key] = data

        except Exception as e:
            logging.error("Error when parsing XML file: %s" % str(e))

    def orthography(self, code, key="default"):
        if code not in self:
            return {}

        return self[code][key]

    def alternative_orthographies(self, code):
        if code not in self:
            return {}

        non_default = {loc: o for loc,
                       o in self[code].items() if loc != "default"}
        return non_default


class CLDRData(UnicodeData):

    main = os.path.join(CLDR, "common/main")

    def __init__(self):
        """
        Get a dict of all cldr/common/main language files.
        They are named: iso-639-1/3(_Script)(_TERRITORY)
        """
        super().__init__()

        if not os.path.isdir(CLDR):
            raise FileNotFoundError(
                "Download the latest CLDR data into tools/cldr")
        self.parse()

    def get_names(self):
        # Get the en.xml and all language names defined in it
        en = ET.parse(os.path.join(self.main, "en.xml"))
        langs = en.getroot().findall(".//localDisplaynames/languages/language")
        for l in langs:
            self.names[l.attrib["type"]] = l.text

    def parse(self):
        # cldr = {}
        # Loop through all xmls in common/main and get their character and
        # autonym info
        for file in os.listdir(self.main):
            self.parse_file(os.path.join(self.main, file))

        # if cldr != {}:
        #     self.update(cldr)


def row(cmp, hyperglot, lang, locale="default"):

    cl = cmp.orthography(lang, locale)
    loc = cl["locale"] if "locale" in cl else "-"
    if loc == "default":
        loc = "-"
    script = cl["script"] if "script" in cl else "-"
    if script == "default":
        script = "-"

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

    if lang not in cmp:
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

        base_str = highlighted_diff(hg_base, cl_base)

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
    alts = cmp.alternative_orthographies(lang)
    if len(alts) > 0 and locale == "default":
        for a in alts:
            logging.info("Get alternative locale %s for %s" %
                         (a, lang))
            alt_rows.append(row(cmp, hyperglot, lang, a))

    return "<tr><td>%s</td><td>%s</td><td>%s</td><td class='center'>%s</td><td class='center'>%s</td><td><div>%s</div></td><td><div>%s</div></td></tr>" % \
        (lang, loc, script, name, autonym,
            base_str, aux_str) + "\n".join(alt_rows)


def write_comparison(cmp, hyperglot, cmp_file):
    table = []
    all_langs = set(list(cmp.keys()) + list(hyperglot.keys()))
    for lang in sorted(all_langs):
        r = row(cmp, hyperglot, lang)
        if r:
            table.append(r)

    with open(cmp_file, "w") as f:
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


if __name__ == "__main__":
    cldr = CLDRData()
    # sldr = SLDRData()
    hyperglot = Languages()

    write_comparison(cldr, hyperglot, os.path.join(
        DIR, "cldr_comparison.html"))
