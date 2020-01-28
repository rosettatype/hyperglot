import re
from tools.languages_meta import get_languages_raw
from lib.fontlang.Languages import Languages

raw = get_languages_raw()
Langs = Languages()


def get_census(raw):
    """
    Helper to attempt to extract a census date from a raw string. Matches
    all of those examples, mostly by matching a 4 digits natural year-like
    number from within parens:

    (2008) [1]
    140 (2016 census)
    (30,000 cited 1973)
    870 (2000–2006) [1]
    1.8 million (2005)
    (1967)
    575,900 (2005–2015)
    ca. 30,000 (2000 census)
    (60,000 cited 1989) [1]
    (1,300 cited 1990 census)
    (1,300 cited 2000 census)
    """
    # The regex includes a bunch of ?: non matching groups, matches years by
    # 19\d{2}|20\d{2}, with some optional matches before and after the year
    # inside the parens, with the optional span to year-ranges like 2005-2015
    census = re.compile(
        r"(?<=(?:\(|\s))(?:(19\d{2}|20\d{2}(?:(?:\–|\-)(?:19\d{2}|20\d{2}))?)(?: census)?)\)")
    matches = census.findall(raw)
    if matches:
        return matches
    return False


for iso, lang in Langs.items():
    if "speakers" in lang and "speakers_date" not in lang:
        if iso in raw.keys():
            census = get_census(raw[iso])
            if census:
                print(iso, "\t", census, "\t", raw[iso])
        else:
            print(iso, "\t no raw data", lang["name"])
