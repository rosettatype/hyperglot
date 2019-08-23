"""
Make test website
"""

from copy import copy
import os
import sys
from collections import OrderedDict
sys.path.insert(0, "..")
from custom_yaml import load_yaml


def comparison(r, s):
    o = ""
    for c in s.split(" "):
        if c in r:
            o += "<em>%s</em> " % c
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
for script in ["Latn", "Cyrl", "Grek"]:
    html = ""
    html += "---\n"
    html += "layout: default\n"
    html += "permalink: /\n"
    html += "---\n\n"
    html += "# %s-script languages\n\n" % script
    html += "Selected character-set databases (CLDR, Latin Plus) "
    html += "juxtaposed next to Rosetta’s Langs DB. When comparing, "
    html += "characters that are included in “Rosetta (base)” "
    html += "are marked grey, any additional characters are marked red. "
    html += "Only “base” fields are compared. "
    html += "The third column indicates whether the field is “todo” (grey) "
    html += "or “done” (green). In case of CLDR, grey refers to draft "
    html += "having been “contributed”.\n\n"

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
                            tab += "<td class='%s'></td></tr>\n" % db[dbk][script][iso]["status"]
                        elif dbk == "cldr":
                            drafts = db[dbk][script][iso]["draft"].split(",")
                            if i < len(drafts):
                                tab += "<td class='%s'></td></tr>\n" % drafts[i]
                            else:
                                tab += "<td class='unknown'></td></tr>\n"
                        else:
                            tab += "<td class='done'></td></tr>\n"
        if all_chars.strip():
            html += "## %s (%s)\n\n" % (iso_639_3[iso]["names"][0], iso)
            html += "<table>\n %s </table>\n\n" % tab

    # save to MD file
    with open("test_%s.md" % script, "w", encoding="utf-8") as f:
        f.write(html)
