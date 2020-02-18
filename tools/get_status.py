"""
Compare and output 'status' suggestions for Rosetta.yaml entries based on 
iso 639 data
"""
import yaml
from lib.fontlang.languages import Languages
from lib.fontlang.main import save_sorted

Langs = Languages(inherit=False)

STATUSES = {
    "E": "extinct",
    "C": "constructed",
    "H": "historical",
    "S": "special",
    "A": "ancient",
    "L": "living"
}

with open("data/iso-639-3.yaml") as f:
    data = yaml.load(f, Loader=yaml.Loader)
    for iso, info in data.items():
        if iso in Langs:
            lang = Langs[iso]
            if "status" not in lang:
                print(iso, "set missing status", STATUSES[info["type"]])
                lang["status"] = "living"
            else:
                if lang["status"] != STATUSES[info["type"]]:
                    print(iso, lang["status"], "in our data, vs iso:",
                          STATUSES[info["type"]])

    # save_sorted(Langs)
