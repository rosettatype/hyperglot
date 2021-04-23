"""
Simple parser to fetch the languagesystem's table from the OT spec and save
them as a yaml dict of ISO-to-languagesystem in tools/languagesystems.yaml.

Sorted by ISO. Languagesystems which relate to several ISO codes have been
expanded and added for each ISO. 

Languagesystems that do not have an ISO code are dropped

Call from repo root directory. Make sure you install bs4 and yaml.

Note: May need updating as the HTML changes.
"""
import os
import re
import yaml
import urllib.request
from bs4 import BeautifulSoup

content = urllib.request.urlopen("https://docs.microsoft.com/en-us/typography/opentype/spec/languagetags").read()
soup = BeautifulSoup(content, "html.parser")

data = {}
# soup.table will match as the _only_ table, then loop over its rows
for row in soup.table.find_all("tr"):
    cols = row.find_all("td")
    if len(cols) == 3:
        lang = re.search(r"[A-Z0-9]{2,4}", cols[1].text).group(0)
        for iso in [i.strip() for i in cols[2].text.split(",")]:
            if not iso:
                print("Dropping languagesystem %s which does not have a corresponding ISO code" % cols[1].text)
                continue
            data[iso] = lang

with open(os.path.abspath("other/languagesystems.yaml"), "w") as f:
    yaml.dump(data, f)
