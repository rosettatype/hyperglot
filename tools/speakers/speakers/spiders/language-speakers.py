__doc__ = """
A scrapy spider for gathering language speaker data from Wikipedia language
pages
"""

__copyright__ = "Copyright (c) 2019, Rosetta Type. All rights reserved."

__author__ = "Johannes Neumeier"

import re
import yaml
import scrapy
import os
import logging
import urllib.parse
import xml.etree.ElementTree as ET


OUTPUT = os.path.join(os.path.dirname(__file__), "../../../../",
                      "data/users.xml")

# Fetch the language names we want to gather speaker info about from this file
INPUT = os.path.join(os.path.dirname(__file__), "../../../../",
                    #  "data/rosetta_new.yaml")
                     "data/iso-639-3.yaml")


class LanguageSpider(scrapy.Spider):
    name = 'speakers'

    # Keep a dict of scraping URLs and their respective language code from
    # our data, to log our language tag to the gathered data
    urls = {}

    # We just paste the language name into the URL and hope for a
    # reasonable from wikipedia
    # The info we are interested in is usually found in a table.infobox on the
    # righthand side of the page. We are searching for tr elements with certain
    # text (label) and then parse that row's data (text)
    base = "https://en.wikipedia.org/wiki/%s_language"

    # Save a dict of iso to URL to later re-associate the crawled data with our
    # data
    with open(INPUT, 'r') as stream:
        try:
            data = yaml.load(stream)
        except yaml.YAMLError as exc:
            print(exc)

        # To crawl all rosetta_new.yaml languages use this code
        # for script, languages in data.items():
        #     for key, lang in languages.items():
        #         # Save the URL encoded
        #         urls[key] = base % urllib.parse.quote_plus(
        #             lang["name"].replace(" ", "_"))

        # To crawl instead all language speaker for e.g. data/iso-639-3.yaml
        # use
        # NOTE This will crawl a longer time, and will result in a bigger xml
        for key, lang in data.items():
            # Save the URL encoded
            urls[key] = base % urllib.parse.quote_plus(
                lang["names"][0].replace(" ", "_"))

    # To run a few languages only for debugging, append e.g. [:5]
    start_urls = [u for u in urls.values()]

    def parse(self, response):
        # 'Native speakers' seems to be a Wikipedia standard label for language
        # pages
        speakers_xpath = "//table[contains(@class, 'infobox')]" \
            + "//tr[contains(.//div, 'Native speakers')]/td//text()"
        speakers_raw = " ".join(response.xpath(speakers_xpath).getall())

        # Clean up raw data some, remove trailing spaces
        speakers = speakers_raw.strip()
        # Remove control chars
        speakers = re.sub(r"[\u0001-\u001F]", "", speakers)
        # Replace all kinds of hyphens with simple hyphen
        speakers = re.sub(r"[\u00AD\u002D\u2010-\u2015]", "-", speakers)

        if re.search("written only", speakers_raw):
            speakers = "written only"
        elif speakers is not None and speakers not in ["", "None", "none"]:
            # Remove anything before and after the first essential number, and
            # save that number with period and commans
            # Also run regex on lowercase to catch various Million/MILLION
            #
            # This should capture the essential number in all of those:
            # 12   million
            # 12 million [1]
            # about 12 million
            # est. 2,100
            # 12  million
            # 12     million
            # 2.5–3 million (with other hyphen)
            # 2.5-3 million (with hyphen)
            # 500+ speakers
            # 25 + speakers
            # 100-250
            # 1.2-2.3
            # 10 million
            # All UK speakers: 700,000+ (2012)[1]
            numbers = re.findall(r"^\D*([0-9,\.\-]*)[\s+]+(million|billion)?",
                                 speakers.lower())
            speakers = "unknown"

            if numbers:
                # findall will return a list, but there ever is only one item
                # which is itself a tuple of the matched groups, where
                # [0][0] is the extracted number, and
                # [0][1] is the million/billion string, if found
                matches = numbers[0]

                # Remove superflous readabiity commas
                # If a range was matches, take the first value only
                number = matches[0].replace(",", "").split("-")[0]

                if number != "":
                    # Parse "b/millions" to actual number:
                    # To float, make m/billions, loose comma
                    if matches[1] == "billion":
                        number = round(float(number) * 10 ** 9)

                    if matches[1] == "million":
                        number = round(float(number) * 10 ** 6)

                    # Plain numbers, no comma-formatting, no fractional humans
                    # please
                    speakers = int(number)

        # While we are at it try to fetch language codes to cross-reference
        iso_639_1 = response.xpath(
            "//table[contains(@class, 'infobox')]"
            + "//tr[contains(.//a, 'ISO 639-1')]/td//a/text()").get()
        iso_639_2 = response.xpath(
            "//table[contains(@class, 'infobox')]"
            + "//tr[contains(.//a, 'ISO 639-2')]/td//a/text()").get()

        # Try match the parsed language back to our original iso 3 letter codes
        try:
            lang = [key for key, url in self.urls.items() if url ==
                    response.request.url][0]
        except Exception as e:
            logging.error(e)
            if iso_639_2 in self.urls.keys():
                lang = iso_639_2
            else:
                lang = "not found"

        yield {
            "lang": lang,
            "speakers": speakers,
            "speakers_raw": speakers_raw,
            "iso_639_1": iso_639_1,
            "iso_639_2": iso_639_2,
            "source": response.request.url
        }

    def closed(self, reason):
        # Since the scraped data flows into the XML file as it is gathered and
        # we are revision-tracking that data, each run will result in changes
        # because of different order. To avoid this, sort the finished XML
        # alphabetically a-z by language iso
        if not os.path.isfile(OUTPUT):
            logging.warning("No output XML file to sort")
            return

        tree = ET.parse(OUTPUT)
        root = tree.getroot()
        items = root.findall("./item")
        langs = [l.text for l in root.findall(".//lang")]

        # A simple alpahbetic sort will do
        langs.sort()

        # Empty the XML tree
        for i in items:
            root.remove(i)

        # Add items in lang order
        for l in langs:
            for i in items:
                item = i.find("./[lang='" + l + "']")
                if item is not None:
                    root.append(item)

        # Save sorted file
        tree.write(OUTPUT, "utf-8", True)
