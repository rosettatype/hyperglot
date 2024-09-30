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
from bs4 import BeautifulSoup

omniglot = {
    "reference": "Ager, Simon. ({date}) {name} language, alphabet, and pronunciation. *Omniglot*. {url}",
    "url": "https://www.omniglot.com/writing/{}.htm"
}
wiki = {
    "reference": "{name}. ({date}). In *Wikipedia*. {url}",
}

# TODO: CLDR, REVIEW, Evertype, Omniglot, ominglot, Unicode specification

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
            # Omniglot (add only when "Omniglot" is present and URL exists)
            # if source == "Omniglot":
            #     sources.append("Omniglot")
            #     omniglot_url = omniglot["url"].format(name.lower())
            #     response = requests.get(omniglot_url)
            #     if response.status_code == 200:
            #         sources.append(omniglot["reference"].format(name=name, date=today, url=omniglot_url))
            #     changed = True
            #     else:
            #         # print("'%s' does not exist" % omniglot_url)
            #         sources.append("Omniglot  # REVIEW")
            # Wikipedia (always add, remove "Wikipedia")
            if "wikipedia" in source:
                # Arbëreshë Albanian language. (2024, August 28). In *Wikipedia*. https://en.wikipedia.org/wiki/Arb%C3%ABresh_language?oldid=1239219170
                url = source.split(". ")[-1].strip()
                try:
                    #res = wikipedia.page(title)
                    r = requests.get(url)
                    #wiki_url = res.url + "?oldid=" + str(res.revision_id)
                except Exception as exp:
                    # sources.append("Wikipedia  # REVIEW")
                    print("ERROR at", url)
                parsed_html = BeautifulSoup(r.text, "html.parser")
                name = parsed_html.find(id="firstHeading").text
                date = parsed_html.find(id="mw-revision-date").text.split(", ")[-1].split(" ")  # 8 August 2024
                date = "%s, %s %s" % (date[2], date[1], date[0])
                reference = wiki["reference"].format(name=name, date=date, url=url)
                if reference != source:
                    sources.append(wiki["reference"].format(name=name, date=date, url=url))
                    changed = True
            else:
                sources.append(source)
        if changed:
            total += 1
        data["sources"] = sources
    with open(path, "w", encoding="utf-8") as f:
        try:
            yaml.safe_dump(data, f, allow_unicode=True,
                            default_flow_style=False)
        except yaml.YAMLError as exc:
            logging.warning(exc)
    del data
print("Total languages affected:", total)

