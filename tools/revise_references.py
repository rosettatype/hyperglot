"""
Get Wikipedia, Ethnologue, and Language Archive references for languages.
"""

from datetime import datetime
import glob
import logging
import os
import requests
import wikipedia
import yaml

alvestrand = {
    "reference": "Alvestrand, Harald. (1995) *Characters and character sets for various languages.* Retrieved on September 6, 2021 from https://www.alvestrand.no/ietf/lang-chars.txt"
}
ethnologue = {
    "reference": "{name}. ({date}). In *Ethnologue*. SIL International. {url}",
    "url": "https://www.ethnologue.com/language/{}/"
}
omniglot = {
    "reference": "Ager, Simon. ({date}) {name} language, alphabet, and pronunciation. *Omniglot*. {url}",
    "url": "https://www.omniglot.com/writing/{}.htm"
}
wiki = {
    "reference": "{name} language. ({date}). In *Wikipedia*. {url}",
}

# TODO: CLDR 

today = datetime.today().strftime("%Y, %B %-d")
paths = sorted(glob.glob("../lib/hyperglot/data/*.yaml"))
total = 0
for path in paths:
     code = os.path.basename(path).replace(".yaml", "").replace("_", "").lower()
     if code == "dflt":
         continue
     with open(path, "rb") as f:
        data = yaml.load(f, Loader=yaml.Loader)
        if not data:
            print("There was an issue opening: {}.yaml".format(code))
            continue
        if "sources" not in data:
            continue
        name = data["name"]
        sources = []
        changed = False
        print("-", name)
        for source in data["sources"]:
            # Alvestrand (add only when "Alvestrand" is present)
            if source == "Alvestrand":
                sources.append(alvestrand["reference"])
            # Ethnologue (add only when "Ethnologue" is present, no URL check)
            elif source == "Ethnologue":
                ethnologue_url = ethnologue["url"].format(code)
                sources.append(ethnologue["reference"].format(name=name, date=today, url=ethnologue_url))
                changed = True
            # Omniglot (add only when "Omniglot" is present and URL exists)
            elif source == "Omniglot":
                sources.append("Omniglot")
            #     omniglot_url = omniglot["url"].format(name.lower())
            #     response = requests.get(omniglot_url)
            #     if response.status_code == 200:
            #         sources.append(omniglot["reference"].format(name=name, date=today, url=omniglot_url))
            #     changed = True
            #     else:
            #         # print("'%s' does not exist" % omniglot_url)
            #         sources.append("Omniglot  # REVIEW")
            # Wikipedia (always add, remove "Wikipedia")
            elif source == "Wikipedia":
                # use permanent link as an url
                try:
                    res = wikipedia.page("{} language".format(name))
                    wiki_url = res.url + "?oldid=" + str(res.revision_id)
                    sources.append(wiki["reference"].format(name=name, date=today, url=wiki_url))
                    changed = True
                except Exception as exp:
                    sources.append("Wikipedia  # REVIEW")
                    # print(exp)
            else:
                sources.append(source + "  # REVIEW")
            data["sources"] = sources
            if changed:
                total += 1
     with open(path, "w", encoding="utf-8") as f:
        try:
            yaml.safe_dump(data, f, allow_unicode=True,
                           default_flow_style=False)
        except yaml.YAMLError as exc:
            logging.warning(exc)
     del data
print("Total languages affected:", total)

