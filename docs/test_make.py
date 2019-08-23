"""
Make test website
"""

from copy import copy
import os
import sys
from collections import OrderedDict
sys.path.insert(0, "..")
from custom_yaml import load_yaml
from readers import SCRIPT_TAGS


def comparison(r, s):
    o = ""
    for c in s.split(" "):
        if c in r:
            o += "<span>%s</span> " % c
        else:
            o += "<strong>%s</strong> " % c
    return o


# -----------------------------------------------------------------------------
# Read and merge data
# -----------------------------------------------------------------------------


iso_639_3 = load_yaml(os.path.join("..", "data", "iso-639-3.yaml"))
db = {}
db["latin_plus"] = OrderedDict()
db["latin_plus"]["Latn"] = load_yaml(os.path.join("..", "data", "latin-plus.yaml"))
db["cldr"] = load_yaml(os.path.join("..", "data", "cldr.yaml"))
db["rstt"] = load_yaml(os.path.join("..", "data", "rosetta_old.yaml"))

# merge data together
for script_name, script in SCRIPT_TAGS.items():
    frnt = ""
    frnt += "---\n"
    frnt += "layout: default\n"
    frnt += "permalink: test_%s\n" % script
    frnt += "---\n\n"
    html = ""
    html += "<h1>%s-script languages (comparison)</h1>\n\n" % script_name.title()
    html += "<p>Selected character-set databases (CLDR, Latin Plus) "
    html += "juxtaposed next to Rosetta’s Langs DB. When comparing, "
    html += "characters that are included in “Rosetta (base)” "
    html += "are marked grey, any additional characters are marked red. "
    html += "Only “base” fields are compared. "
    html += "The third column indicates the status of the field.<p>\n\n"

    # get a super-set of all ISO codes
    isos = set()
    for dbk in ["rstt", "latin_plus", "cldr"]:
        if script in db[dbk]:
            isos = isos.union(set(db[dbk][script].keys()))
    for iso in sorted(list(isos)):
        all_chars = ""
        tab = ""
        r = ""
        for dbk in ["rstt", "latin_plus", "cldr"]:
            if (script in db[dbk]) and (iso in db[dbk][script]):
                for i, t in enumerate(["base", "auxiliary", "numbers", "punctuation"]):
                    if t in db[dbk][script][iso]["characters"]:
                        # characters
                        chars = db[dbk][script][iso]["characters"][t]
                        all_chars += chars
                        if dbk == "rstt":
                            r = copy(chars)
                            tab += "<tr><th>%s (%s):</th><td>%s</td>" % (dbk, t, chars)
                        else:
                            tab += "<tr><th>%s (%s):</th><td>%s</td>" % (dbk, t, comparison(r, chars))
                        # status
                        if dbk == "rstt":
                            s = (db[dbk][script][iso]["status"] == "done")
                        elif dbk == "cldr":
                            drafts = db[dbk][script][iso]["draft"].split(",")
                            s = -1
                            if i < len(drafts):
                                s = not (drafts[i] == "contributed")
                        else:
                            s = 1
                        s = ["☒", "☑︎", "☐"][s]
                        tab += "<td>%s</td></tr>\n" % s
        if all_chars.strip():
            html += "<h2>%s (%s)</h2>\n\n" % (iso_639_3[iso]["names"][0], iso)
            html += "<table>\n %s </table>\n\n" % tab

    # save to MD
    with open("test_%s.md" % script, "w", encoding="utf-8") as f:
        f.write(frnt + html)

    # save to HTML
    with open("_layouts/template.html", "r", encoding="utf-8") as f:
        page = f.read()
        page = page.replace("{{ title }}", "%s-script languages (comparison)" % script_name.title())
        page = page.replace("{{ content }}", html)
    with open("test_%s.html" % script, "w", encoding="utf-8") as f:
        f.write(page)
