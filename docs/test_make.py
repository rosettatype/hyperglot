"""
Make test website
"""

from copy import copy
import os
import sys
from collections import OrderedDict
sys.path.insert(0, "..")
from custom_yaml import load_yaml


# -----------------------------------------------------------------------------
# Helpers
# -----------------------------------------------------------------------------


def get_cldr_code(code):
    if code in cldr:
        return code
    elif iso_639_3[code]["639-2B"] in cldr:
        return iso_639_3[code]["639-2B"]
    elif iso_639_3[code]["639-2T"] in cldr:
        return iso_639_3[code]["iso-639-2T"]
    elif iso_639_3[code]["639-1"] in cldr:
        return iso_639_3[code]["639-1"]
    else:
        return None


# -----------------------------------------------------------------------------
# Read and merge data
# -----------------------------------------------------------------------------

script = "Latn"

iso_639_3 = load_yaml(os.path.join("..", "data", "iso-639-3.yaml"))
latin_plus = load_yaml(os.path.join("..", "data", "latin-plus.yaml"))
cldr = load_yaml(os.path.join("..", "data", "cldr.yaml"))
rstt = load_yaml(os.path.join("..", "data", "rosetta_old.yaml"))

# merge data together
merged = OrderedDict()
for code, lang in rstt[script].items():
    merged[code] = copy(lang)
    merged[code]["latin_plus"] = None
    merged[code]["cldr"] = None
    if code in latin_plus and script == "Latn":
        merged[code]["latin_plus"] = latin_plus[code]["characters"]["base"]
    ccode = get_cldr_code(code)
    if ccode and script == cldr[ccode]["script"]:
        merged[code]["cldr"] = OrderedDict()
        merged[code]["cldr"]["base"] = cldr[ccode]["characters"]["base"]
        merged[code]["cldr"]["auxiliary"] = ""
        merged[code]["cldr"]["numbers"] = ""
        merged[code]["cldr"]["punctuation"] = ""
        merged[code]["cldr"]["draft"] = cldr[ccode]["draft"].split(",")
        if "auxiliary" in cldr[ccode]["characters"]:
            merged[code]["cldr"]["auxiliary"] = cldr[ccode]["characters"]["auxiliary"]
        if "numbers" in cldr[ccode]["characters"]:
            merged[code]["cldr"]["numbers"] = cldr[ccode]["characters"]["numbers"]
        if "punctuation" in cldr[ccode]["characters"]:
            merged[code]["cldr"]["punctuation"] = cldr[ccode]["characters"]["punctuation"]


# -----------------------------------------------------------------------------
# Compile test website
# -----------------------------------------------------------------------------


def comparison(r, s):
    o = ""
    for c in s.split(" "):
        if c in r:
            o += "<em>%s</em> " % c
        else:
            o += "<strong>%s</strong> " % c
    return o


s = ""
for code, lang in merged.items():
    r = merged[code]["characters"]["base"]
    s += "<h2>%s: %s</h2>\n" % (lang["name"], code)
    s += "<table>\n"
    s += "<tr><th>%s:</th><td>%s</td><td class='%s'></td></tr>\n" % ("Rosetta (base)", r, merged[code]["status"])
    if "optional" in merged[code]["characters"]:
        s += "<tr><th>%s:</th><td>%s</td><td class='%s'></td></tr>\n" % ("Rosetta (optional)", merged[code]["characters"]["optional"], merged[code]["status"])
    if merged[code]["latin_plus"] is not None:
        s += "<tr><th>%s:</th><td>%s</td><td class='done'></td></tr>\n" % ("Latin Plus", comparison(r, merged[code]["latin_plus"]))
    if merged[code]["cldr"] is not None:
        for t, draft in zip(["base", "auxiliary", "numbers", "punctuation"], merged[code]["cldr"]["draft"]):
            if t in merged[code]["cldr"]:
                if t == "base":
                    # comparison only for base
                    s += "<tr><th>%s:</th><td>%s</td><td class='%s'></td></tr>\n" % ("CLDR (%s)" % t, comparison(r, merged[code]["cldr"][t]), draft)
                else:
                    s += "<tr><th>%s:</th><td>%s</td><td class='%s'></td></tr>\n" % ("CLDR (%s)" % t, merged[code]["cldr"][t], draft)
    s += "</table>\n\n"

# save the HTML
with open("template.html", "r", encoding="utf-8") as f:
    html = f.read()
    html = html.replace("{{ title }}", "Latin languages")
    html = html.replace("{{ content }}", s)
with open("test_latin.html", "w", encoding="utf-8") as f:
    f.write(html)
